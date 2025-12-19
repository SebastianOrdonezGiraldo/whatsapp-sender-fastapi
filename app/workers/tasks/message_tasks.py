"""Background tasks for processing WhatsApp messages."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.logging import get_logger
from app.core.exceptions import ExternalServiceError
from app.repositories.message_repository import MessageRepository
from app.repositories.campaign_repository import CampaignRepository
from app.services.whatsapp_service import WhatsAppService
from app.utils.enums import MessageStatus, CampaignStatus

settings = get_settings()
logger = get_logger(__name__)


def send_message_task(message_id: int) -> Dict[str, Any]:
    """
    Synchronous wrapper for async message sending.
    
    This function is called by RQ workers (which are synchronous).
    It creates an async event loop to run the async send logic.
    
    Args:
        message_id: ID of the message to send
        
    Returns:
        Dictionary with task result
    """
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_send_message_async(message_id))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(
            "Error in send_message_task",
            message_id=message_id,
            error=str(e),
            exc_info=True,
        )
        return {
            "success": False,
            "message_id": message_id,
            "error": str(e),
        }


async def _send_message_async(message_id: int) -> Dict[str, Any]:
    """
    Async function to send a WhatsApp message.
    
    Args:
        message_id: ID of the message to send
        
    Returns:
        Dictionary with result
    """
    async with AsyncSessionLocal() as session:
        try:
            message_repo = MessageRepository(session)
            campaign_repo = CampaignRepository(session)
            whatsapp_service = WhatsAppService()
            
            # Get message
            message = await message_repo.get(message_id)
            if not message:
                logger.warning("Message not found", message_id=message_id)
                return {
                    "success": False,
                    "message_id": message_id,
                    "error": "Message not found",
                }
            
            # Check if campaign is still running
            campaign = await campaign_repo.get(message.campaign_id)
            if not campaign:
                logger.warning(
                    "Campaign not found",
                    campaign_id=message.campaign_id,
                )
                return {
                    "success": False,
                    "message_id": message_id,
                    "error": "Campaign not found",
                }
            
            # Don't send if campaign is paused or cancelled
            if campaign.status in [CampaignStatus.PAUSED, CampaignStatus.CANCELLED]:
                logger.info(
                    "Campaign not active, skipping message",
                    campaign_id=campaign.id,
                    status=campaign.status,
                    message_id=message_id,
                )
                return {
                    "success": False,
                    "message_id": message_id,
                    "error": f"Campaign is {campaign.status}",
                }
            
            # Update message status to SENDING
            await message_repo.update_status(message_id, MessageStatus.SENDING)
            
            # Prepare template variables
            template_variables = message.template_variables or {}
            parameters = list(template_variables.values()) if template_variables else None
            
            # Format phone number
            formatted_phone = whatsapp_service.format_phone_number(message.recipient_phone)
            
            # Send message via WhatsApp API
            try:
                response = await whatsapp_service.send_template_message(
                    to=formatted_phone,
                    template_name=campaign.template_name,
                    language=campaign.template_language,
                    parameters=parameters,
                )
                
                # Extract WhatsApp message ID from response
                whatsapp_message_id = None
                if "messages" in response and len(response["messages"]) > 0:
                    whatsapp_message_id = response["messages"][0].get("id")
                
                # Update message status to SENT
                await message_repo.update_status(
                    message_id,
                    MessageStatus.SENT,
                    whatsapp_message_id=whatsapp_message_id,
                )
                
                # Update campaign counters
                await campaign_repo.update_counters(
                    campaign.id,
                    messages_sent=1,
                )
                
                await session.commit()
                
                logger.info(
                    "Message sent successfully",
                    message_id=message_id,
                    whatsapp_message_id=whatsapp_message_id,
                )
                
                # Publish notification
                try:
                    from app.services.notification_service import get_notification_service
                    notification_service = get_notification_service()
                    await notification_service.publish_message_update(
                        campaign.id,
                        message_id,
                        "message_sent",
                        {
                            "status": "sent",
                            "whatsapp_message_id": whatsapp_message_id,
                        },
                    )
                except Exception as notify_error:
                    logger.warning(
                        "Failed to publish message notification",
                        message_id=message_id,
                        error=str(notify_error),
                    )
                
                return {
                    "success": True,
                    "message_id": message_id,
                    "whatsapp_message_id": whatsapp_message_id,
                }
                
            except ExternalServiceError as e:
                # Update message status to FAILED
                await message_repo.update_status(
                    message_id,
                    MessageStatus.FAILED,
                    error_message=str(e),
                    error_code=e.code,
                )
                
                # Update campaign counters
                await campaign_repo.update_counters(
                    campaign.id,
                    messages_failed=1,
                )
                
                await session.commit()
                
                logger.error(
                    "Failed to send message",
                    message_id=message_id,
                    error=str(e),
                )
                
                # Publish notification
                try:
                    from app.services.notification_service import get_notification_service
                    notification_service = get_notification_service()
                    await notification_service.publish_message_update(
                        campaign.id,
                        message_id,
                        "message_failed",
                        {
                            "status": "failed",
                            "error": str(e),
                            "error_code": e.code,
                        },
                    )
                except Exception as notify_error:
                    logger.warning(
                        "Failed to publish message notification",
                        message_id=message_id,
                        error=str(notify_error),
                    )
                
                return {
                    "success": False,
                    "message_id": message_id,
                    "error": str(e),
                }
                
        except Exception as e:
            await session.rollback()
            logger.error(
                "Unexpected error sending message",
                message_id=message_id,
                error=str(e),
                exc_info=True,
            )
            raise


def process_message_batch_task(campaign_id: int, batch_size: int = 50) -> Dict[str, Any]:
    """
    Process a batch of pending messages for a campaign.
    
    Args:
        campaign_id: Campaign ID
        batch_size: Number of messages to process in this batch
        
    Returns:
        Dictionary with batch processing result
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_message_batch_async(campaign_id, batch_size))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(
            "Error in process_message_batch_task",
            campaign_id=campaign_id,
            error=str(e),
            exc_info=True,
        )
        return {
            "success": False,
            "campaign_id": campaign_id,
            "error": str(e),
        }


