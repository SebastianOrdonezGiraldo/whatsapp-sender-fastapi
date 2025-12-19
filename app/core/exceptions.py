"""Custom exceptions for the application."""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details:  Optional[dict[str, Any]] = None,
    ):
        """
        Initialize application exception.

        Args:
            message: Error message
            code: Error code for client
            details: Additional error details
        """
        self.message = message
        self. code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppException):
    """Exception raised when a resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize not found error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message=message, code="NOT_FOUND", details=details)


class ValidationError(AppException):
    """Exception raised when validation fails."""

    def __init__(
        self,
        message: str = "Validation error",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize validation error.

        Args:
            message: Error message
            details:  Additional error details
        """
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class AuthenticationError(AppException):
    """Exception raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize authentication error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message=message, code="AUTHENTICATION_ERROR", details=details)


class AuthorizationError(AppException):
    """Exception raised when authorization fails."""

    def __init__(
        self,
        message:  str = "Authorization failed",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize authorization error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message=message, code="AUTHORIZATION_ERROR", details=details)


class ConflictError(AppException):
    """Exception raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize conflict error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message=message, code="CONFLICT", details=details)


class ExternalServiceError(AppException):
    """Exception raised when an external service fails."""

    def __init__(
        self,
        message: str = "External service error",
        service_name: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize external service error.

        Args:
            message: Error message
            service_name: Name of the external service
            details: Additional error details
        """
        details = details or {}
        if service_name:
            details["service"] = service_name

        super().__init__(
            message=message,
            code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )


class RateLimitError(AppException):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details:  Optional[dict[str, Any]] = None,
    ):
        """
        Initialize rate limit error.

        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after

        super().__init__(message=message, code="RATE_LIMIT_ERROR", details=details)


class DatabaseError(AppException):
    """Exception raised when a database operation fails."""

    def __init__(
        self,
        message: str = "Database error",
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize database error.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message=message, code="DATABASE_ERROR", details=details)