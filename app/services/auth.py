import logging

from app.db.database import sql
from typing import Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import UserCreate, UserLogin
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    generate_api_key, get_api_key_expiry, encrypt_api_key, get_api_key_hash
)
from app.api.deps import get_current_active_user


logger = logging.getLogger(__name__)


def login_user(user_data: UserLogin):

    # Get user by email
    user = sql("SELECT id, email, hashed_password, is_active FROM users WHERE email = :email",
               email=user_data.email
               ).dict()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user['is_active']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(user_data.password, user['hashed_password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user['id'], expires_delta=access_token_expires
    )

    # Generate API key
    original_api_key = generate_api_key()  # Keep this for returning to the user
    api_key_expires_at = get_api_key_expiry()
    encrypted_api_key = encrypt_api_key(original_api_key)
    api_key_hash = get_api_key_hash(original_api_key)

    import uuid
    websocket_channel_id = str(uuid.uuid4())

    # Update user with API key
    sql("""
            UPDATE users 
            SET api_key = :api_key, 
                api_key_hash = :api_key_hash,
                api_key_expires_at = :api_key_expires_at,
                websocket_connection_id = :websocket_channel_id,
                updated_at = :updated_at
            WHERE id = :user_id
        """,
        api_key=encrypted_api_key,
        api_key_hash=api_key_hash,
        api_key_expires_at=api_key_expires_at,
        websocket_channel_id=websocket_channel_id,
        updated_at=datetime.utcnow(),
        user_id=user['id']
        )

    token_expires_at = datetime.utcnow() + access_token_expires

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": token_expires_at,
        "api_key": original_api_key,
        "api_key_expires_at": api_key_expires_at,
        "websocket_channel_id": websocket_channel_id
    }


def register_user(user_data: UserCreate):

    user_exists = sql("SELECT id FROM users WHERE email = :email",
                      email=user_data.email
                      ).scalar()

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    hashed_password = get_password_hash(user_data.password)
    now = datetime.utcnow()

    sql("""
            INSERT INTO users 
            (email, first_name, last_name, hashed_password, role_id, is_active)
            VALUES 
            (:email, :first_name, :last_name, :hashed_password, :role_id, TRUE)
        """,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
        role_id=user_data.role_id

        )

    new_user_id = sql("SELECT id FROM users WHERE email = :email",
                      email=user_data.email
                      ).scalar()

    return {
        "id": new_user_id,
        "email": user_data.email,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "message": "User registered successfully"
    }


def logout(current_user):
    user_id = current_user["id"]

    sql("""
            UPDATE users 
            SET websocket_connection_id = NULL
            WHERE id = :user_id
        """,
        user_id=user_id
        )

    return {"message": "Successfully logged out"}
