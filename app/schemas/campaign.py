"""Campaign schemas for API requests and responses."""

from datetime import datetime
from typing import Optional

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, TimestampSchema
from app.utils.enums import CampaignStatus


class CampaignBase(BaseSchema):
    """Base campaign schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_name: str = Field(..., min_length=1, max_length=255)
    template_language: str = Field(default="es", pattern="^[a-z]{2}$")
    batch_size: int = Field(default=50, ge=1, le=100)
    delay_between_messages: float = Field(default=0.3, ge=0.1, le=5.0)
    is_test: bool = Field(default=False)


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign."""

    scheduled_at: Optional[datetime] = None

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        if v and v < datetime.now():
            raise ValueError("scheduled_at must be in the future")
        return v


class CampaignUpdate(BaseSchema):
    """Schema for updating a campaign."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[CampaignStatus] = None
    scheduled_at: Optional[datetime] = None
    batch_size: Optional[int] = Field(None, ge=1, le=100)
    delay_between_messages: Optional[float] = Field(None, ge=0.1, le=5.0)


class CampaignResponse(CampaignBase, TimestampSchema):
    """Schema for campaign response."""

    id: int
    status: CampaignStatus
    total_recipients: int
    messages_sent: int
    messages_delivered: int
    messages_failed: int
    messages_read: int
    estimated_cost: float
    actual_cost: float
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.total_recipients == 0:
            return 0.0
        total_processed = self.messages_sent + self.messages_failed
        return round((total_processed / self.total_recipients) * 100, 2)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.messages_sent == 0:
            return 0.0
        return round((self.messages_delivered / self.messages_sent) * 100, 2)


class CampaignListResponse(BaseSchema):
    """Schema for campaign list item."""

    id: int
    name: str
    status: CampaignStatus
    total_recipients: int
    messages_sent: int
    messages_delivered: int
    messages_failed: int
    progress_percentage: float
    created_at: datetime
    scheduled_at: Optional[datetime] = None


class CampaignStatsResponse(BaseSchema):
    """Schema for campaign statistics."""

    total_campaigns: int
    active_campaigns: int
    completed_campaigns: int
    total_messages_sent: int
    total_messages_delivered: int
    total_messages_failed: int
    overall_success_rate: float
    total_cost: float