"""Campaign service with business logic."""

from typing import List, Optional
from datetime import datetime

from app.repositories.campaign_repository import CampaignRepository
from app.repositories.message_repository import MessageRepository
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.models.campaign import Campaign
from app.utils.enums import CampaignStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.services.notification_service import get_notification_service
from app.services.template_service import TemplateService

logger = get_logger(__name__)


class CampaignService:
    """
    Service for campaign business logic.

    This service orchestrates campaign operations using repositories.
    It implements business rules and validation.
    """

    def __init__(
            self,
            campaign_repo: CampaignRepository,
            message_repo: MessageRepository,
    ):
        """
        Initialize campaign service.

        Args:
            campaign_repo:  Campaign repository
            message_repo: Message repository
        """
        self.campaign_repo = campaign_repo
        self.message_repo = message_repo

    async def create_campaign(self, campaign_in: CampaignCreate) -> Campaign:
        """
        Create a new campaign.

        Args:
            campaign_in: Campaign creation data

        Returns:
            Created campaign

        Raises:
            ValidationError: If validation fails
        """
        logger.info("Creating new campaign", name=campaign_in.name)

        # Validate scheduled_at if provided
        if campaign_in.scheduled_at and campaign_in.scheduled_at < datetime.utcnow():
            raise ValidationError("Scheduled time must be in the future")

        # Validate template exists and is approved in Meta
        try:
            template_service = TemplateService()
            template = await template_service.get_template_by_name(
                campaign_in.template_name,
                campaign_in.template_language or "es",
            )
            logger.info(
                "Template validated",
                template_name=template.name,
                template_id=template.id,
                status=template.status,
            )
        except NotFoundError as e:
            raise ValidationError(
                f"Template '{campaign_in.template_name}' with language "
                f"'{campaign_in.template_language or 'es'}' not found or not approved in Meta. "
                f"Please ensure the template exists and is APPROVED in your WhatsApp Business Account."
            ) from e
        except Exception as e:
            logger.warning(
                "Error validating template (continuing anyway)",
                template_name=campaign_in.template_name,
                error=str(e),
            )
            # Don't fail campaign creation if template validation fails
            # The error will be caught when trying to send messages

        # Prepare campaign data
        campaign_data = campaign_in.model_dump()
        campaign_data["status"] = CampaignStatus.DRAFT
        campaign_data["total_recipients"] = 0
        campaign_data["messages_sent"] = 0
        campaign_data["messages_delivered"] = 0
        campaign_data["messages_failed"] = 0
        campaign_data["messages_read"] = 0
        campaign_data["estimated_cost"] = 0.0
        campaign_data["actual_cost"] = 0.0

        campaign = await self.campaign_repo.create(obj_in=campaign_data)

        logger.info(
            "Campaign created successfully",
            campaign_id=campaign.id,
            name=campaign.name,
        )

        return campaign

    async def get_campaign(self, campaign_id: int) -> Campaign:
        """
        Get campaign by ID.

        Args:
            campaign_id: Campaign ID

        Returns:
            Campaign instance

        Raises:
            NotFoundError:  If campaign not found
        """
        campaign = await self.campaign_repo.get(campaign_id)

        if not campaign:
            raise NotFoundError(f"Campaign with id {campaign_id} not found")

        return campaign

    async def get_campaigns(
            self,
            skip: int = 0,
            limit: int = 100,
    ) -> List[Campaign]:
        """
        Get list of campaigns.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of campaigns
        """
        return await self.campaign_repo.get_multi(
            skip=skip,
            limit=limit,
            order_by="created_at",
        )

    async def get_campaigns_by_status(
            self,
            status: CampaignStatus,
            skip: int = 0,
            limit: int = 100,
    ) -> List[Campaign]:
        """
        Get campaigns by status.

        Args:
            status: Campaign status
            skip: Number of records to skip
            limit:  Maximum number of records

        Returns:
            List of campaigns
        """
        return await self.campaign_repo.get_by_status(
            status,
            skip=skip,
            limit=limit,
        )

    async def update_campaign(
            self,
            campaign_id: int,
            campaign_in: CampaignUpdate,
    ) -> Campaign:
        """
        Update campaign.

        Args:
            campaign_id: Campaign ID
            campaign_in: Campaign update data

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If campaign cannot be updated
        """
        campaign = await self.get_campaign(campaign_id)

        # Validate:  can only update campaigns in DRAFT status
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValidationError(
                f"Cannot update campaign in {campaign.status} status"
            )

        # Prepare update data (exclude None values)
        update_data = campaign_in.model_dump(exclude_unset=True)

        # Validate scheduled_at if being updated
        if "scheduled_at" in update_data and update_data["scheduled_at"]:
            if update_data["scheduled_at"] < datetime.utcnow():
                raise ValidationError("Scheduled time must be in the future")

        # Validate template if being updated
        if "template_name" in update_data:
            template_name = update_data.get("template_name")
            template_language = update_data.get("template_language", campaign.template_language or "es")
            
            try:
                template_service = TemplateService()
                template = await template_service.get_template_by_name(
                    template_name,
                    template_language,
                )
                logger.info(
                    "Template validated on update",
                    template_name=template.name,
                    template_id=template.id,
                    status=template.status,
                )
            except NotFoundError as e:
                raise ValidationError(
                    f"Template '{template_name}' with language '{template_language}' "
                    f"not found or not approved in Meta. Please ensure the template exists "
                    f"and is APPROVED in your WhatsApp Business Account."
                ) from e
            except Exception as e:
                logger.warning(
                    "Error validating template on update (continuing anyway)",
                    template_name=template_name,
                    error=str(e),
                )

        updated_campaign = await self.campaign_repo.update(
            db_obj=campaign,
            obj_in=update_data,
        )

        logger.info("Campaign updated", campaign_id=campaign_id)

        return updated_campaign

    async def delete_campaign(self, campaign_id: int) -> bool:
        """
        Delete campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            True if deleted

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If campaign cannot be deleted
        """
        campaign = await self.get_campaign(campaign_id)

        # Validate: can only delete campaigns in DRAFT status
        if campaign.status != CampaignStatus.DRAFT:
            raise ValidationError(
                f"Cannot delete campaign in {campaign.status} status"
            )

        deleted = await self.campaign_repo.delete(id=campaign_id)

        if deleted:
            logger.info("Campaign deleted", campaign_id=campaign_id)

        return deleted

    async def start_campaign(self, campaign_id: int) -> Campaign:
        """
        Start a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If campaign cannot be started
        """
        campaign = await self.get_campaign(campaign_id)

        # Validate: can only start DRAFT or SCHEDULED campaigns
        if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
            raise ValidationError(
                f"Cannot start campaign in {campaign.status} status"
            )

        # Validate: must have recipients
        if campaign.total_recipients == 0:
            raise ValidationError("Cannot start campaign without recipients")

        # Update status to RUNNING
        updated_campaign = await self.campaign_repo.update_status(
            campaign_id,
            CampaignStatus.RUNNING,
        )

        logger.info(
            "Campaign started",
            campaign_id=campaign_id,
            total_recipients=campaign.total_recipients,
        )

        # Enqueue job to process messages
        await self._enqueue_campaign_job(campaign_id)

        # Publish notification
        await self._publish_campaign_update(
            campaign_id,
            "status_changed",
            {"status": CampaignStatus.RUNNING, "started_at": updated_campaign.started_at},
        )

        return updated_campaign

    async def pause_campaign(self, campaign_id: int) -> Campaign:
        """
        Pause a running campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
            ValidationError:  If campaign cannot be paused
        """
        campaign = await self.get_campaign(campaign_id)

        # Validate:  can only pause RUNNING campaigns
        if campaign.status != CampaignStatus.RUNNING:
            raise ValidationError(
                f"Cannot pause campaign in {campaign.status} status"
            )

        updated_campaign = await self.campaign_repo.update_status(
            campaign_id,
            CampaignStatus.PAUSED,
        )

        logger.info("Campaign paused", campaign_id=campaign_id)

        # Publish notification
        await self._publish_campaign_update(
            campaign_id,
            "status_changed",
            {"status": CampaignStatus.PAUSED},
        )

        return updated_campaign

    async def resume_campaign(self, campaign_id: int) -> Campaign:
        """
        Resume a paused campaign.

        Args:
            campaign_id:  Campaign ID

        Returns:
            Updated campaign

        Raises:
            NotFoundError: If campaign not found
            ValidationError: If campaign cannot be resumed
        """
        campaign = await self.get_campaign(campaign_id)

        # Validate: can only resume PAUSED campaigns
        if campaign.status != CampaignStatus.PAUSED:
            raise ValidationError(
                f"Cannot resume campaign in {campaign.status} status"
            )

        updated_campaign = await self.campaign_repo.update_status(
            campaign_id,
            CampaignStatus.RUNNING,
        )

        logger.info("Campaign resumed", campaign_id=campaign_id)

        # Re-enqueue job to continue processing
        await self._enqueue_campaign_job(campaign_id)

        # Publish notification
        await self._publish_campaign_update(
            campaign_id,
            "status_changed",
            {"status": CampaignStatus.RUNNING},
        )

        return updated_campaign

    async def cancel_campaign(self, campaign_id: int) -> Campaign:
        """
        Cancel a campaign.

        Args:
            campaign_id: Campaign ID

        Returns:
            Updated campaign

        Raises:
            NotFoundError:  If campaign not found
            ValidationError: If campaign cannot be cancelled
        """
        campaign = await self.get_campaign(campaign_id)

        # Validate:  can only cancel active campaigns
        if campaign.status not in [
            CampaignStatus.SCHEDULED,
            CampaignStatus.RUNNING,
            CampaignStatus.PAUSED,
        ]:
            raise ValidationError(
                f"Cannot cancel campaign in {campaign.status} status"
            )

        updated_campaign = await self.campaign_repo.update_status(
            campaign_id,
            CampaignStatus.CANCELLED,
        )

        logger.info("Campaign cancelled", campaign_id=campaign_id)

        # Publish notification
        await self._publish_campaign_update(
            campaign_id,
            "status_changed",
            {"status": CampaignStatus.CANCELLED},
        )

        return updated_campaign

    async def get_campaign_stats(self, campaign_id: int) -> dict:
        """
        Get campaign statistics.

        Args:
            campaign_id: Campaign ID

        Returns:
            Dictionary with campaign statistics

        Raises:
            NotFoundError: If campaign not found
        """
        stats = await self.campaign_repo.get_stats(campaign_id)

        if not stats:
            raise NotFoundError(f"Campaign with id {campaign_id} not found")

        return stats

    async def count_campaigns(self) -> int:
        """
        Count total campaigns.

        Returns:
            Total number of campaigns
        """
        return await self.campaign_repo.count()

    async def _enqueue_campaign_job(self, campaign_id: int) -> None:
        """
        Enqueue a background job to process campaign messages.

        Args:
            campaign_id: Campaign ID
        """
        try:
            from app.core.redis import get_campaign_queue
            from app.workers.tasks.campaign_tasks import process_campaign_task
            from app.workers.handlers.campaign_handler import (
                handle_campaign_job_success,
                handle_campaign_job_failure,
            )

            campaign_queue = get_campaign_queue()
            job = campaign_queue.enqueue(
                process_campaign_task,
                campaign_id,
                job_timeout=3600,  # 1 hour timeout
                on_success=handle_campaign_job_success,
                on_failure=handle_campaign_job_failure,
            )

            logger.info(
                "Campaign processing job enqueued",
                campaign_id=campaign_id,
                job_id=job.id,
            )
        except Exception as e:
            logger.error(
                "Failed to enqueue campaign job",
                campaign_id=campaign_id,
                error=str(e),
                exc_info=True,
            )
            # Don't raise - campaign is already started, job can be retried manually

    async def _publish_campaign_update(
        self,
        campaign_id: int,
        event_type: str,
        data: dict,
    ) -> None:
        """
        Publish campaign update notification.

        Args:
            campaign_id: Campaign ID
            event_type: Event type
            data: Event data
        """
        try:
            notification_service = get_notification_service()
            await notification_service.publish_campaign_update(
                campaign_id,
                event_type,
                data,
            )
        except Exception as e:
            logger.warning(
                "Failed to publish campaign update",
                campaign_id=campaign_id,
                error=str(e),
            )
            # Don't raise - notification failure shouldn't break the operation