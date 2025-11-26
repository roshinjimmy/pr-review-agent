from pydantic import BaseModel, Field


class DiffRequest(BaseModel):
    diff: str


class PRReviewRequest(BaseModel):
    """Request to review a GitHub Pull Request."""
    
    repo_owner: str = Field(..., description="GitHub repository owner (username or org)")
    repo_name: str = Field(..., description="GitHub repository name")
    pr_number: int = Field(..., description="Pull request number", gt=0)
    github_token: str = Field(..., description="GitHub personal access token")
