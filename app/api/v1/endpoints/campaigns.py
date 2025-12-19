"""Campaign endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status, Query, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignStatsResponse,
)
from app.schemas.base import ResponseSchema
from app.schemas.csv_schema import CSVUploadResponse
from app.services.campaign_service import CampaignService
from app.services.csv_service import get_csv_service, CSVService
from app.core.dependencies import get_campaign_service, get_db
from app.core.logging import get_logger
from app.core.exceptions import ValidationError, NotFoundError
from app.repositories.message_repository import MessageRepository
from app.repositories.campaign_repository import CampaignRepository
from app.models.message import Message
from app.utils.enums import MessageStatus, CampaignStatus
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


@router.post(
    "",
    response_model=ResponseSchema[CampaignResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new campaign",
    description="Create a new WhatsApp campaign in DRAFT status",
)
async def create_campaign(
    campaign_in: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Create a new campaign.

    Args:
        campaign_in: Campaign creation data
        service: Campaign service (injected)

    Returns:
        Created campaign
    """
    logger.info("API:  Creating campaign", name=campaign_in.name)

    campaign = await service.create_campaign(campaign_in)

    return ResponseSchema(
        success=True,
        message="Campaign created successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.get(
    "",
    response_model=ResponseSchema[CampaignListResponse],
    summary="List campaigns",
    description="Get a paginated list of campaigns",
)
async def list_campaigns(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    service: CampaignService = Depends(get_campaign_service),
):
    """
    List campaigns with pagination.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        service: Campaign service (injected)

    Returns:
        List of campaigns with metadata
    """
    logger.info("API: Listing campaigns", skip=skip, limit=limit)

    campaigns = await service. get_campaigns(skip=skip, limit=limit)
    total = await service.count_campaigns()

    return ResponseSchema(
        success=True,
        message="Campaigns retrieved successfully",
        data=CampaignListResponse(
            campaigns=[CampaignResponse.model_validate(c) for c in campaigns],
            total=total,
            skip=skip,
            limit=limit,
        ),
    )


