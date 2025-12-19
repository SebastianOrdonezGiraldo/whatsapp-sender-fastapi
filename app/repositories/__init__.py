"""Repositories package."""

from app.repositories.base import BaseRepository
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.message_repository import MessageRepository

__all__ = [
    "BaseRepository",
    "CampaignRepository",
    "MessageRepository",
]