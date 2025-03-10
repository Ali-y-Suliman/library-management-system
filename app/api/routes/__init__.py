from fastapi import APIRouter
from app.core.config import settings
from app.api.routes import auth, books, user, borrow
from app.websockets.manager import websocket_router

# Create a main router that includes all other routers
router = APIRouter()

# Include all route modules with their prefixes and tags
router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(books.router, prefix="/books", tags=["books"])
router.include_router(user.router, prefix="/users", tags=["users"])
router.include_router(borrow.router, prefix="/borrow", tags=["borrowing"])

# Export the websocket router as well
# This allows both routers to be imported from the same module
