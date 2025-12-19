"""WhatsApp Business API service."""

import httpx
from typing import Optional, Dict, Any

from app.core.config import get_settings
from app.core.exceptions import ExternalServiceError
from app.core.logging import get_logger
from app.services.template_service import TemplateService

settings = get_settings()
logger = get_logger(__name__)


class WhatsAppService:
    """
    Service for sending messages via WhatsApp Business API.

    This service handles sending template messages to recipients.
    """

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
            language: str = "es",
            parameters: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a template message to a recipient.

        Args:
            to:  Recipient phone number with country code (e.g., +573001234567)
            template_name:  Name of the approved template
            language: Template language code
            parameters: List of parameter values for template variables

        Returns:
            Response from WhatsApp API with message ID

        Raises:
            ExternalServiceError: If sending fails
        """
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
                response.raise_for_status()

                data = response.json()

                logger.info(
                    "WhatsApp message sent",
                    to=to,
                    template=template_name,
                    message_id=data.get("messages", [{}])[0].get("id"),
                )

                return data

        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response.text else {}
            error_message = error_data.get("error", {}).get("message", str(e))

            logger.error(
                "Failed to send WhatsApp message",
                to=to,
                template=template_name,
                status_code=e.response.status_code,
                error=error_message,
            )

            raise ExternalServiceError(
                f"Failed to send WhatsApp message: {error_message}",
                service_name="Meta WhatsApp API",
            )
        except httpx.HTTPError as e:
            logger.error("Network error sending message", error=str(e))
            raise ExternalServiceError(
                "Network error connecting to WhatsApp API",
                service_name="Meta WhatsApp API",
            )

    def format_phone_number(self, phone: str) -> str:
        """
        Format phone number for WhatsApp API.

        Args:
            phone: Phone number (can be with or without +)

        Returns:
            Formatted phone number with country code
        """
        # Remove all non-numeric characters except +
        cleaned = ''.join(c for c in phone if c.isdigit() or c == '+')

        # Ensure it starts with +
        if not cleaned.startswith('+'):
            # Assume Colombian number if no country code
            cleaned = f'+57{cleaned}'

        return cleaned