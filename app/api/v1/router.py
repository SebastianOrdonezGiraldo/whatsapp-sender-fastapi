"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import campaigns, templates

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(campaigns.router)
api_router.include_router(templates.router)  # ← NUEVO

# Future routers
# api_router.include_router(messages.router)
# api_router.include_router(stats.router)