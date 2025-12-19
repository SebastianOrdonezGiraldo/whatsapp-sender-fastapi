"""Campaign database model."""

from datetime import datetime
from typing import Optional, List

from sqlalchemy import String, Integer, Enum as SQLEnum, Text, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.utils.enums import CampaignStatus


class Campaign(Base, TimestampMixin):
    """Campaign model for storing campaign information."""

    __tablename__ = "campaigns"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Campaign Info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Template Info
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_language: Mapped[str] = mapped_column(String(10), default="es")

    # Status
    status: Mapped[CampaignStatus] = mapped_column(
        SQLEnum(CampaignStatus),
        default=CampaignStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Recipients
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    csv_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Progress
    messages_sent: Mapped[int] = mapped_column(Integer, default=0)
    messages_delivered: Mapped[int] = mapped_column(Integer, default=0)
    messages_failed: Mapped[int] = mapped_column(Integer, default=0)
    messages_read: Mapped[int] = mapped_column(Integer, default=0)

    # Cost
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    actual_cost: Mapped[float] = mapped_column(Float, default=0.0)

    # Scheduling
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Settings
    batch_size: Mapped[int] = mapped_column(Integer, default=50)
    delay_between_messages: Mapped[float] = mapped_column(Float, default=0.3)

    # Flags
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Campaign(id={self.id}, name='{self.name}', status={self.status})>"

    @property
    def progress_percentage(self) -> float:
        """Calculate campaign progress percentage."""
        if self.total_recipients == 0:
            return 0.0
        total_processed = self.messages_sent + self.messages_failed
        return (total_processed / self.total_recipients) * 100

    @property
    def success_rate(self) -> float:
        """Calculate message success rate."""
        if self.messages_sent == 0:
            return 0.0
        return (self.messages_delivered / self.messages_sent) * 100