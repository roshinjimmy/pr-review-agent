import os
from pathlib import Path
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in environment")

os.environ["OPENROUTER_API_KEY"] = openrouter_key

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from src.models.diff import DiffRequest, PRReviewRequest
from src.models.review import ReviewResponse
from src.models.errors import ErrorResponse, ErrorDetail
from src.services.orchestrator import run_review_pipeline
from src.services.github_service import (
    fetch_pr_diff, 
    GitHubAPIError,
    PRNotFoundError,
    InvalidTokenError,
    RateLimitError,
    EmptyPRError,
    BinaryDiffError,
    NetworkError
)
from src.utils.diff_parser import parse_unified_diff
from src.utils.logger import setup_logger, log_with_context

logger = setup_logger(__name__)

app = FastAPI(title="PR Review Agent", version="0.1.0")
startup_time = datetime.now(timezone.utc)


@app.exception_handler(GitHubAPIError)
async def github_api_error_handler(request: Request, exc: GitHubAPIError):
    """Handle all GitHub API errors with structured responses."""
    status_code = 400
    
    # Map specific error types to appropriate HTTP status codes
    if isinstance(exc, PRNotFoundError):
        status_code = 404
    elif isinstance(exc, InvalidTokenError):
        status_code = 401
    elif isinstance(exc, RateLimitError):
        status_code = 429
    elif isinstance(exc, NetworkError):
        status_code = 503
    elif isinstance(exc, (EmptyPRError, BinaryDiffError)):
        status_code = 422
    
    error_response = ErrorResponse(
        error=ErrorDetail(
            type=exc.error_type,
            message=exc.message,
            details=exc.details
        )
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump()
    )


@app.get("/health")
async def health() -> dict:
    uptime_seconds = (datetime.now(timezone.utc) - startup_time).total_seconds()
    return {
        "status": "ok",
        "uptime_seconds": uptime_seconds,
        "version": "0.1.0"
    }


@app.post("/review/diff", response_model=ReviewResponse)
async def review_diff(request: DiffRequest) -> ReviewResponse:
    """Review a raw unified diff."""
    log_with_context(logger, "info", "Received diff review request", endpoint="/review/diff")
    
    try:
        # Validate diff is not empty
        if not request.diff or request.diff.strip() == "":
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "type": "EmptyDiffError",
                        "message": "Diff content is empty",
                        "details": "Provided diff string contains no content"
                    }
                }
            )
        
        # Check for binary files
        if "Binary files" in request.diff or "GIT binary patch" in request.diff:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "type": "BinaryDiffError",
                        "message": "Diff contains binary files that cannot be reviewed",
                        "details": "Detected binary file markers in diff"
                    }
                }
            )
        
        parsed = parse_unified_diff(request.diff)
        
        # Check if parsing yielded any files
        if not parsed:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "type": "DiffParseError",
                        "message": "Failed to parse diff - no valid file changes found",
                        "details": "Diff format may be invalid or contain no parseable changes"
                    }
                }
            )
        
        files = [
            {
                "file": fd.file,
                "changes": [
                    {"type": c.type, "line": c.line, "content": c.content}
                    for c in fd.changes
                ],
            }
            for fd in parsed
        ]

        structured_diff = {"files": files}
        review_output = run_review_pipeline(structured_diff)

        # Return validated Pydantic response
        response = ReviewResponse(**review_output)
        
        log_with_context(
            logger, "info", "Diff review completed successfully",
            endpoint="/review/diff",
            total_comments=len(response.comments)
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Unexpected error in diff review",
            endpoint="/review/diff",
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "InternalError",
                    "message": "An unexpected error occurred while processing the diff",
                    "details": str(e)
                }
            }
        )


@app.post("/review/pr", response_model=ReviewResponse)
async def review_pr(request: PRReviewRequest) -> ReviewResponse:
    """Review a GitHub Pull Request by fetching its diff."""
    log_with_context(
        logger, "info", "Received PR review request",
        endpoint="/review/pr",
        repo=f"{request.repo_owner}/{request.repo_name}",
        pr_number=request.pr_number
    )
    
    try:
        # Fetch the PR diff from GitHub (errors handled by exception handler)
        diff_text = await fetch_pr_diff(
            repo_owner=request.repo_owner,
            repo_name=request.repo_name,
            pr_number=request.pr_number,
            github_token=request.github_token
        )
        
        # Parse the diff
        parsed = parse_unified_diff(diff_text)
        
        # Check if parsing yielded any files
        if not parsed:
            raise EmptyPRError(
                f"Pull request #{request.pr_number} has no parseable file changes",
                details="Diff was fetched but contained no valid unified diff format"
            )
        
        files = [
            {
                "file": fd.file,
                "changes": [
                    {"type": c.type, "line": c.line, "content": c.content}
                    for c in fd.changes
                ],
            }
            for fd in parsed
        ]

        structured_diff = {"files": files}
        review_output = run_review_pipeline(structured_diff)

        # Return validated Pydantic response
        response = ReviewResponse(**review_output)
        
        log_with_context(
            logger, "info", "PR review completed successfully",
            endpoint="/review/pr",
            repo=f"{request.repo_owner}/{request.repo_name}",
            pr_number=request.pr_number,
            total_comments=len(response.comments)
        )
        
        return response
        
    except GitHubAPIError:
        # Re-raise to be caught by exception handler
        raise
    except Exception as e:
        log_with_context(
            logger, "error", "Unexpected error in PR review",
            endpoint="/review/pr",
            repo=f"{request.repo_owner}/{request.repo_name}",
            pr_number=request.pr_number,
            error=str(e)
        )
        # Wrap unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "type": "InternalError",
                    "message": "An unexpected error occurred while reviewing the PR",
                    "details": str(e)
                }
            }
        )
