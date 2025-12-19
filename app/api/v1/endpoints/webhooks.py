"""Webhook endpoints for WhatsApp status updates."""

from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.logging import get_logger
from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.repositories.message_repository import MessageRepository
from app.repositories.campaign_repository import CampaignRepository
from app.models.message import Message
from app.utils.enums import MessageStatus
from app.services.notification_service import get_notification_service

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify_webhook_signature(
    request_body: bytes,
    signature: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
) -> bool:
    """
    Verify webhook signature from Meta.
    
    Args:
        request_body: Raw request body
        signature: Signature from X-Hub-Signature-256 header
        
    Returns:
        True if signature is valid
    """
    # TODO: Implement signature verification
    # For now, we'll skip verification in development
    # In production, you should verify using HMAC SHA256
    if settings.debug:
        return True
    
    if not signature:
        return False
    
    # TODO: Implement actual signature verification
    # import hmac
    # import hashlib
    # expected_signature = hmac.new(
    #     settings.whatsapp_webhook_secret.encode(),
    #     request_body,
    #     hashlib.sha256
    # ).hexdigest()
    # return hmac.compare_digest(f"sha256={expected_signature}", signature)
    
    return True


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: Optional[str] = None,
    hub_verify_token: Optional[str] = None,
    hub_challenge: Optional[str] = None,
):
    """
    Verify webhook endpoint (GET request from Meta).
    
    Meta sends a GET request to verify the webhook endpoint.
    You need to configure the verify token in Meta's webhook settings.
    
    Args:
        hub_mode: Should be "subscribe"
        hub_verify_token: Token to verify
        hub_challenge: Challenge string to return
        
    Returns:
        Challenge string if verification succeeds
    """
    # TODO: Configure verify token in settings
    VERIFY_TOKEN = "your-verify-token-here"  # Should be in settings
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return int(hub_challenge) if hub_challenge else "OK"
    
    logger.warning(
        "Webhook verification failed",
        hub_mode=hub_mode,
        token_received=hub_verify_token is not None,
    )
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed",
    )


@router.post("/whatsapp")
async def handle_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_hub_signature_256: Optional[str] = Header(None),
):
    """
    Handle WhatsApp webhook events (POST request from Meta).
    
    Processes status updates for messages (sent, delivered, read, failed).
    
    Args:
        request: FastAPI request object
        db: Database session
        x_hub_signature_256: Webhook signature header
        
    Returns:
        Success response
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify signature (in production)
        if not verify_webhook_signature(body, x_hub_signature_256):
            logger.warning("Webhook signature verification failed")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook signature",
            )
        
        # Parse JSON body
        data = await request.json()
        
        logger.debug("Webhook received", data=data)
        
        # Handle webhook event
        if "object" in data and data["object"] == "whatsapp_business_account":
            entries = data.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    value = change.get("value", {})
                    
                    # Handle status updates
                    if "statuses" in value:
                        statuses = value["statuses"]
                        await _handle_status_updates(statuses, db)
                    
                    # Handle messages (for future use)
                    if "messages" in value:
                        messages = value["messages"]
                        await _handle_messages(messages, db)
        
        return {"status": "success"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error handling webhook",
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook",
        )


async def _handle_status_updates(
    statuses: list[Dict[str, Any]],
    db: AsyncSession,
) -> None:
    """
    Handle message status updates from webhook.
    
    Args:
        statuses: List of status update objects
        db: Database session
    """
    message_repo = MessageRepository(db)
    campaign_repo = CampaignRepository(db)
    notification_service = get_notification_service()
    
    for status_update in statuses:
        try:
            whatsapp_message_id = status_update.get("id")
            status_value = status_update.get("status")
            recipient_id = status_update.get("recipient_id")
            timestamp = status_update.get("timestamp")
            
            if not whatsapp_message_id:
                logger.warning("Status update missing message ID", status_update=status_update)
                continue
            
            # Find message by WhatsApp message ID
            result = await db.execute(
                select(Message).where(Message.whatsapp_message_id == whatsapp_message_id)
            )
            message = result.scalar_one_or_none()
            
            if not message:
                logger.warning(
                    "Message not found for status update",
                    whatsapp_message_id=whatsapp_message_id,
                )
                continue
            
            # Map WhatsApp status to our MessageStatus enum
            new_status = _map_whatsapp_status(status_value)
            
            if not new_status:
                logger.warning(
                    "Unknown status value",
                    status=status_value,
                    whatsapp_message_id=whatsapp_message_id,
                )
                continue
            
            # Update message status
            updated_message = await message_repo.update_status(
                message.id,
                new_status,
            )
            
            if not updated_message:
                continue
            
            # Update campaign counters
            if new_status == MessageStatus.DELIVERED:
                await campaign_repo.update_counters(
                    message.campaign_id,
                    messages_delivered=1,
                )
            elif new_status == MessageStatus.READ:
                await campaign_repo.update_counters(
                    message.campaign_id,
                    messages_read=1,
                )
            
            await db.commit()
            
            # Publish notification
            await notification_service.publish_message_update(
                message.campaign_id,
                message.id,
                f"message_{status_value}",
                {
                    "status": status_value,
                    "whatsapp_message_id": whatsapp_message_id,
                    "timestamp": timestamp,
                },
            )
            
            logger.info(
                "Message status updated",
                message_id=message.id,
                whatsapp_message_id=whatsapp_message_id,
                old_status=message.status,
                new_status=new_status,
            )
            
        except Exception as e:
            logger.error(
                "Error processing status update",
                status_update=status_update,
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            continue


async def _handle_messages(
    messages: list[Dict[str, Any]],
    db: AsyncSession,
) -> None:
    """
    Handle incoming messages (for future use).
    
    Args:
        messages: List of message objects
        db: Database session
    """
    # TODO: Implement handling of incoming messages if needed
    logger.debug("Received messages", count=len(messages))


def _map_whatsapp_status(whatsapp_status: str) -> Optional[MessageStatus]:
    """
    Map WhatsApp status to our MessageStatus enum.
    
    Args:
        whatsapp_status: WhatsApp status string
        
    Returns:
        MessageStatus enum value or None
    """
    status_mapping = {
        "sent": MessageStatus.SENT,
        "delivered": MessageStatus.DELIVERED,
        "read": MessageStatus.READ,
        "failed": MessageStatus.FAILED,
    }
    
    return status_mapping.get(whatsapp_status.lower())

