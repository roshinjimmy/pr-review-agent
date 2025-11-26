"""Error models for structured error responses."""

from typing import Optional
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    type: str = Field(..., description="Error type/category")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional technical details")


class ErrorResponse(BaseModel):
    """Structured error response."""
    
    error: ErrorDetail
