from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.db.database import sql
from app.core.security import decode_access_token, get_api_key_hash


# OAuth2 scheme for JWT tokens
# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl=f"{settings.API_V1_STR}/auth/login")

oauth2_scheme = HTTPBearer(auto_error=False)

# API Key scheme
# api_key_header = APIKeyHeader(name="X-API-Key")


def get_current_user_any_method(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    token: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme)
) -> Dict[str, Any]:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if x_api_key:
        user = get_current_user_by_api_key(x_api_key)

        if user:
            return {
                "id": user['id'],
                "email": user['email'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "role_id": user['role_id'],
                "websocket_connection_id": user['websocket_connection_id'],
                "is_active": user['is_active']
            }

        if not user:
            raise credentials_exception

    if token:
        try:

            user = get_current_user_by_token(token, credentials_exception)

            if user:
                return {
                    "id": user['id'],
                    "email": user['email'],
                    "first_name": user['first_name'],
                    "last_name": user['last_name'],
                    "role_id": user['role_id'],
                    "websocket_connection_id": user['websocket_connection_id'],
                    "is_active": user['is_active']
                }
        except JWTError:
            pass

    raise credentials_exception


def get_current_user_by_api_key(api_key):
    hashed_key = get_api_key_hash(api_key)
    return sql("""
            SELECT * FROM users
            WHERE api_key_hash = :hashed_key
            AND api_key_expires_at > NOW()
            AND is_active = TRUE
            """,
               hashed_key=hashed_key
               ).dict()


def get_current_user_by_token(token, credentials_exception):
    try:
        payload = decode_access_token(token.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return sql("SELECT * FROM users WHERE id = :user_id AND is_active = TRUE",
               user_id=user_id
               ).dict()


def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user_any_method)
) -> Dict[str, Any]:

    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def check_admin_access(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    if current_user["role_id"] != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def check_librarian_access(current_user: Dict[str, Any] = Depends(get_current_active_user)) -> Dict[str, Any]:
    if current_user["role_id"] not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
