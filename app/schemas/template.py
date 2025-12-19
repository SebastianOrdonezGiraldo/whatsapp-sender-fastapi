"""WhatsApp Template schemas."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class TemplateParameter(BaseModel):
    """Template parameter for dynamic content."""

    type: str = Field(default="text", description="Parameter type (text, currency, date_time)")
    text: Optional[str] = Field(None, description="Text value for text type")
    currency: Optional[Dict[str, Any]] = Field(None, description="Currency data")
    date_time: Optional[Dict[str, Any]] = Field(None, description="Date/time data")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "text",
                "text": "Juan"
            }
        }


class TemplateComponent(BaseModel):
    """Template component (header, body, footer, buttons)."""

    type: str = Field(..., description="Component type:  HEADER, BODY, FOOTER, BUTTONS")
    format: Optional[str] = Field(None, description="Format for HEADER:  TEXT, IMAGE, VIDEO, DOCUMENT")
    text: Optional[str] = Field(None, description="Template text with placeholders")
    example: Optional[Dict[str, List[str]]] = Field(None, description="Example values for variables")
    parameters: Optional[List[TemplateParameter]] = Field(None, description="Parameters for sending")
    buttons: Optional[List[Dict[str, Any]]] = Field(None, description="Button definitions")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "BODY",
                "text": "Hola {{1}}, tu producto {{2}} está listo!",
                "example": {
                    "body_text": [["Juan", "Laptop"]]
                }
            }
        }


class TemplateLanguage(BaseModel):
    """Template language."""

    code: str = Field(default="es", description="Language code (es, en, pt, etc.)")
    policy: Optional[str] = Field(None, description="Language policy")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "es"
            }
        }


class TemplateResponse(BaseModel):
    """WhatsApp template from Meta API."""

    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    status: str = Field(..., description="Template status:  APPROVED, PENDING, REJECTED, DISABLED")
    language: str = Field(..., description="Template language code")
    category: str = Field(..., description="Template category:  MARKETING, UTILITY, AUTHENTICATION")
    components: List[Dict[str, Any]] = Field(..., description="Template components")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456789",
                "name": "bienvenida",
                "status": "APPROVED",
                "language": "es",
                "category": "MARKETING",
                "components": [
                    {
                        "type": "BODY",
                        "text": "Hola {{1}}, bienvenido a {{2}}!"
                    }
                ]
            }
        }


class TemplateParsed(BaseModel):
    """Parsed template with variable information."""

    id: str
    name: str
    status: str
    language: str
    category: str
    variables: List[str] = Field(default_factory=list, description="List of variable placeholders")
    variable_count: int = Field(default=0, description="Number of variables")
    body_text: Optional[str] = Field(None, description="Body text with placeholders")
    header_format: Optional[str] = Field(None, description="Header format if exists")
    has_buttons: bool = Field(default=False, description="Whether template has buttons")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "123456789",
                "name": "bienvenida",
                "status": "APPROVED",
                "language": "es",
                "category": "MARKETING",
                "variables": ["nombre", "empresa"],
                "variable_count": 2,
                "body_text": "Hola {{1}}, bienvenido a {{2}}!",
                "header_format": None,
                "has_buttons": False
            }
        }


class TemplateListResponse(BaseModel):
    """List of templates response."""

    templates: List[TemplateParsed]
    total: int
    approved: int
    pending: int
    rejected: int

    class Config:
        json_schema_extra = {
            "example": {
                "templates": [],
                "total": 10,
                "approved": 8,
                "pending": 1,
                "rejected": 1
            }
        }


class SendTemplateRequest(BaseModel):
    """Request to send message with template."""

    template_name: str = Field(..., description="Template name")
    template_language: str = Field(default="es", description="Template language code")
    to: str = Field(..., description="Recipient phone number with country code")
    parameters: List[str] = Field(..., description="Values for template variables in order")

    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "bienvenida",
                "template_language": "es",
                "to": "+573001234567",
                "parameters": ["Juan", "Mi Empresa"]
            }
        }