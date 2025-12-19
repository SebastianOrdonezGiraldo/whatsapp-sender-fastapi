"""FastAPI application main entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi. exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.core. logging import configure_logging, get_logger
from app.core. database import close_db
from app.core.exceptions import AppException
from app.core.exception_handlers import (
    app_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
)

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan events."""
    # Startup
    logger.info("Starting WhatsApp Sender API", version="0.1.0")
    configure_logging(debug=settings. debug)

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Backend API for bulk WhatsApp message sending",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "WhatsApp Sender API",
        "version": "0.1.0",
        "docs":  "/api/docs",
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "whatsapp-sender-api",
            "version":  "0.1.0",
        }
    )


# Include API routers
# IMPORTANTE: Esto debe estar al final pero en el mismo archivo
try:
    from app.api. v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")
    logger.info("API v1 router included successfully")
except Exception as e:
    logger.error("Failed to include API v1 router", error=str(e))
    raise