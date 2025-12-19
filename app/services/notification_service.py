"""Service for real-time notifications using Redis pub/sub."""

import json
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.redis import get_redis
from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationService:
    """
    Service for publishing and subscribing to real-time notifications.
    
    Uses Redis pub/sub for broadcasting campaign and message updates.
    """

    def __init__(self):
        """Initialize notification service."""
        self.redis_client: Optional[Any] = None

    async def _get_redis(self):
        """Get Redis client (lazy initialization)."""
        if self.redis_client is None:
            self.redis_client = await get_redis()
        return self.redis_client

    async def publish_campaign_update(
        self,
        campaign_id: int,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Publish a campaign update event.
        
        Args:
            campaign_id: Campaign ID
            event_type: Type of event (status_changed, progress_updated, etc.)
            data: Event data
        """
        try:
            redis = await self._get_redis()
            
            event = {
                "type": event_type,
                "campaign_id": campaign_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            
            # Publish to campaign-specific channel
            channel = f"campaign:{campaign_id}"
            await redis.publish(channel, json.dumps(event))
            
            # Also publish to general campaigns channel
            await redis.publish("campaigns", json.dumps(event))
            
            logger.debug(
                "Campaign update published",
                campaign_id=campaign_id,
                event_type=event_type,
            )
            
        except Exception as e:
            logger.error(
                "Failed to publish campaign update",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )

    async def publish_message_update(
        self,
        campaign_id: int,
        message_id: int,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Publish a message update event.
        
        Args:
            campaign_id: Campaign ID
            message_id: Message ID
            event_type: Type of event (sent, delivered, failed, etc.)
            data: Event data
        """
        try:
            redis = await self._get_redis()
            
            event = {
                "type": event_type,
                "campaign_id": campaign_id,
                "message_id": message_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data,
            }
            
            # Publish to campaign-specific channel
            channel = f"campaign:{campaign_id}"
            await redis.publish(channel, json.dumps(event))
            
            logger.debug(
                "Message update published",
                campaign_id=campaign_id,
                message_id=message_id,
                event_type=event_type,
            )
            
        except Exception as e:
            logger.error(
                "Failed to publish message update",
                campaign_id=campaign_id,
                message_id=message_id,
                error=str(e),
                exc_info=True,
            )

    async def subscribe_to_campaign(
        self,
        campaign_id: int,
    ):
        """
        Subscribe to campaign updates.
        
        Args:
            campaign_id: Campaign ID to subscribe to
            
        Yields:
            Event dictionaries
        """
        try:
            redis = await self._get_redis()
            pubsub = redis.pubsub()
            
            # Subscribe to campaign-specific channel
            channel = f"campaign:{campaign_id}"
            await pubsub.subscribe(channel)
            
            logger.info(
                "Subscribed to campaign updates",
                campaign_id=campaign_id,
                channel=channel,
            )
            
            try:
                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    
                    if message and message["type"] == "message":
                        try:
                            event = json.loads(message["data"])
                            yield event
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "Failed to decode event",
                                error=str(e),
                            )
                            
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()
                
        except Exception as e:
            logger.error(
                "Error in campaign subscription",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None


# Singleton instance
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """
    Get notification service instance (singleton).
    
    Returns:
        NotificationService instance
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

