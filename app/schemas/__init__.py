"""Schemas package."""

from app.schemas. base import (
    ResponseSchema,
    PaginatedResponseSchema,
    ErrorResponseSchema,
)
from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignStatsResponse,
)
from app.schemas.message import (
    MessageCreate,
    MessageResponse,
    MessageStatusUpdate,
)
from app.schemas.csv_schema import (  # ← Cambiado aquí
    CSVRecipient,
    CSVUploadResponse,
    CSVValidationError,
)

__all__ = [
    # Base
    "ResponseSchema",
    "PaginatedResponseSchema",
    "ErrorResponseSchema",
    # Campaign
    "CampaignCreate",
    "CampaignUpdate",
    "CampaignResponse",
    "CampaignListResponse",
    "CampaignStatsResponse",
    # Message
    "MessageCreate",
    "MessageResponse",
    "MessageStatusUpdate",
    # CSV
    "CSVRecipient",
    "CSVUploadResponse",
    "CSVValidationError",
]