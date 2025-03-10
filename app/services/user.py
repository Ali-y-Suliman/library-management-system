import logging

from app.db.database import sql
from fastapi import HTTPException, status
from datetime import datetime
from app.core.security import get_password_hash


logger = logging.getLogger(__name__)


class NotFoundException(Exception):
    pass


def get_users(page: int, limit: int):

    skip = page * limit

    users = sql("""
        SELECT id, email, first_name, last_name FROM users
            LIMIT :limit OFFSET :skip
        """,
                skip=skip, limit=limit
                ).dicts()

    if not users:
        return []

    total = sql(""" SELECT COUNT(*) FROM users """).scalar()

    number_of_pages = total % limit

    number_of_pages = (total // limit) + \
        (1 if total % limit != 0 else 0)

    return {
        "users": users,
        "page": page,
        "size": len(limit),
        "total": total,
        "number_of_pages": number_of_pages
    }


def get_user_by_id(email: str):
    user = sql('''
        SELECT * FROM users
        WHERE email = :email
        ''', email=email,).dict()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


def get_roles(id):

    roles = sql("SELECT * FROM roles").dicts()

    return [
        {
            "id": role.id,
            "name": role.name
        }
        for role in roles
    ]


def get_user(user_id, current_user):
    logger.error('------------------')
    logger.error(current_user["id"])
    logger.error('------------------')
    if user_id != current_user["id"] and current_user["role_id"] != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user"
        )

    # Get user data
    user = sql("""
            SELECT u.*, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = :user_id
        """,
               user_id=user_id
               ).dict()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # Get active borrow count
    active_borrows = sql("""
            SELECT COUNT(*) FROM borrow_records
            WHERE user_id = :user_id AND returned_date IS NULL
        """,
                         user_id=user_id
                         ).scalar()

    # Get overdue borrow count
    overdue_borrows = sql("""
            SELECT COUNT(*) FROM borrow_records
            WHERE user_id = :user_id AND returned_date IS NULL AND due_date < NOW()
        """,
                          user_id=user_id
                          ).scalar()

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role_id": user.role_id,
        "role_name": user.role_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "active_borrow_count": active_borrows,
        "overdue_borrow_count": overdue_borrows,
        "has_api_key": bool(user.api_key and user.api_key_expires_at and user.api_key_expires_at > datetime.utcnow())
    }


def update_user(user_id, user_update, current_user):
    # Check permission
    if user_id != current_user["id"] and current_user["role_id"] != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this user"
        )

    # Check if user exists
    user = sql("SELECT * FROM users WHERE id = :user_id",
               user_id=user_id
               ).dict()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )

    # If it's a role change and user is not admin
    if user_update.role_id and user_update.role_id != user.role_id and current_user["role_id"] != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Regular users cannot change their role"
        )

    update_fields = []
    update_values = {"user_id": user_id, "updated_at": datetime.utcnow()}

    if user_update.email:
        email_exists = sql("SELECT id FROM users WHERE email = :email AND id != :user_id",
                           email=user_update.email, user_id=user_id
                           ).scalar()

        if email_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_update.email} is already in use"
            )

        update_fields.append("email = :email")
        update_values["email"] = user_update.email

    if user_update.first_name:
        update_fields.append("first_name = :first_name")
        update_values["first_name"] = user_update.first_name

    if user_update.last_name:
        update_fields.append("last_name = :last_name")
        update_values["last_name"] = user_update.last_name

    if user_update.password:
        update_fields.append("hashed_password = :hashed_password")
        update_values["hashed_password"] = get_password_hash(
            user_update.password)

    if user_update.role_id is not None:
        # Check if role exists
        role_exists = sql("SELECT id FROM roles WHERE id = :role_id",
                          role_id=user_update.role_id
                          ).scalar()

        if not role_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with ID {user_update.role_id} does not exist"
            )

        update_fields.append("role_id = :role_id")
        update_values["role_id"] = user_update.role_id

    if user_update.is_active is not None:
        update_fields.append("is_active = :is_active")
        update_values["is_active"] = user_update.is_active

    if update_fields:
        update_fields.append("updated_at = :updated_at")
        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = :user_id"
        sql(update_query, **update_values)

    # Get the updated user
    return get_user(user_id, current_user)
