from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str = Field(..., min_length=8)
    role_id: int = 3

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError(
                'Password must contain at least one uppercase letter')
        if not any(char in '!@#$%^&*()_+-=[]{}|;:,.<>?/' for char in v):
            raise ValueError(
                'Password must contain at least one special character')
        return v


class UserCreateResponse(BaseModel):
    email: str
    first_name: str
    last_name: str
    message: str = "User registered successfully"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    api_key: str
    api_key_expires_at: datetime
    websocket_channel_id: str


class APIKey(BaseModel):
    api_key: str
    expires_at: datetime
