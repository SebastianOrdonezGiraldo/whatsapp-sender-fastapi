"""Campaign repository for database operations."""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.campaign import Campaign
from app.models.message import Message
from app.repositories.base import BaseRepository
from app.utils.enums import CampaignStatus


class CampaignRepository(BaseRepository[Campaign]):
    """
    Repository for Campaign model.

    Extends BaseRepository with campaign-specific queries.
    """

    def __init__(self, session: AsyncSession):
        """Initialize campaign repository."""
        super().__init__(Campaign, session)

    async def get_by_status(
            self,
            status: CampaignStatus,
            *,
            skip: int = 0,
            limit: int = 100,
    ) -> List[Campaign]:
        """
        Get campaigns by status.

        Args:
            status: Campaign status to filter by
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of campaigns with the specified status
        """
        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.status == status)
            .order_by(Campaign.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_messages(self, id: int) -> Optional[Campaign]:
        """
        Get campaign with its messages eagerly loaded.

        Args:
            id: Campaign ID

        Returns:
            Campaign with messages or None
        """
        result = await self.session.execute(
            select(Campaign)
            .options(selectinload(Campaign.messages))
            .where(Campaign.id == id)
        )
        return result.scalar_one_or_none()

    async def get_active_campaigns(self) -> List[Campaign]:
        """
        Get all active campaigns (draft, scheduled, running, paused).

        Returns:
            List of active campaigns
        """
        active_statuses = [
            CampaignStatus.DRAFT,
            CampaignStatus.SCHEDULED,
            CampaignStatus.RUNNING,
            CampaignStatus.PAUSED,
        ]

        result = await self.session.execute(
            select(Campaign)
            .where(Campaign.status.in_(active_statuses))
            .order_by(Campaign.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_scheduled_ready(self) -> List[Campaign]:
        """
        Get campaigns scheduled to start now or in the past.

        Returns:
            List of campaigns ready to be started
        """
        now = datetime.utcnow()

        result = await self.session.execute(
            select(Campaign)
            .where(
                and_(
                    Campaign.status == CampaignStatus.SCHEDULED,
                    Campaign.scheduled_at <= now,
                )
            )
        )
        return list(result.scalars().all())

    async def update_counters(
            self,
            campaign_id: int,
            *,
            messages_sent: Optional[int] = None,
            messages_delivered: Optional[int] = None,
            messages_failed: Optional[int] = None,
            messages_read: Optional[int] = None,
    ) -> Optional[Campaign]:
        """
        Update campaign message counters.

        Args:
            campaign_id: Campaign ID
            messages_sent:  Increment sent counter
            messages_delivered: Increment delivered counter
            messages_failed:  Increment failed counter
            messages_read: Increment read counter

        Returns:
            Updated campaign or None if not found
        """
        campaign = await self.get(campaign_id)
        if not campaign:
            return None

        if messages_sent is not None:
            campaign.messages_sent += messages_sent
        if messages_delivered is not None:
            campaign.messages_delivered += messages_delivered
        if messages_failed is not None:
            campaign.messages_failed += messages_failed
        if messages_read is not None:
            campaign.messages_read += messages_read

        await self.session.flush()
        await self.session.refresh(campaign)
        return campaign

    async def update_status(
            self,
            campaign_id: int,
            status: CampaignStatus,
    ) -> Optional[Campaign]:
        """
        Update campaign status and related timestamps.

        Args:
            campaign_id: Campaign ID
            status: New status

        Returns:
            Updated campaign or None if not found
        """
        campaign = await self.get(campaign_id)
        if not campaign:
            return None

        campaign.status = status

        # Update timestamps based on status
        now = datetime.utcnow()
        if status == CampaignStatus.RUNNING:
            campaign.started_at = now
        elif status in [CampaignStatus.COMPLETED, CampaignStatus.FAILED, CampaignStatus.CANCELLED]:
            campaign.completed_at = now

        await self.session.flush()
        await self.session.refresh(campaign)
        return campaign

    async def get_stats(self, campaign_id: int) -> Optional[dict]:
        """
        Get campaign statistics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Dictionary with campaign stats or None
        """
        campaign = await self.get(campaign_id)
        if not campaign:
            return None

        # Calculate progress
        progress_percentage = 0.
        0
        if campaign.total_recipients > 0:
            total_processed = campaign.messages_sent + campaign.messages_failed
            progress_percentage = (total_processed / campaign.total_recipients) * 100

        # Calculate success rate
        success_rate = 0.0
        if campaign.messages_sent > 0:
            success_rate = (campaign.messages_delivered / campaign.messages_sent) * 100

        return {
            "campaign_id": campaign.id,
            "status": campaign.status,
            "total_recipients": campaign.total_recipients,
            "messages_sent": campaign.messages_sent,
            "messages_delivered": campaign.messages_delivered,
            "messages_failed": campaign.messages_failed,
            "messages_read": campaign.messages_read,
            "progress_percentage": round(progress_percentage, 2),
            "success_rate": round(success_rate, 2),
            "estimated_cost": campaign.estimated_cost,
            "actual_cost": campaign.actual_cost,
            "started_at": campaign.started_at,
            "completed_at": campaign.completed_at,
        }