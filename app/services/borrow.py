import logging

from app.db.database import sql
from fastapi import HTTPException, status
from datetime import datetime
from app.schemas.borrow import BorrowRequest, ReturnRequest, BorrowHistoryParams
from app.db.models import BookStatus
from app.websockets.manager import notify_user


logger = logging.getLogger(__name__)


def borrow_book(borrow_data: BorrowRequest, current_user):

    user_id = current_user["id"]

    # Check if book item exists and is available
    book = sql("""
            SELECT *
            FROM books
            WHERE id = :book_id
        """,
               book_id=borrow_data.book_id
               ).dict()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    if not book['available_quantity']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Out of stock"
        )

    # Check if due date is valid (not in the past)
    if borrow_data.due_date.replace(tzinfo=None) < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be in the past"
        )

    book_item_id = sql(
        '''
        SELECT id
        FROM book_items
        WHERE book_id = :book_id AND status = :available_status
        LIMIT 1
        ''',
        book_id=book['id'],
        available_status=BookStatus.AVAILABLE.value,
    ).scalar()

    # Create borrow record
    sql("""
            INSERT INTO borrow_records
            (user_id, book_item_id, borrowed_date, due_date, status)
            VALUES
            (:user_id, :book_item_id, NOW(), :due_date, 'active')
        """,
        user_id=user_id,
        book_item_id=book_item_id,
        due_date=borrow_data.due_date
        )

    borrow_id = sql("""
                    SELECT id FROM borrow_records
                    WHERE user_id = :user_id AND book_item_id = :book_item_id
                    """,
                    user_id=user_id,
                    book_item_id=book_item_id
                    ).scalar()

    sql("""
            UPDATE book_items 
            SET status = 'borrowed'
            WHERE id = :book_item_id
        """,
        book_item_id=book_item_id
        )

    available_quantity = book['available_quantity'] - 1
    sql("""
            UPDATE books
            SET available_quantity = :available_quantity
            WHERE id = :book_id
        """,
        book_id=book['id'],
        available_quantity=available_quantity,
        )

    return get_borrow_record_by_id(borrow_id)


def return_book(current_user, return_data: ReturnRequest):

    user_id = current_user["id"]

    # Get the borrow record
    borrow_record = sql("""
            SELECT br.*, bi.book_id
            FROM borrow_records br
            JOIN book_items bi ON br.book_item_id = bi.id
            WHERE br.id = :borrow_id
        """,
                        borrow_id=return_data.borrow_id
                        ).dict()

    if not borrow_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borrow record not found"
        )

    # Check if this is the user's borrow record or if user is a librarian
    if borrow_record['user_id'] != user_id and current_user["role_id"] not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only return your own borrowed books"
        )

    # Check if already returned
    if borrow_record['returned_date']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book has already been returned"
        )

    # Update borrow record
    sql("""
            UPDATE borrow_records 
            SET returned_date = NOW(), status = 'returned'
            WHERE id = :borrow_id
        """,
        borrow_id=return_data.borrow_id
        )

    # Update book item status
    sql("""
            UPDATE book_items 
            SET status = 'available', updated_at = NOW()
            WHERE id = :book_item_id
        """,
        book_item_id=borrow_record['book_item_id']
        )

    # Update book available quantity
    sql("""
            UPDATE books
            SET available_quantity = available_quantity + 1, updated_at = NOW()
            WHERE id = :book_id
        """,
        book_id=borrow_record['book_id']
        )

    # Check if there are users in the notification queue for this book
    users_waiting = sql("""
            SELECT nq.user_id, b.title
            FROM notification_queue nq
            LEFT JOIN books b ON nq.book_id = b.id
            WHERE nq.book_id = :book_id
        """,
                        book_id=borrow_record['book_id']
                        ).dicts()

    sql("DELETE FROM notification_queue WHERE book_id = :book_id",
        book_id=borrow_record['book_id'])

    # Notify users that the book is available
    for user in users_waiting:
        notify_user(
            user_id=user["user_id"],
            message={
                "type": "book_available",
                "message": f"The book '{user["title"]}' is now available.",
                "book_id": borrow_record['book_id']
            }
        )

    return get_borrow_record_by_id(return_data.borrow_id)


