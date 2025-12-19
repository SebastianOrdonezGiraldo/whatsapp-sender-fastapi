"""Background tasks for processing campaigns."""

import asyncio
from typing import Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import get_settings
from app.core.logging import get_logger
from app.repositories.campaign_repository import CampaignRepository
from app.repositories.message_repository import MessageRepository
from app.utils.enums import CampaignStatus
from app.workers.tasks.message_tasks import process_message_batch_task

settings = get_settings()
logger = get_logger(__name__)


def process_campaign_task(campaign_id: int) -> Dict[str, Any]:
    """
    Process a campaign by sending messages in batches.
    
    This is the main task that orchestrates the campaign processing.
    It processes messages in batches with delays between batches.
    
    Args:
        campaign_id: Campaign ID to process
        
    Returns:
        Dictionary with task result
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_campaign_async(campaign_id))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(
            "Error in process_campaign_task",
            campaign_id=campaign_id,
            error=str(e),
            exc_info=True,
        )
        return {
            "success": False,
            "campaign_id": campaign_id,
            "error": str(e),
        }


async def _process_campaign_async(campaign_id: int) -> Dict[str, Any]:
    """
    Async function to process a campaign.
    
    Args:
        campaign_id: Campaign ID to process
        
    Returns:
        Dictionary with result
    """
    async with AsyncSessionLocal() as session:
        try:
            campaign_repo = CampaignRepository(session)
            
            # Get campaign
            campaign = await campaign_repo.get(campaign_id)
            if not campaign:
                logger.warning("Campaign not found", campaign_id=campaign_id)
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": "Campaign not found",
                }
            
            # Check if campaign should be processed
            if campaign.status != CampaignStatus.RUNNING:
                logger.info(
                    "Campaign not running, skipping",
                    campaign_id=campaign_id,
                    status=campaign.status,
                )
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": f"Campaign is {campaign.status}",
                }
            
            logger.info(
                "Starting campaign processing",
                campaign_id=campaign_id,
                batch_size=campaign.batch_size,
                delay=campaign.delay_between_messages,
            )
            
            # Process messages in batches
            batch_size = campaign.batch_size or settings.campaign_batch_size
            delay_between_batches = (
                campaign.delay_between_messages * batch_size
                if campaign.delay_between_messages
                else settings.campaign_delay_between_batches
            )
            
            total_processed = 0
            batch_number = 0
            
            while True:
                # Check campaign status before each batch
                await session.refresh(campaign)
                if campaign.status != CampaignStatus.RUNNING:
                    logger.info(
                        "Campaign status changed, stopping processing",
                        campaign_id=campaign_id,
                        status=campaign.status,
                    )
                    break
                
                # Process batch
                batch_result = process_message_batch_task(campaign_id, batch_size)
                
                if not batch_result.get("success"):
                    logger.warning(
                        "Batch processing failed",
                        campaign_id=campaign_id,
                        error=batch_result.get("error"),
                    )
                    break
                
                messages_processed = batch_result.get("messages_processed", 0)
                total_processed += messages_processed
                batch_number += 1
                
                # Check if campaign is completed
                if batch_result.get("campaign_completed"):
                    logger.info(
                        "Campaign processing completed",
                        campaign_id=campaign_id,
                        total_batches=batch_number,
                        total_messages=total_processed,
                    )
                    break
                
                # If no messages were processed, wait a bit and check again
                if messages_processed == 0:
                    logger.debug(
                        "No messages to process, waiting",
                        campaign_id=campaign_id,
                    )
                    await asyncio.sleep(5)
                    continue
                
                # Wait before next batch (if not last batch)
                if messages_processed == batch_size:
                    logger.info(
                        "Batch processed, waiting before next batch",
                        campaign_id=campaign_id,
                        batch_number=batch_number,
                        delay=delay_between_batches,
                    )
                    await asyncio.sleep(delay_between_batches)
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "total_batches": batch_number,
                "total_messages_processed": total_processed,
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(
                "Error processing campaign",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )
            
            # Update campaign status to FAILED
            try:
                await campaign_repo.update_status(
                    campaign_id,
                    CampaignStatus.FAILED,
                )
                await session.commit()
            except Exception as update_error:
                logger.error(
                    "Failed to update campaign status",
                    campaign_id=campaign_id,
                    error=str(update_error),
                )
            
            raise


def schedule_campaign_task(campaign_id: int) -> Dict[str, Any]:
    """
    Schedule a campaign to start at its scheduled time.
    
    This task checks if a scheduled campaign is ready to start.
    
    Args:
        campaign_id: Campaign ID to check
        
    Returns:
        Dictionary with result
    """
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_schedule_campaign_async(campaign_id))
            return result
        finally:
            loop.close()
    except Exception as e:
        logger.error(
            "Error in schedule_campaign_task",
            campaign_id=campaign_id,
            error=str(e),
            exc_info=True,
        )
        return {
            "success": False,
            "campaign_id": campaign_id,
            "error": str(e),
        }


async def _schedule_campaign_async(campaign_id: int) -> Dict[str, Any]:
    """
    Check if a scheduled campaign is ready to start.
    
    Args:
        campaign_id: Campaign ID to check
        
    Returns:
        Dictionary with result
    """
    async with AsyncSessionLocal() as session:
        try:
            campaign_repo = CampaignRepository(session)
            
            campaign = await campaign_repo.get(campaign_id)
            if not campaign:
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": "Campaign not found",
                }
            
            # Check if campaign is scheduled and ready
            if campaign.status != CampaignStatus.SCHEDULED:
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": f"Campaign is not scheduled (status: {campaign.status})",
                }
            
            if not campaign.scheduled_at:
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": "Campaign has no scheduled time",
                }
            
            # Check if it's time to start
            now = datetime.utcnow()
            if campaign.scheduled_at > now:
                # Not ready yet
                return {
                    "success": False,
                    "campaign_id": campaign_id,
                    "error": "Campaign not ready to start yet",
                    "scheduled_at": campaign.scheduled_at.isoformat(),
                }
            
            # Start the campaign
            from app.services.campaign_service import CampaignService
            
            campaign_service = CampaignService(
                campaign_repo,
                MessageRepository(session),
            )
            
            updated_campaign = await campaign_service.start_campaign(campaign_id)
            await session.commit()
            
            logger.info(
                "Scheduled campaign started",
                campaign_id=campaign_id,
            )
            
            # Enqueue processing task
            from app.core.redis import get_campaign_queue
            
            campaign_queue = get_campaign_queue()
            job = campaign_queue.enqueue(
                process_campaign_task,
                campaign_id,
                job_timeout=3600,  # 1 hour timeout
            )
            
            logger.info(
                "Campaign processing task enqueued",
                campaign_id=campaign_id,
                job_id=job.id,
            )
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "job_id": job.id,
            }
            
        except Exception as e:
            await session.rollback()
            logger.error(
                "Error scheduling campaign",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )
            raise

