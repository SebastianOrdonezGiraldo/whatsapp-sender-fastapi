"""Message schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema
from app.utils.enums import MessageStatus


class MessageBase(BaseSchema):
    """Base message schema."""

    recipient_phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    recipient_name: Optional[str] = Field(None, max_length=255)
    template_variables: Optional[dict[str, str]] = None


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    campaign_id: int


class MessageResponse(MessageBase, TimestampSchema):
    """Schema for message response."""

    id: int
    campaign_id: int
    status: MessageStatus
    whatsapp_message_id: Optional[str] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: int
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None


class MessageStatusUpdate(BaseSchema):
    """Schema for updating message status (from webhook)."""

    whatsapp_message_id: str
    status: MessageStatus
    timestamp: datetime
    error_code: Optional[str] = None
    error_message: Optional[str] = None