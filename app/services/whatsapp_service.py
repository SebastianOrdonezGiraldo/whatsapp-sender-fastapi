"""WhatsApp Business API service."""

import httpx
from typing import Optional, Dict, Any, List

from app.core.config import get_settings
from app. core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.services.template_service import TemplateService

settings = get_settings()
logger = get_logger(__name__)


class WhatsAppService:
    """Service for sending messages via WhatsApp Business API."""

    def __init__(self):
        """Initialize WhatsApp service."""
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = settings.whatsapp_access_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.template_service = TemplateService()

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language:  str = "es",
        parameters: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send a template message to a recipient."""
        # Validate parameters
        if parameters:
            await self.template_service.validate_template_parameters(
                template_name,
                language,
                parameters,
            )

        # Build template payload
        template_payload = self.template_service.build_template_payload(
            template_name,
            language,
            parameters or [],
        )

        # Build message payload
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template_payload,
        }

        url = f"{self.base_url}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )
                response. raise_for_status()

                data = response.json()

                logger.info(
                    "WhatsApp message sent",
                    to=to,
                    template=template_name,
                )

                return data

        except httpx.HTTPError as e:
            logger.error("Failed to send WhatsApp message", error=str(e))
            raise ExternalServiceError(
                "Failed to send WhatsApp message",
                service_name="Meta WhatsApp API",
            )

    def format_phone_number(self, phone:  str) -> str:
        """Format phone number for WhatsApp API."""
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        if not cleaned. startswith('+'):
            cleaned = f'+57{cleaned}'

        return cleaned