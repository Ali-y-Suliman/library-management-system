from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, Index, Enum
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.schema import UniqueConstraint
import sqlalchemy as sa
from app.db.database import Base
import enum


class BookStatus(enum.Enum):
    AVAILABLE = "available"
    BORROWED = "borrowed"


class BorrowedBookStatus(enum.Enum):
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"


class Role(Base):
    """
    Role model for user permissions.
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)


class User(Base):
    """
    User model representing both regular users and librarians.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role_id = Column(Integer, index=True, nullable=False)
    api_key = Column(String(255), nullable=True)
    api_key_hash = Column(String(255), nullable=True, index=True)
    api_key_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    websocket_connection_id = Column(String(255), nullable=True)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)


class Category(Base):
    """
    Book category model.
    """
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)


class Book(Base):
    """
    Book model with detailed information.
    """
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    author = Column(String(50), nullable=False)
    publisher = Column(String(50), nullable=True)
    publication_year = Column(Integer, nullable=True, index=True)
    description = Column(TEXT, nullable=True)
    total_quantity = Column(Integer, nullable=False)
    available_quantity = Column(Integer, nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    # Indexes / Constraints
    __table_args__ = (
        UniqueConstraint('title', 'author', name='unq_title_author'),
        Index('idx_book_publication_year', 'publication_year')
    )


class BookItem(Base):
    """
    Physical copy of a book that can be borrowed.
    """
    __tablename__ = "book_items"

    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, nullable=False)
    isbn = Column(String(50), unique=True, nullable=False)
    location = Column(String(50), nullable=True)
    status = Column(Enum(BookStatus),
                    default=BookStatus.AVAILABLE, nullable=False)
    acquisition_date = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    __table_args__ = (
        Index('idx_book_item_book_id', 'book_id'),
        Index('idx_book_item_status', 'status'),
    )


class BorrowRecord(Base):
    """
    Records of book borrowing history.
    """
    __tablename__ = "borrow_records"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    book_item_id = Column(Integer, nullable=False)
    borrowed_date = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    due_date = Column(DateTime, nullable=False)
    returned_date = Column(DateTime, nullable=True)
    # active, returned, overdue
    status = Column(Enum(BorrowedBookStatus),
                    default=BorrowedBookStatus.ACTIVE, nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    __table_args__ = (
        Index('idx_borrow_user', 'user_id'),
        Index('idx_borrow_book', 'book_item_id'),
        Index('idx_borrow_status', 'status'),
    )


class BookCategory(Base):
    __tablename__ = "book_category"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    book_id = Column(Integer, nullable=False)
    category_id = Column(Integer, nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    __table_args__ = (
        UniqueConstraint('book_id', 'category_id', name='uq_book_category'),
    )


class NotificationQueue(Base):
    __tablename__ = "notification_queue"

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    book_id = Column(Integer, nullable=False)
    channel_id = Column(String(255), nullable=False)

    created_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP'), nullable=False)
    updated_at = Column(sa.TIMESTAMP, server_default=sa.text(
        'CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'book_id', name='uq_user_book'),
    )
