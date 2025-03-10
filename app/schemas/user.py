from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from enum import Enum
from datetime import datetime


class RoleType(str, Enum):
    ADMIN = "admin"
    LIBRARIAN = "librarian"
    USER = "user"


class UserRole(BaseModel):
    id: int
    name: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)


class UserResponse(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role_id: int
    role_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    active_borrow_count: int
    overdue_borrow_count: int
    has_api_key: bool


class PaginatedUserResponse(BaseModel):
    users: List[UserBase]
    page: int
    size: int
    total: int
    number_of_pages: int
