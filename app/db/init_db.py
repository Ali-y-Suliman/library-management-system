import logging
from sqlalchemy.sql import text
from app.db.database import engine
from app.db.models import Base

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize the database, create tables if they don't exist."""
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"Database connection test: {result.scalar()}")

    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise
