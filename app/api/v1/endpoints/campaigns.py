"""Campaign endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status, Query

from app.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignListResponse,
    CampaignStatsResponse,
)
from app.schemas.base import ResponseSchema
from app.services.campaign_service import CampaignService
from app.core.dependencies import get_campaign_service
from app.core.logging import get_logger

logger = get_logger(__name__)

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