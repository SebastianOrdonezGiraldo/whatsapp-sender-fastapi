"""Message database model."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, ForeignKey, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin
from app.utils.enums import MessageStatus


class Message(Base, TimestampMixin):
    """Message model for individual WhatsApp messages."""

    __tablename__ = "messages"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Foreign Key
    campaign_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Recipient Info
    recipient_phone: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Template Variables
    template_variables: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[MessageStatus] = mapped_column(
        SQLEnum(MessageStatus),
        default=MessageStatus.PENDING,
        nullable=False,
        index=True,
    )

    # WhatsApp Response
    whatsapp_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Retry Info
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_retry_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Timestamps
    sent_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Relationship
    campaign: Mapped["Campaign"] = relationship("Campaign", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, phone={self.recipient_phone}, status={self.status})>"