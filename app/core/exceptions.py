"""Custom exception classes."""

from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
            self,
            message: str,
            code: Optional[str] = None,
            details: Optional[dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code or "APP_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(AppException):
    """Database-related exceptions."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class WhatsAppAPIException(AppException):
    """WhatsApp API exceptions."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="WHATSAPP_API_ERROR", details=details)


class CampaignNotFoundException(AppException):
    """Campaign not found exception."""

    def __init__(self, campaign_id: int):
        super().__init__(
            message=f"Campaign with ID {campaign_id} not found",
            code="CAMPAIGN_NOT_FOUND",
            details={"campaign_id": campaign_id},
        )


class InvalidCSVException(AppException):
    """Invalid CSV file exception."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        super().__init__(message, code="INVALID_CSV", details=details)