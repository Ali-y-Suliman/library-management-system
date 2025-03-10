import logging
from datetime import datetime
from app.core.security import get_password_hash
from app.db.database import sql

logger = logging.getLogger(__name__)


def seed_roles() -> None:
    """Seed default roles."""
    try:
        roles = [
            {"id": 1, "name": "admin"},
            {"id": 2, "name": "librarian"},
            {"id": 3, "name": "user"}
        ]

        for role in roles:
            sql('''
                INSERT INTO roles (id, name) VALUES (:id, :name)
                ''',
                **role
                )
    except Exception as e:
        logger.error(f'error seeding roles {e}')
    logger.info("Roles seeded successfully")


def seed_admin_user() -> None:
    """Seed default admin user."""
    admin_data = {
        "email": "admin@library.com",
        "first_name": "Admin",
        "last_name": "User",
        "hashed_password": get_password_hash("admin123"),
        "role_id": 1,
        "is_active": True,
    }

    # Check if admin user exists
    admin_exists = sql('''
        SELECT id FROM users WHERE email = :email
        ''',
                       email=admin_data["email"]
                       ).dict()

    if not admin_exists:
        sql("""
                INSERT INTO users 
                (email, first_name, last_name, hashed_password, role_id, is_active)
                VALUES 
                (:email, :first_name, :last_name, :hashed_password, :role_id, :is_active)
            """,
            **admin_data
            )

        logger.info("Admin user seeded successfully")


def seed_librarian_user() -> None:
    """Seed default librarian user."""
    librarian_data = {
        "email": "librarian@library.com",
        "first_name": "Librarian",
        "last_name": "User",
        "hashed_password": get_password_hash("librarian123"),
        "role_id": 2,
        "is_active": True
    }

    # Check if librarian user exists
    librarian_exists = sql('''
        SELECT id FROM users WHERE email = :email
        ''',
                           email=librarian_data["email"]
                           ).dict()

    if not librarian_exists:
        sql("""
                INSERT INTO users 
                (email, first_name, last_name, hashed_password, role_id, is_active)
                VALUES 
                (:email, :first_name, :last_name, :hashed_password, :role_id, :is_active)
            """,
            **librarian_data
            )

        logger.info("Librarian user seeded successfully")


def seed_sample_categories() -> None:
    """Seed sample book categories."""
    categories = [
        {"name": "Fiction"},
        {"name": "Non-Fiction"},
        {"name": "Science"},
        {"name": "Technology"},
        {"name": "History"}
    ]

    for category in categories:
        # Check if category exists
        cat_exists = sql("SELECT id FROM categories WHERE name = :name",
                         name=category["name"]
                         ).scalar()

        if not cat_exists:
            sql("""
                    INSERT INTO categories 
                    (name)
                    VALUES 
                    (:name)
                """,
                **category
                )

    logger.info("Sample categories seeded successfully")


def seed_sample_books() -> None:
    """Seed sample books."""
    books = [
        {
            "title": "Introduction to Library Science",
            "author": "John Doe",
            "publisher": "Academic Press",
            "publication_year": 2022,
            "description": "A comprehensive guide to library science and management.",
            "total_quantity": 5,
            "available_quantity": 1,
        },
        {
            "title": "Database Systems",
            "author": "Jane Smith",
            "publisher": "Tech Publications",
            "publication_year": 2021,
            "description": "An in-depth look at modern database systems and their applications.",
            "total_quantity": 3,
            "available_quantity": 3,
        }
    ]

    for book in books:

        book_exists = sql("SELECT id FROM books WHERE title = :title AND author = :author",
                          title=book["title"], author=book["author"]
                          ).scalar()

        if not book_exists:

            result = sql("""
                    INSERT INTO books 
                    (title, author, publisher, publication_year, description, 
                    total_quantity, available_quantity)
                    VALUES 
                    (:title, :author, :publisher, :publication_year, :description, 
                    :total_quantity, :available_quantity)
                """,
                         **book
                         )

            # Get the inserted book ID
            book_id = sql("SELECT id FROM books WHERE title = :title AND author = :author",
                          title=book["title"], author=book["author"]
                          ).scalar()

            # Add book items
            isbn_base = book['title']
            for i in range(book["total_quantity"]):
                isbn = f"{isbn_base}-{i+1}"
                sql("""
                        INSERT INTO book_items 
                        (book_id, isbn, status)
                        VALUES 
                        (:book_id, :isbn, 'available')
                    """,
                    book_id=book_id,
                    isbn=isbn,
                    )

            # Assign categories
            if book["title"] == "Introduction to Library Science":
                category_ids = sql(
                    "SELECT id FROM categories WHERE name IN ('Non-Fiction', 'Education')"
                ).scalars()

                for cat_id in category_ids:
                    sql("""
                            INSERT INTO book_category 
                            (book_id, category_id)
                            VALUES 
                            (:book_id, :category_id)
                        """,
                        book_id=book_id, category_id=cat_id
                        )

            elif book["title"] == "Database Systems":
                category_ids = sql(
                    "SELECT id FROM categories WHERE name IN ('Technology', 'Science')"
                ).scalars()

                for cat_id in category_ids:
                    sql("""
                            INSERT INTO book_category 
                            (book_id, category_id)
                            VALUES 
                            (:book_id, :category_id)
                        """,
                        book_id=book_id, category_id=cat_id
                        )

    logger.info("Sample books seeded successfully")


def seed_data() -> None:
    """Main function to seed all initial data."""
    try:
        seed_roles()
        seed_admin_user()
        seed_librarian_user()
        seed_sample_categories()
        seed_sample_books()

        logger.info("All seed data created successfully")
    except Exception as e:
        logger.error(f"Error seeding data: {e}")
        raise
