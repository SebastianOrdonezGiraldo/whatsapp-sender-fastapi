"""WhatsApp Template service for Meta API integration."""

import httpx
import re
from typing import List, Optional, Dict, Any
from functools import lru_cache

from app.core.config import get_settings
from app.schemas.template import (
    TemplateResponse,
    TemplateParsed,
    TemplateListResponse,
)
from app.core.exceptions import ExternalServiceError, NotFoundError
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TemplateService:
    """
    Service for managing WhatsApp templates from Meta API.

    This service fetches and parses WhatsApp Business message templates.
    """

    def __init__(self):
        """Initialize template service."""
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = settings.whatsapp_access_token
        self.waba_id = settings.whatsapp_business_account_id

        # Validate configuration
        if not self.access_token or self.access_token == "your-token-here":
            logger.warning("WhatsApp access token not configured")

        if not self.waba_id or self.waba_id == "your-waba-id":
            logger.warning("WhatsApp Business Account ID not configured")

    async def get_templates(self) -> TemplateListResponse:
        """
        Get all templates from Meta API.

        Returns:
            TemplateListResponse with templates and statistics

        Raises:
            ExternalServiceError: If API call fails
        """
        url = f"{self.base_url}/{self.waba_id}/message_templates"

        params = {
            "access_token": self.access_token,
            "fields": "id,name,status,components,language,category",
            "limit": 100,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=30.0)
                response.raise_for_status()

                data = response.json()
                templates_data = data.get("data", [])

                # Parse and categorize templates
                templates = []
                stats = {
                    "total": len(templates_data),
                    "approved": 0,
                    "pending": 0,
                    "rejected": 0,
                }

                for template_data in templates_data:
                    status = template_data.get("status", "UNKNOWN")

                    if status == "APPROVED":
                        stats["approved"] += 1
                        parsed = self._parse_template(template_data)
                        templates.append(parsed)
                    elif status == "PENDING":
                        stats["pending"] += 1
                    elif status == "REJECTED":
                        stats["rejected"] += 1

                logger.info(
                    "Templates fetched from Meta",
                    total=stats["total"],
                    approved=stats["approved"],
                    pending=stats["pending"],
                    rejected=stats["rejected"],
                )

                return TemplateListResponse(
                    templates=templates,
                    **stats,
                )

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error fetching templates",
                status_code=e.response.status_code,
                response=e.response.text,
            )
            raise ExternalServiceError(
                f"Failed to fetch templates from WhatsApp API: {e.response.status_code}",
                service_name="Meta WhatsApp API",
            )
        except httpx.HTTPError as e:
            logger.error("Network error fetching templates", error=str(e))
            raise ExternalServiceError(
                "Network error connecting to WhatsApp API",
                service_name="Meta WhatsApp API",
            )
        except Exception as e:
            logger.exception("Unexpected error fetching templates")
            raise ExternalServiceError(
                f"Unexpected error fetching templates:  {str(e)}",
                service_name="Meta WhatsApp API",
            )

    async def get_template_by_name(
            self,
            name: str,
            language: str = "es",
    ) -> TemplateParsed:
        """
        Get specific template by name.

        Args:
            name: Template name
            language: Template language code

        Returns:
            Parsed template

        Raises:
            NotFoundError: If template not found
        """
        templates_response = await self.get_templates()

        for template in templates_response.templates:
            if template.name == name and template.language == language:
                return template

        raise NotFoundError(
            f"Template '{name}' with language '{language}' not found or not approved"
        )

    def _parse_template(self, template_data: Dict[str, Any]) -> TemplateParsed:
        """
        Parse template data and extract variables.

        Args:
            template_data: Raw template data from Meta API

        Returns:
            Parsed template with variable information
        """
        components = template_data.get("components", [])

        # Extract information from components
        body_text = None
        header_format = None
        has_buttons = False
        variables = []

        for component in components:
            comp_type = component.get("type", "")

            if comp_type == "HEADER":
                header_format = component.get("format", "TEXT")

            elif comp_type == "BODY":
                body_text = component.get("text", "")
                # Extract variables like {{1}}, {{2}}, etc.
                matches = re.findall(r'\{\{(\d+)\}\}', body_text)
                variables = [f"variable_{m}" for m in sorted(set(matches))]

            elif comp_type == "BUTTONS":
                has_buttons = True

        return TemplateParsed(
            id=template_data.get("id", ""),
            name=template_data.get("name", ""),
            status=template_data.get("status", ""),
            language=template_data.get("language", ""),
            category=template_data.get("category", ""),
            variables=variables,
            variable_count=len(variables),
            body_text=body_text,
            header_format=header_format,
            has_buttons=has_buttons,
        )

    def build_template_payload(
            self,
            template_name: str,
            language: str,
            parameters: List[str],
    ) -> Dict[str, Any]:
        """
        Build WhatsApp template message payload.

        Args:
            template_name: Name of the template
            language: Language code
            parameters: List of parameter values

        Returns:
            Template payload for WhatsApp API
        """
        components = []

        if parameters:
            # Build body parameters
            body_parameters = [
                {"type": "text", "text": str(param)}
                for param in parameters
            ]

            components.append({
                "type": "body",
                "parameters": body_parameters,
            })

        return {
            "name": template_name,
            "language": {
                "code": language,
            },
            "components": components,
        }

    async def validate_template_parameters(
            self,
            template_name: str,
            language: str,
            parameters: List[str],
    ) -> bool:
        """
        Validate that parameters match template requirements.

        Args:
            template_name:  Template name
            language: Language code
            parameters: Parameters to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If parameters don't match
        """
        from app.core.exceptions import ValidationError

        template = await self.get_template_by_name(template_name, language)

        expected_count = template.variable_count
        actual_count = len(parameters)

        if actual_count != expected_count:
            raise ValidationError(
                f"Template '{template_name}' requires {expected_count} parameters, "
                f"but {actual_count} were provided"
            )

        return True