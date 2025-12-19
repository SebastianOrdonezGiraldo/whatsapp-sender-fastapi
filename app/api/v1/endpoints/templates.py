"""Template endpoints."""

from fastapi import APIRouter, Query

from app.schemas.template import (
    TemplateParsed,
    TemplateListResponse,
    SendTemplateRequest,
)
from app.schemas.base import ResponseSchema
from app.services.template_service import TemplateService
from app.services.whatsapp_service import WhatsAppService
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get(
    "",
    response_model=ResponseSchema[TemplateListResponse],
    summary="Get WhatsApp templates",
    description="Fetch all approved WhatsApp message templates from Meta API",
)
async def list_templates():
    """
    Get all approved WhatsApp templates.

    This endpoint fetches templates from Meta's WhatsApp Business API
    and returns only APPROVED templates with parsed variable information.
    """
    logger.info("API:  Listing WhatsApp templates")

    service = TemplateService()
    templates_response = await service.get_templates()

    return ResponseSchema(
        success=True,
        message=f"Templates retrieved successfully ({templates_response.approved} approved)",
        data=templates_response,
    )


@router.get(
    "/{template_name}",
    response_model=ResponseSchema[TemplateParsed],
    summary="Get template by name",
    description="Get specific template details by name and language",
)
async def get_template(
        template_name: str,
        language: str = Query(default="es", description="Template language code"),
):
    """
    Get specific template by name.

    Args:
        template_name: Name of the template
        language: Language code (default: es)

    Returns:
        Template details with variables

    Raises:
        NotFoundError: If template not found or not approved
    """
    logger.info("API: Getting template", name=template_name, language=language)

    service = TemplateService()
    template = await service.get_template_by_name(template_name, language)

    return ResponseSchema(
        success=True,
        message="Template retrieved successfully",
        data=template,
    )


@router.post(
    "/send",
    response_model=ResponseSchema[dict],
    summary="Send template message",
    description="Send a WhatsApp template message to a recipient (for testing)",
)
async def send_template_message(request: SendTemplateRequest):
    """
    Send a template message (for testing).

    This endpoint allows testing template sending before using it in a campaign.

    Args:
        request: Template sending request with recipient and parameters

    Returns:
        WhatsApp API response with message ID
    """
    logger.info(
        "API: Sending template message",
        template=request.template_name,
        to=request.to,
    )

    service = WhatsAppService()

    # Format phone number
    formatted_phone = service.format_phone_number(request.to)

    # Send message
    response = await service.send_template_message(
        to=formatted_phone,
        template_name=request.template_name,
        language=request.template_language,
        parameters=request.parameters,
    )

    return ResponseSchema(
        success=True,
        message="Template message sent successfully",
        data=response,
    )