async def _process_message_batch_async(
    campaign_id: int,
    batch_size: int = 50,
) -> Dict[str, Any]:
    """
    Process a batch of pending messages.
    
    Args:
        campaign_id: Campaign ID
        batch_size: Number of messages to process
        
    Returns:
        Dictionary with batch result
    """
    async with AsyncSessionLocal() as session:
        try:
            message_repo = MessageRepository(session)
            campaign_repo = CampaignRepository(session)
            
            # Get campaign
            campaign = await campaign_repo.get(campaign_id)
            if not campaign:
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": "Campaign not found",
                }
            
            # Check if campaign is still running
            if campaign.status != CampaignStatus.RUNNING:
                logger.info(
                    "Campaign not running, skipping batch",
                    campaign_id=campaign_id,
                    status=campaign.status,
                )
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": f"Campaign is {campaign.status}",
                }
            
            # Get pending messages
            pending_messages = await message_repo.get_pending(
                campaign_id,
                limit=batch_size,
            )
            
            if not pending_messages:
                # No more pending messages, check if campaign is complete
                total_pending = await message_repo.count_by_status(
                    campaign_id,
                    MessageStatus.PENDING,
                )
                
                if total_pending == 0:
                    # All messages processed, update campaign status
                    await campaign_repo.update_status(
                        campaign_id,
                        CampaignStatus.COMPLETED,
                    )
                    await session.commit()
                    
                    logger.info(
                        "Campaign completed",
                        campaign_id=campaign_id,
                    )
                
                return {
                    "success": True,
                    "campaign_id": campaign_id,
                    "messages_processed": 0,
                    "campaign_completed": total_pending == 0,
                }
            
            # Process messages (enqueue individual send tasks)
            from app.core.redis import get_message_queue
            
            message_queue = get_message_queue()
            enqueued_count = 0
            
            for message in pending_messages:
                # Update status to QUEUED
                await message_repo.update_status(message.id, MessageStatus.QUEUED)
                
                # Enqueue send task
                job = message_queue.enqueue(
                    send_message_task,
                    message.id,
                    job_timeout=300,  # 5 minutes timeout
                )
                
                enqueued_count += 1
                
                logger.debug(
                    "Message enqueued",
                    message_id=message.id,
                    job_id=job.id,
                )
            
            await session.commit()
            
            logger.info(
                "Message batch processed",
                campaign_id=campaign_id,
                messages_enqueued=enqueued_count,
            )
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "messages_processed": enqueued_count,
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(
                "Error processing message batch",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )
            raise

