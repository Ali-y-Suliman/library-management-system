from typing import Dict, Any
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.db.database import sql
from fastapi import APIRouter

# Create the WebSocket router
websocket_router = APIRouter()

logger = logging.getLogger(__name__)

# Store active connections
active_connections: Dict[str, WebSocket] = {}


async def notify_user(user_id: int, message: Dict[str, Any]):
    # Get the user's channel ID
    user = sql("SELECT websocket_connection_id FROM users WHERE id = :user_id",
               user_id=user_id
               ).dict()

    if not user or not user.websocket_connection_id:
        return False

    channel_id = user.websocket_connection_id

    if channel_id in active_connections:
        try:
            await active_connections[channel_id].send_json(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {str(e)}")
            return False
    return False


@websocket_router.websocket("/ws/{channel_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    channel_id: str
):
    """WebSocket endpoint for real-time notifications."""
    await websocket.accept()

    try:
        user = sql("""
                SELECT id, email, first_name, last_name 
                FROM users 
                WHERE websocket_connection_id = :channel_id AND is_active = TRUE
            """,
                   channel_id=channel_id
                   ).dict()

        if not user:
            await websocket.send_json({"error": "Invalid channel ID"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        active_connections[channel_id] = websocket

        await websocket.send_json({
            "type": "connection_established",
            "message": "WebSocket connection established. You will receive notifications here."
        })

        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "echo", "message": data})

    except WebSocketDisconnect:
        if channel_id in active_connections:
            del active_connections[channel_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        if channel_id in active_connections:
            del active_connections[channel_id]