def get_borrow_history(current_user, params: BorrowHistoryParams):

    query = """
        SELECT br.id
        FROM borrow_records br
        JOIN book_items bi ON br.book_item_id = bi.id
        JOIN books b ON bi.book_id = b.id
        WHERE 1=1
    """
    query_params = {}

    if params.user_id:
        if params.user_id != current_user["id"] and current_user["role_id"] not in [1, 2]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own borrowing history"
            )
        query += " AND br.user_id = :user_id"
        query_params["user_id"] = params.user_id
    elif current_user["role_id"] not in [1, 2]:
        query += " AND br.user_id = :user_id"
        query_params["user_id"] = current_user["id"]

    if params.status:
        query += " AND br.status = :status"
        query_params["status"] = params.status

    if params.is_overdue is not None:
        if params.is_overdue:
            query += " AND br.returned_date IS NULL AND br.due_date < NOW()"
        else:
            query += " AND (br.returned_date IS NOT NULL OR br.due_date >= NOW())"

    total_borrow_history = sql(query, **query_params).dicts()

    query += " ORDER BY br.borrowed_date DESC LIMIT :limit OFFSET :offset"
    offset = params.page * params.limit
    query_params["limit"] = params.limit
    query_params["offset"] = offset

    borrow_ids = sql(query, **query_params).scalars()

    history = [get_borrow_record_by_id(id) for id in borrow_ids]

    number_of_pages = (len(total_borrow_history) // params.limit) + \
        (1 if len(total_borrow_history) % params.limit != 0 else 0)

    return {
        "borrows": history,
        "page": params.page,
        "size": params.limit,
        "total": len(total_borrow_history),
        "number_of_pages": number_of_pages
    }


def notify_when_available(book_id, current_user):
    user_id = current_user["id"]

    # Check if book exists
    book = sql("SELECT id, title, available_quantity FROM books WHERE id = :book_id",
               book_id=book_id
               ).dict()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )

    # If the book is already available, inform the user
    if book['available_quantity'] > 0:
        return {"message": f"The book '{book['title']}' is already available. No notification needed."}

    # Check if user is already in the notification queue for this book
    existing = sql("""
            SELECT user_id FROM notification_queue
            WHERE user_id = :user_id AND book_id = :book_id
        """,
                   user_id=user_id, book_id=book_id
                   ).scalar()

    if existing:
        return {"message": f"You are already in the notification queue for the book '{book['title']}'."}

    # Add user to notification queue
    sql("""
            INSERT INTO notification_queue (user_id, book_id, channel_id)
            VALUES (:user_id, :book_id, :channel_id)
        """,
        user_id=user_id,
        book_id=book_id,
        channel_id=current_user["websocket_connection_id"]
        )

    return {"message": f"You will be notified when the book '{book['title']}' becomes available."}


def get_borrow_record_by_id(borrow_id: int):

    borrow_record = sql("""
            SELECT 
                br.*,
                u.email as user_email,
                u.first_name as user_first_name,
                u.last_name as user_last_name,
                bi.isbn,
                b.id as book_id,
                b.title,
                b.author
            FROM borrow_records br
            LEFT JOIN users u ON br.user_id = u.id
            LEFT JOIN book_items bi ON br.book_item_id = bi.id
            LEFT JOIN books b ON bi.book_id = b.id
            WHERE br.id = :borrow_id
        """,
                        borrow_id=borrow_id
                        ).dict()

    if not borrow_record:
        return None

    # Calculate is_overdue, days_remaining, days_overdue
    now = datetime.utcnow()
    is_overdue = not borrow_record['returned_date'] and borrow_record['due_date'] < now

    if borrow_record['returned_date']:
        days_remaining = 0
        borrowing_duration = (borrow_record['returned_date'] -
                              borrow_record['borrowed_date']).days
    else:
        days_remaining = (borrow_record['due_date'] -
                          now).days if borrow_record['due_date'] > now else 0
        borrowing_duration = (now - borrow_record['borrowed_date']).days

    days_overdue = (now - borrow_record['due_date']).days if is_overdue else 0

    return {
        "id": borrow_record['id'],
        "user_id": borrow_record['user_id'],
        "book_item_id": borrow_record['book_item_id'],
        "borrowed_date": borrow_record['borrowed_date'],
        "due_date": borrow_record['due_date'],
        "returned_date": borrow_record['returned_date'],
        "status": borrow_record['status'],
        "is_overdue": is_overdue,
        "days_remaining": days_remaining,
        "days_overdue": days_overdue,
        "borrowing_duration": borrowing_duration,
        "book_details": {
            "book_id": borrow_record['book_id'],
            "isbn": borrow_record['isbn'],
            "title": borrow_record['title'],
            "author": borrow_record['author']
        },
        "user_details": {
            "email": borrow_record['user_email'],
            "name": f"{borrow_record['user_first_name']} {borrow_record['user_last_name']}"
        }
    }
