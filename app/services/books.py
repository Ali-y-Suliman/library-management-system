import logging

from app.db.database import sql
from fastapi import HTTPException, status
from app.schemas.book import CategoryCreate, Category, BookCreate, BookSearchParams, BookUpdate, BookItemCreate
from app.utils.cache import get_cached, set_cached, delete_cached, clear_cache_pattern


logger = logging.getLogger(__name__)


def create_category(category: CategoryCreate):

    existing = sql("SELECT id FROM categories WHERE name = :name",
                   name=category.name
                   ).scalar()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )

    sql("""
            INSERT INTO categories (name)
            VALUES (:name)
        """,
        name=category.name
        )

    category_data = sql("SELECT * FROM categories WHERE name = :name",
                        name=category.name
                        ).dict()

    return {
        "id": category_data['id'],
        "name": category_data['name'],
        "book_count": 0,
        "created_at": category_data['created_at'],
        "updated_at": category_data['updated_at']
    }


def get_categories(page: int, limit: int):

    skip = page * limit

    categories = sql("""
            SELECT c.id, c.name, c.created_at, c.updated_at,
                   COUNT(bc.book_id) as book_count
            FROM categories c
            LEFT JOIN book_category bc ON c.id = bc.category_id
            GROUP BY c.id
            ORDER BY c.name
            LIMIT :limit OFFSET :skip
        """,
                     skip=skip, limit=limit
                     ).dicts()

    total = sql(""" SELECT COUNT(*) FROM categories """).scalar()

    number_of_pages = (len(total) // limit) + \
        (1 if len(total) % limit != 0 else 0)

    categories: list[Category] = [
        {
            "id": cat['id'],
            "name": cat['name'],
            "book_count": cat['book_count'],
            "created_at": cat['created_at'],
            "updated_at": cat['updated_at']
        }
        for cat in categories
    ]
    return {
        "categories": categories,
        "page": page,
        "size": limit,
        "total": total,
        "number_of_pages": number_of_pages
    }


def search_books(params: BookSearchParams):

    query = """
        SELECT DISTINCT b.* FROM books b
        JOIN book_category bc ON b.id = bc.book_id
        WHERE 1=1
    """
    conditions = []
    query_params = {}

    if params.title:
        conditions.append("b.title LIKE :title")
        query_params["title"] = f"%{params.title}%"

    if params.author:
        conditions.append("b.author LIKE :author")
        query_params["author"] = f"%{params.author}%"

    if params.publication_year:
        conditions.append("b.publication_year = :publication_year")
        query_params["publication_year"] = params.publication_year

    if params.category_id:
        conditions.append("bc.category_id = :category_id")
        query_params["category_id"] = params.category_id

    if params.available_only:
        conditions.append("b.available_quantity > 0")

    if conditions:
        query += " AND " + " AND ".join(conditions)

    total_books = sql(query, **query_params).dicts()

    offset = params.page * params.limit
    query += " ORDER BY b.title LIMIT :limit OFFSET :offset"
    query_params["limit"] = params.limit
    query_params["offset"] = offset

    books = sql(query, **query_params).dicts()

    number_of_pages = (len(total_books) // params.limit) + \
        (1 if len(total_books) % params.limit != 0 else 0)

    for book in books:
        book['categories'] = get_book_categories(book['id'])

    return {
        "books": books,
        "page": params.page,
        "size": params.limit,
        "total": len(total_books),
        "number_of_pages": number_of_pages
    }


def get_book_categories(book_id):
    return sql('''
        SELECT c.id, c.name
        FROM book_category bc
        LEFT JOIN categories c ON c.id = bc.category_id
        WHERE bc.book_id = :book_id
    ''',
               book_id=book_id).dicts()


def create_book(book: BookCreate):

    existing = sql("SELECT id FROM books WHERE title = :title AND author = :author",
                   title=book.title, author=book.author
                   ).scalar()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Book with ISBN '{book}' already exists"
        )

    # Create new book
    sql("""
            INSERT INTO books 
            (title, author, publisher, publication_year, description, 
             total_quantity, available_quantity, created_at, updated_at)
            VALUES 
            (:title, :author, :publisher, :publication_year, :description, 
             :total_quantity, :available_quantity, NOW(), NOW())
        """,
        title=book.title,
        author=book.author,
        publisher=book.publisher,
        publication_year=book.publication_year,
        description=book.description,
        total_quantity=0,
        available_quantity=0,
        )

    book_id = sql("SELECT id FROM books WHERE title = :title AND author = :author",
                  title=book.title, author=book.author
                  ).scalar()

    for category_id in book.category_ids:

        category = sql("SELECT id FROM categories WHERE id = :category_id",
                       category_id=category_id
                       ).scalar()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {category_id} does not exist"
            )

        sql("""
                INSERT INTO book_category (book_id, category_id)
                VALUES (:book_id, :category_id)
            """,
            book_id=book_id, category_id=category_id
            )
    book_copy = BookItemCreate(
        book_id=book_id, isbn=book.isbn, location=book.location)
    add_book_copy(book_copy)

    return get_book_by_id(book_id)


