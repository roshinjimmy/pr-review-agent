from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ReviewComment(BaseModel):
    """A single code review comment."""

    file: str = Field(..., description="File path where the issue was found")
    line: Optional[int] = Field(None, description="Line number of the issue")
    severity: Literal["critical", "error", "warning", "high", "moderate", "medium", "low", "info"] = Field(
        ..., description="Severity level of the issue"
    )
    issue: str = Field(..., description="Description of the issue")
    recommendation: str = Field(..., description="Suggested fix or improvement")
    source: Optional[str] = Field(
        None, description="Agent that generated this comment (e.g., 'readability', 'security')"
    )


class ReviewResponse(BaseModel):
    """Response containing all review comments."""

    comments: List[ReviewComment] = Field(
        default_factory=list, description="List of review comments"
    )
