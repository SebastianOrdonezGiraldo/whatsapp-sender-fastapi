"""Dependency injection functions for FastAPI."""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import Settings, get_settings
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.message_repository import MessageRepository
from app.services.campaign_service import CampaignService


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_campaign_repository(
    db: AsyncSession = Depends(get_db),
) -> CampaignRepository:
    """
    Dependency to get campaign repository.

    Args:
        db: Database session (injected)

    Returns:
        CampaignRepository instance
    """
    return CampaignRepository(db)


def get_message_repository(
    db: AsyncSession = Depends(get_db),
) -> MessageRepository:
    """
    Dependency to get message repository.

    Args:
        db: Database session (injected)

    Returns:
        MessageRepository instance
    """
    return MessageRepository(db)


def get_campaign_service(
    campaign_repo: CampaignRepository = Depends(get_campaign_repository),
    message_repo: MessageRepository = Depends(get_message_repository),
) -> CampaignService:
    """
    Dependency to get campaign service.

    Args:
        campaign_repo: Campaign repository (injected)
        message_repo: Message repository (injected)

    Returns:
        CampaignService instance

    Example:
        @app.post("/campaigns")
        async def create_campaign(
            campaign_in: CampaignCreate,
            service: CampaignService = Depends(get_campaign_service)
        ):
            campaign = await service.create_campaign(campaign_in)
            return campaign
    """
    return CampaignService(campaign_repo, message_repo)


def get_settings_dependency() -> Settings:
    """
    Dependency to get application settings.

    Returns:
        Settings instance
    """
    return get_settings()