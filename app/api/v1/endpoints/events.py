"""SSE endpoint for real-time campaign updates."""

from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import json

from app.core.dependencies import get_campaign_service
from app.services.campaign_service import CampaignService
from app.services.notification_service import get_notification_service, NotificationService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


async def generate_sse_event(event_type: str, data: dict) -> str:
    """
    Generate SSE-formatted event string.
    
    Args:
        event_type: Event type
        data: Event data
        
    Returns:
        SSE-formatted string
    """
    event_data = json.dumps(data)
    return f"event: {event_type}\ndata: {event_data}\n\n"


@router.get(
    "/campaigns/{campaign_id}/stream",
    summary="Stream campaign updates (SSE)",
    description="Server-Sent Events stream for real-time campaign updates",
)
async def stream_campaign_updates(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service),
    notification_service: NotificationService = Depends(get_notification_service),
) -> StreamingResponse:
    """
    Stream real-time updates for a campaign using Server-Sent Events (SSE).
    
    Args:
        campaign_id: Campaign ID to stream updates for
        service: Campaign service (injected)
        notification_service: Notification service (injected)
        
    Returns:
        StreamingResponse with SSE events
        
    Raises:
        HTTPException: If campaign not found
    """
    # Verify campaign exists
    try:
        campaign = await service.get_campaign(campaign_id)
    except Exception as e:
        logger.warning(
            "Campaign not found for SSE stream",
            campaign_id=campaign_id,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found",
        )
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """
        Generate SSE events from Redis pub/sub.
        
        Yields:
            SSE-formatted event strings
        """
        try:
            # Send initial connection event
            initial_data = {
                "type": "connected",
                "campaign_id": campaign_id,
                "message": "Connected to campaign update stream",
            }
            yield await generate_sse_event("connected", initial_data)
            
            # Send initial campaign state
            from app.schemas.campaign import CampaignResponse
            campaign_data = CampaignResponse.model_validate(campaign).model_dump()
            initial_state = {
                "type": "initial_state",
                "campaign_id": campaign_id,
                "data": campaign_data,
            }
            yield await generate_sse_event("initial_state", initial_state)
            
            # Subscribe to campaign updates
            async for event in notification_service.subscribe_to_campaign(campaign_id):
                try:
                    # Format event for SSE
                    sse_event = {
                        "type": event.get("type", "update"),
                        "campaign_id": event.get("campaign_id"),
                        "timestamp": event.get("timestamp"),
                        "data": event.get("data", {}),
                    }
                    
                    # Add message_id if present
                    if "message_id" in event:
                        sse_event["message_id"] = event["message_id"]
                    
                    yield await generate_sse_event(
                        event.get("type", "update"),
                        sse_event,
                    )
                    
                except Exception as e:
                    logger.error(
                        "Error processing SSE event",
                        campaign_id=campaign_id,
                        error=str(e),
                        exc_info=True,
                    )
                    # Send error event
                    error_event = {
                        "type": "error",
                        "campaign_id": campaign_id,
                        "error": str(e),
                    }
                    yield await generate_sse_event("error", error_event)
                    
        except Exception as e:
            logger.error(
                "Error in SSE event generator",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )
            # Send final error event
            error_event = {
                "type": "error",
                "campaign_id": campaign_id,
                "error": "Stream connection error",
            }
            yield await generate_sse_event("error", error_event)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get(
    "/campaigns/stream",
    summary="Stream all campaigns updates (SSE)",
    description="Server-Sent Events stream for all campaigns updates",
)
async def stream_all_campaigns_updates(
    notification_service: NotificationService = Depends(get_notification_service),
) -> StreamingResponse:
    """
    Stream real-time updates for all campaigns using Server-Sent Events (SSE).
    
    Args:
        notification_service: Notification service (injected)
        
    Returns:
        StreamingResponse with SSE events
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        """
        Generate SSE events from Redis pub/sub for all campaigns.
        
        Yields:
            SSE-formatted event strings
        """
        try:
            redis = await notification_service._get_redis()
            pubsub = redis.pubsub()
            
            # Subscribe to general campaigns channel
            await pubsub.subscribe("campaigns")
            
            # Send initial connection event
            initial_data = {
                "type": "connected",
                "message": "Connected to all campaigns update stream",
            }
            yield await generate_sse_event("connected", initial_data)
            
            try:
                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    
                    if message and message["type"] == "message":
                        try:
                            event = json.loads(message["data"])
                            
                            # Format event for SSE
                            sse_event = {
                                "type": event.get("type", "update"),
                                "campaign_id": event.get("campaign_id"),
                                "timestamp": event.get("timestamp"),
                                "data": event.get("data", {}),
                            }
                            
                            # Add message_id if present
                            if "message_id" in event:
                                sse_event["message_id"] = event["message_id"]
                            
                            yield await generate_sse_event(
                                event.get("type", "update"),
                                sse_event,
                            )
                            
                        except json.JSONDecodeError as e:
                            logger.warning(
                                "Failed to decode event",
                                error=str(e),
                            )
                            
            finally:
                await pubsub.unsubscribe("campaigns")
                await pubsub.close()
                
        except Exception as e:
            logger.error(
                "Error in SSE event generator (all campaigns)",
                error=str(e),
                exc_info=True,
            )
            # Send final error event
            error_event = {
                "type": "error",
                "error": "Stream connection error",
            }
            yield await generate_sse_event("error", error_event)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

