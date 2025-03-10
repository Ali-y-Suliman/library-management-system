from fastapi import APIRouter

from typing import Dict, Any, List
from app.schemas import user as user_schema
from app.services import user as user_service
from fastapi import APIRouter, Depends
from app.api.deps import check_admin_access, get_current_active_user

router = APIRouter()


@router.get('/users', response_model=user_schema.PaginatedUserResponse)
def get_users(
    limit: int,
    page: int,
    _: Dict[str, Any] = Depends(check_admin_access)
):
    return user_service.get_users(page, limit)


@router.get("/roles", response_model=List[user_schema.UserRole])
def get_roles(
    _: Dict[str, Any] = Depends(check_admin_access)
):
    return user_service.get_roles(id)


@router.get("/{user_id}", response_model=user_schema.UserResponse)
def get_user(
    user_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    return user_service.get_user(user_id, current_user)


@router.put("/{user_id}", response_model=user_schema.UserResponse)
def update_user(
    user_id: int,
    user_update: user_schema.UserUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    return user_service.update_user(user_id, user_update, current_user)
