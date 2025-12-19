"""API v1 router."""

from fastapi import APIRouter

# Import routers
from app.api.v1.endpoints.campaigns import router as campaigns_router
from app.api.v1.endpoints.templates import router as templates_router
from app.api.v1.endpoints.events import router as events_router
from app.api.v1.endpoints.webhooks import router as webhooks_router

# Create main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(campaigns_router)
api_router.include_router(templates_router)
api_router.include_router(events_router)
api_router.include_router(webhooks_router)