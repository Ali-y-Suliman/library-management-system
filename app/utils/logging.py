import logging
from datetime import datetime
from fastapi import Request, Response
import json
import time
import uuid

# Configure logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Create logger
logger = logging.getLogger("library_api")

# Request ID middleware for tracking requests


class RequestIdMiddleware:
    async def __call__(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())

        request.state.request_id = request_id

        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "process_time": process_time,
            "status_code": response.status_code,
        }

        if response.status_code >= 500:
            logger.error(f"Request error: {json.dumps(log_data)}")
        elif response.status_code >= 400:
            logger.warning(f"Request warning: {json.dumps(log_data)}")
        else:
            logger.info(f"Request info: {json.dumps(log_data)}")

        return response


def log_exception(request: Request, exc: Exception) -> None:
    request_id = getattr(request.state, "request_id", "unknown")

    log_data = {
        "request_id": request_id,
        "timestamp": datetime.utcnow().isoformat(),
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host,
        "exception_type": type(exc).__name__,
        "exception_message": str(exc)
    }

    logger.error(f"Exception: {json.dumps(log_data)}")
