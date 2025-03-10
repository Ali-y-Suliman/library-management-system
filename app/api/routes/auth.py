from fastapi import APIRouter
from app.schemas.auth import UserCreate, Token, UserCreateResponse, UserLogin
from app.services import auth as auth_service

from typing import Dict, Any
from fastapi import APIRouter, Depends
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/register", response_model=UserCreateResponse)
def register_user(user_data: UserCreate):
    return auth_service.register_user(user_data)


@router.post("/login", response_model=Token)
def login(user_data: UserLogin):
    return auth_service.login_user(user_data)


@router.post("/logout")
def logout(current_user: Dict[str, Any] = Depends(get_current_active_user)):
    return auth_service.logout(current_user)
