import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Library Management System"

    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "0000")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "3306")
    DB_NAME: str = os.getenv("DB_NAME", "library_db")
    DATABASE_URL: str = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    API_SECRET_KEY: str = os.getenv("API_SECRET_KEY", "your-secret-key-here")
    API_KEY_EXPIRY_MINUTES: int = int(
        os.getenv("API_KEY_EXPIRY_MINUTES", "43200"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")

    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8000"))

    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))

    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    SSL_CERT_PATH: str = os.getenv("SSL_CERT_PATH", "./app/ssl/cert.pem")
    SSL_KEY_PATH: str = os.getenv("SSL_KEY_PATH", "./app/ssl/key.pem")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