@router.get(
    "/{campaign_id}",
    response_model=ResponseSchema[CampaignResponse],
    summary="Get campaign by ID",
    description="Get detailed information about a specific campaign",
)
async def get_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Get campaign by ID.

    Args:
        campaign_id: Campaign ID
        service: Campaign service (injected)

    Returns:
        Campaign details

    Raises:
        NotFoundError: If campaign not found
    """
    logger.info("API: Getting campaign", campaign_id=campaign_id)

    campaign = await service. get_campaign(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign retrieved successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.put(
    "/{campaign_id}",
    response_model=ResponseSchema[CampaignResponse],
    summary="Update campaign",
    description="Update campaign details (only DRAFT or SCHEDULED campaigns)",
)
async def update_campaign(
    campaign_id: int,
    campaign_in: CampaignUpdate,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Update campaign.

    Args:
        campaign_id:  Campaign ID
        campaign_in:  Campaign update data
        service: Campaign service (injected)

    Returns:
        Updated campaign

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot be updated
    """
    logger.info("API: Updating campaign", campaign_id=campaign_id)

    campaign = await service.update_campaign(campaign_id, campaign_in)

    return ResponseSchema(
        success=True,
        message="Campaign updated successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.delete(
    "/{campaign_id}",
    response_model=ResponseSchema[None],
    status_code=status.HTTP_200_OK,
    summary="Delete campaign",
    description="Delete a campaign (only DRAFT campaigns)",
)
async def delete_campaign(
    campaign_id:  int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Delete campaign.

    Args:
        campaign_id: Campaign ID
        service: Campaign service (injected)

    Returns:
        Success message

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot be deleted
    """
    logger.info("API: Deleting campaign", campaign_id=campaign_id)

    await service.delete_campaign(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign deleted successfully",
        data=None,
    )


@router.post(
    "/{campaign_id}/start",
    response_model=ResponseSchema[CampaignResponse],
    summary="Start campaign",
    description="Start sending messages for a campaign",
)
async def start_campaign(
    campaign_id:  int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Start campaign execution.

    Args:
        campaign_id: Campaign ID
        service: Campaign service (injected)

    Returns:
        Updated campaign with RUNNING status

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot be started
    """
    logger.info("API: Starting campaign", campaign_id=campaign_id)

    campaign = await service.start_campaign(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign started successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.post(
    "/{campaign_id}/pause",
    response_model=ResponseSchema[CampaignResponse],
    summary="Pause campaign",
    description="Pause a running campaign",
)
async def pause_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Pause campaign execution.

    Args:
        campaign_id: Campaign ID
        service: Campaign service (injected)

    Returns:
        Updated campaign with PAUSED status

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot be paused
    """
    logger.info("API:  Pausing campaign", campaign_id=campaign_id)

    campaign = await service.pause_campaign(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign paused successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.post(
    "/{campaign_id}/resume",
    response_model=ResponseSchema[CampaignResponse],
    summary="Resume campaign",
    description="Resume a paused campaign",
)
async def resume_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Resume campaign execution.

    Args:
        campaign_id: Campaign ID
        service: Campaign service (injected)

    Returns:
        Updated campaign with RUNNING status

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot be resumed
    """
    logger.info("API: Resuming campaign", campaign_id=campaign_id)

    campaign = await service.resume_campaign(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign resumed successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.post(
    "/{campaign_id}/cancel",
    response_model=ResponseSchema[CampaignResponse],
    summary="Cancel campaign",
    description="Cancel a campaign",
)
async def cancel_campaign(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Cancel campaign execution.

    Args:
        campaign_id: Campaign ID
        service: Campaign service (injected)

    Returns:
        Updated campaign with CANCELLED status

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot be cancelled
    """
    logger.info("API: Cancelling campaign", campaign_id=campaign_id)

    campaign = await service.cancel_campaign(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign cancelled successfully",
        data=CampaignResponse.model_validate(campaign),
    )


@router.get(
    "/{campaign_id}/stats",
    response_model=ResponseSchema[CampaignStatsResponse],
    summary="Get campaign statistics",
    description="Get detailed statistics for a campaign",
)
async def get_campaign_stats(
    campaign_id: int,
    service: CampaignService = Depends(get_campaign_service),
):
    """
    Get campaign statistics.

    Args:
        campaign_id: Campaign ID
        service:  Campaign service (injected)

    Returns:
        Campaign statistics

    Raises:
        NotFoundError: If campaign not found
    """
    logger. info("API: Getting campaign stats", campaign_id=campaign_id)

    stats = await service.get_campaign_stats(campaign_id)

    return ResponseSchema(
        success=True,
        message="Campaign statistics retrieved successfully",
        data=CampaignStatsResponse(**stats),
    )


@router.post(
    "/{campaign_id}/upload-recipients",
    response_model=ResponseSchema[CSVUploadResponse],
    status_code=status.HTTP_200_OK,
    summary="Upload CSV with recipients",
    description="Upload a CSV file with campaign recipients and create messages",
)
async def upload_recipients_csv(
    campaign_id: int,
    file: UploadFile = File(..., description="CSV file with recipients"),
    service: CampaignService = Depends(get_campaign_service),
    csv_service: CSVService = Depends(get_csv_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload CSV file with recipients and create messages for the campaign.

    CSV format:
    - Required column: "Recipient-Phone-Number"
    - Optional columns: Any other columns will be used as template variables

    Args:
        campaign_id: Campaign ID
        file: CSV file upload
        service: Campaign service (injected)
        csv_service: CSV service (injected)
        db: Database session (injected)

    Returns:
        CSV upload response with validation results

    Raises:
        NotFoundError: If campaign not found
        ValidationError: If campaign cannot accept recipients
    """
    logger.info("API: Uploading recipients CSV", campaign_id=campaign_id, filename=file.filename)

    # Verify campaign exists and can accept recipients
    campaign = await service.get_campaign(campaign_id)

    if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
        raise ValidationError(
            f"Cannot upload recipients to campaign in {campaign.status} status"
        )

    # Validate file type
    if not file.filename or not file.filename.endswith(".csv"):
        raise ValidationError("File must be a CSV file")

    try:
        # Read file content
        file_content = await file.read()

        # Save file
        saved_path = csv_service.save_uploaded_file(file_content, file.filename)

        # Validate CSV
        validation_result = csv_service.validate_csv_file(saved_path)

        if validation_result.valid_rows == 0:
            # No valid rows, delete file and return error
            csv_service.delete_file(saved_path)
            raise ValidationError(
                "No valid recipients found in CSV file",
                details={"errors": validation_result.errors},
            )

        # Parse recipients
        recipients = csv_service.parse_csv_recipients(saved_path)

        # Create messages
        message_repo = MessageRepository(db)
        campaign_repo = CampaignRepository(db)

        messages_data = []
        for recipient in recipients:
            messages_data.append({
                "campaign_id": campaign_id,
                "recipient_phone": recipient.phone,
                "recipient_name": recipient.variables.get("name"),
                "template_variables": recipient.variables,
                "status": MessageStatus.PENDING,
            })

        # Bulk create messages
        created_messages = await message_repo.bulk_create(messages_data)

        # Update campaign with recipient count and file path
        update_data = {
            "total_recipients": len(created_messages),
            "csv_file_path": saved_path,
        }

        # Calculate estimated cost
        cost_per_message = settings.cost_per_message
        update_data["estimated_cost"] = len(created_messages) * cost_per_message

        await campaign_repo.update(campaign, update_data)
        await db.commit()

        logger.info(
            "Recipients uploaded successfully",
            campaign_id=campaign_id,
            total_recipients=len(created_messages),
            valid_rows=validation_result.valid_rows,
            invalid_rows=validation_result.invalid_rows,
        )

        # Publish notification
        from app.services.notification_service import get_notification_service
        notification_service = get_notification_service()
        await notification_service.publish_campaign_update(
            campaign_id,
            "recipients_uploaded",
            {
                "total_recipients": len(created_messages),
                "valid_rows": validation_result.valid_rows,
                "invalid_rows": validation_result.invalid_rows,
            },
        )

        return ResponseSchema(
            success=True,
            message="Recipients uploaded successfully",
            data=CSVUploadResponse(
                filename=validation_result.filename,
                total_rows=validation_result.total_rows,
                valid_rows=validation_result.valid_rows,
                invalid_rows=validation_result.invalid_rows,
                errors=validation_result.errors,
                file_path=saved_path,
            ),
        )

    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Error uploading recipients CSV",
            campaign_id=campaign_id,
            error=str(e),
            exc_info=True,
        )
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV file: {str(e)}",
        )