def add_book_copy(book_copy: BookItemCreate):
    book = sql("""
            SELECT *
            FROM books
            WHERE id = :book_id
        """,
               book_id=book_copy.book_id
               ).dict()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )

    sql("""
        INSERT INTO book_items (book_id, isbn, location)
                VALUES (:book_id, :isbn, :location)
        """,
        book_id=book_copy.book_id, isbn=book_copy.isbn, location=book_copy.location)

    sql("""
        UPDATE books SET total_quantity = total_quantity + 1, available_quantity = available_quantity + 1
        WHERE id = :book_id
    """,
        book_id=book_copy.book_id)

    return get_book(book_copy.book_id)


def get_book(book_id: int):

    # Try to get from cache
    cache_key = f"book:{book_id}"
    cached_book = get_cached(cache_key)
    if cached_book:
        return cached_book

    book_data = get_book_by_id(book_id)
    if not book_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )

    # Cache the result
    set_cached(cache_key, book_data)

    return book_data


def update_book(book_id: int, book_update: BookUpdate):

    # Check if book exists
    existing = sql("SELECT * FROM books WHERE id = :book_id",
                   book_id=book_id
                   ).dict()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )

    # Build update query dynamically based on provided fields
    update_fields = []
    update_values = {"book_id": book_id}

    if book_update.title is not None:
        update_fields.append("title = :title")
        update_values["title"] = book_update.title

    if book_update.author is not None:
        update_fields.append("author = :author")
        update_values["author"] = book_update.author

    if book_update.publisher is not None:
        update_fields.append("publisher = :publisher")
        update_values["publisher"] = book_update.publisher

    if book_update.publication_year is not None:
        update_fields.append("publication_year = :publication_year")
        update_values["publication_year"] = book_update.publication_year

    if book_update.description is not None:
        update_fields.append("description = :description")
        update_values["description"] = book_update.description

    if book_update.total_quantity is not None:
        update_fields.append("total_quantity = :total_quantity")
        update_values["total_quantity"] = book_update.total_quantity

    if book_update.available_quantity is not None:
        update_fields.append("available_quantity = :available_quantity")
        update_values["available_quantity"] = book_update.available_quantity

    if update_fields:
        update_fields.append("updated_at = NOW()")
        update_query = f"UPDATE books SET {', '.join(update_fields)} WHERE id = :book_id"
        sql(update_query, **update_values)

    # Update categories if provided
    if book_update.category_ids is not None:
        sql("DELETE FROM book_category WHERE book_id = :book_id",
            book_id=book_id
            )

        for category_id in book_update.category_ids:
            sql("""
                    INSERT INTO book_category (book_id, category_id)
                    VALUES (:book_id, :category_id)
                """,
                book_id=book_id, category_id=category_id
                )

    delete_cached(f"book:{book_id}")
    clear_cache_pattern("books:*")

    return get_book_by_id(book_id)


def get_book_by_id(book_id: int):

    book = sql("""
                SELECT *
                FROM books
                WHERE id = :book_id
               """,
               book_id=book_id
               ).dict()

    if not book:
        return None

    book["categories"] = get_book_categories(book["id"])

    return book


def delete_book(book_id: int):

    existing = sql("SELECT id FROM books WHERE id = :book_id",
                   book_id=book_id
                   ).scalar()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Book with ID {book_id} not found"
        )

    # Check if any book items are currently borrowed
    borrowed = sql("""
            SELECT COUNT(*) FROM book_items bi
            JOIN borrow_records br ON bi.id = br.book_item_id
            WHERE bi.book_id = :book_id AND br.returned_date IS NULL
        """,
                   book_id=book_id
                   ).scalar()

    if borrowed > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete book while copies are still borrowed"
        )

    sql("DELETE FROM books WHERE id = :book_id",
        book_id=book_id
        )

    delete_cached(f"book:{book_id}")
    clear_cache_pattern("books:*")

    return {"message": f"Book with ID {book_id} deleted successfully"}
