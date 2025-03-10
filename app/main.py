import logging
import ssl
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.db.init_db import init_db
from app.db.seed_data import seed_data
from app.core.config import settings
from app.utils.rate_limiter import rate_limit_dependency
from app.api.routes import router as api_router
from app.websockets.manager import websocket_router
from starlette.responses import JSONResponse, RedirectResponse
from fastapi.openapi.utils import get_openapi


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    dependencies=[Depends(rate_limit_dependency)],
    docs_url="/swagger",
    redoc_url="/redoc",
)

# custom OpenAPI schema to add security schemes


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        description="Library Management System API",
        routes=app.routes,
    )

    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "api_key": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Enter API key"
        },
        "bearer": {
            "type": "http",
            "scheme": "bearer",
            "in": "header",
            "bearerFormat": "JWT",
            "description": "Enter JWT token (without 'Bearer' prefix)"
        },
    }

    # Add security requirement to all operations except login and register
    if "paths" in openapi_schema:
        for path, path_item in openapi_schema["paths"].items():

            if (f"{settings.API_V1_STR}/auth/login" in path or
                    f"{settings.API_V1_STR}/auth/register" in path):
                continue

            for operation in path_item.values():
                operation["security"] = [
                    {"bearer": []},
                    {"api_key": []}
                ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/swagger")


# Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# General exception handler


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(websocket_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application...")
    try:
        # Initialize the database
        init_db()
        # Seed initial data
        seed_data()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {e}")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # SSL context for HTTPS
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(settings.SSL_CERT_PATH, settings.SSL_KEY_PATH)

    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=False,
        ssl_keyfile=settings.SSL_KEY_PATH,
        ssl_certfile=settings.SSL_CERT_PATH
    )
