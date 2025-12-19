"""Base schemas for common response patterns."""

from typing import Any, Generic, Optional, TypeVar
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime


DataT = TypeVar("DataT")


class ResponseSchema(BaseSchema, Generic[DataT]):
    """Generic response wrapper."""

    success: bool = True
    message: str = "Success"
    data: Optional[DataT] = None


class PaginationSchema(BaseSchema):
    """Pagination metadata."""

    page: int
    page_size: int
    total: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class PaginatedResponseSchema(BaseSchema, Generic[DataT]):
    """Paginated response wrapper."""

    success: bool = True
    message: str = "Success"
    data: list[DataT]
    pagination: PaginationSchema


class ErrorDetailSchema(BaseSchema):
    """Error detail schema."""

    code: str
    message: str
    details: Optional[dict[str, Any]] = None


class ErrorResponseSchema(BaseSchema):
    """Error response schema."""

    success: bool = False
    error: ErrorDetailSchema