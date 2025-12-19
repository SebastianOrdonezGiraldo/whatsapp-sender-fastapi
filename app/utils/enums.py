"""Enumerations for the application."""

from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign status enum."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageStatus(str, Enum):
    """Message delivery status enum."""

    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class TemplateLanguage(str, Enum):
    """WhatsApp template language codes."""

    EN = "en"
    ES = "es"
    PT = "pt"
    FR = "fr"