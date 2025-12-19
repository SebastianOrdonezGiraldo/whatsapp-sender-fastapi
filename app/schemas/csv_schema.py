"""CSV validation schemas."""

from typing import Optional

from pydantic import Field, field_validator

from app.schemas. base import BaseSchema


class CSVRecipient(BaseSchema):
    """Schema for CSV recipient row."""

    phone: str = Field(..., alias="Recipient-Phone-Number")
    variables: dict[str, str] = Field(default_factory=dict)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        # Remove spaces and dashes
        phone = v.replace(" ", "").replace("-", "")

        # Add + if not present
        if not phone. startswith("+"):
            phone = f"+{phone}"

        # Basic validation (international format)
        if not phone[1:].isdigit():
            raise ValueError(f"Invalid phone number format: {v}")

        if len(phone) < 10 or len(phone) > 16:
            raise ValueError(f"Phone number length invalid: {v}")

        return phone


class CSVUploadResponse(BaseSchema):
    """Response schema for CSV upload."""

    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[dict[str, str]] = Field(default_factory=list)
    file_path: Optional[str] = None


class CSVValidationError(BaseSchema):
    """Schema for CSV validation error."""

    row:  int
    column: Optional[str] = None
    value: Optional[str] = None
    error: str