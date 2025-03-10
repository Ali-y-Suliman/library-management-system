from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
import secrets
import base64
import hashlib
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_fernet_key(secret_key: str) -> bytes:
    """Derive a Fernet key from the secret key."""
    salt = b'library_management_system'  # Fixed salt for consistency
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
    return key


# Create cipher suite using the API_SECRET_KEY
cipher_suite = Fernet(get_fernet_key(settings.API_SECRET_KEY))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.API_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, settings.API_SECRET_KEY, algorithms=[settings.ALGORITHM])


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def encrypt_api_key(api_key: str) -> str:
    try:
        return cipher_suite.encrypt(api_key.encode()).decode()
    except Exception as e:
        raise ValueError(f"Failed to encrypt API key: {str(e)}")


def get_api_key_hash(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def decrypt_api_key(encrypted_api_key: str) -> str:
    """Decrypt API key retrieved from database."""
    try:
        return cipher_suite.decrypt(encrypted_api_key.encode()).decode()
    except Exception as e:
        # Handle decryption errors gracefully
        raise ValueError(f"Failed to decrypt API key: {str(e)}")


def get_api_key_expiry() -> datetime:
    """Get API key expiry timestamp."""
    return datetime.utcnow() + timedelta(minutes=settings.API_KEY_EXPIRY_MINUTES)
