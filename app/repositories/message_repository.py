"""Message repository for database operations."""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.base import BaseRepository
from app.utils.enums import MessageStatus


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message model.

    Extends BaseRepository with message-specific queries.
    """

    def __init__(self, session: AsyncSession):
        """Initialize message repository."""
        super().__init__(Message, session)

    async def get_by_campaign(
            self,
            campaign_id: int,
            *,
            skip: int = 0,
            limit: int = 100,
            status: Optional[MessageStatus] = None,
    ) -> List[Message]:
        """
        Get messages by campaign ID.

        Args:
            campaign_id: Campaign ID
            skip: Number of records to skip
            limit: Maximum number of records
            status: Optional status filter

        Returns:
            List of messages for the campaign
        """
        query = select(Message).where(Message.campaign_id == campaign_id)

        if status:
            query = query.where(Message.status == status)

        query = query.order_by(Message.created_at.desc()).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending(self, campaign_id: int, limit: int = 50) -> List[Message]:
        """
        Get pending messages for a campaign.

        Args:
            campaign_id: Campaign ID
            limit: Maximum number of messages

        Returns:
            List of pending messages
        """
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.campaign_id == campaign_id,
                    Message.status == MessageStatus.PENDING,
                )
            )
            .order_by(Message.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_create(self, messages_data: List[dict]) -> List[Message]:
        """
        Create multiple messages at once.

        Args:
            messages_data: List of dictionaries with message data

        Returns:
            List of created message instances
        """
        messages = [Message(**data) for data in messages_data]
        self.session.add_all(messages)
        await self.session.flush()

        # Refresh all instances to get generated IDs
        for message in messages:
            await self.session.refresh(message)

        return messages

    async def update_status(
            self,
            message_id: int,
            status: MessageStatus,
            *,
            whatsapp_message_id: Optional[str] = None,
            error_message: Optional[str] = None,
            error_code: Optional[str] = None,
    ) -> Optional[Message]:
        """
        Update message status and related fields.

        Args:
            message_id: Message ID
            status: New status
            whatsapp_message_id: WhatsApp message ID (if sent)
            error_message: Error message (if failed)
            error_code: Error code (if failed)

        Returns:
            Updated message or None if not found
        """
        message = await self.get(message_id)
        if not message:
            return None

        from datetime import datetime
        now = datetime.utcnow()

        message.status = status

        if whatsapp_message_id:
            message.whatsapp_message_id = whatsapp_message_id

        if error_message:
            message.error_message = error_message

        if error_code:
            message.error_code = error_code

        # Update timestamps based on status
        if status == MessageStatus.SENT:
            message.sent_at = now
        elif status == MessageStatus.DELIVERED:
            message.delivered_at = now
        elif status == MessageStatus.READ:
            message.read_at = now
        elif status == MessageStatus.FAILED:
            message.failed_at = now
            message.retry_count += 1

        await self.session.flush()
        await self.session.refresh(message)
        return message

    async def count_by_status(
            self,
            campaign_id: int,
            status: MessageStatus,
    ) -> int:
        """
        Count messages by status for a campaign.

        Args:
            campaign_id: Campaign ID
            status: Message status

        Returns:
            Number of messages with the status
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count())
            .select_from(Message)
            .where(
                and_(
                    Message.campaign_id == campaign_id,
                    Message.status == status,
                )
            )
        )
        return result.scalar_one()

    async def get_failed_retryable(
            self,
            campaign_id: int,
            max_retries: int = 3,
            limit: int = 50,
    ) -> List[Message]:
        """
        Get failed messages that can be retried.

        Args:
            campaign_id: Campaign ID
            max_retries: Maximum number of retry attempts
            limit: Maximum number of messages

        Returns:
            List of failed messages eligible for retry
        """
        result = await self.session.execute(
            select(Message)
            .where(
                and_(
                    Message.campaign_id == campaign_id,
                    Message.status == MessageStatus.FAILED,
                    Message.retry_count < max_retries,
                )
            )
            .order_by(Message.failed_at)
            .limit(limit)
        )
        return list(result.scalars().all())