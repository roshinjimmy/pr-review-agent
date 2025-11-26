import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in environment")

os.environ["OPENROUTER_API_KEY"] = openrouter_key

from fastapi import FastAPI, HTTPException
from src.models.diff import DiffRequest, PRReviewRequest
from src.models.review import ReviewResponse
from src.services.orchestrator import run_review_pipeline
from src.services.github_service import fetch_pr_diff, GitHubAPIError
from src.utils.diff_parser import parse_unified_diff

app = FastAPI(title="PR Review Agent", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/review/diff", response_model=ReviewResponse)
async def review_diff(request: DiffRequest) -> ReviewResponse:
    """Review a raw unified diff."""
    parsed = parse_unified_diff(request.diff)
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
    return ReviewResponse(**review_output)


@app.post("/review/pr", response_model=ReviewResponse)
async def review_pr(request: PRReviewRequest) -> ReviewResponse:
    """Review a GitHub Pull Request by fetching its diff."""
    try:
        # Fetch the PR diff from GitHub
        diff_text = await fetch_pr_diff(
            repo_owner=request.repo_owner,
            repo_name=request.repo_name,
            pr_number=request.pr_number,
            github_token=request.github_token
        )
        
        # Parse the diff
        parsed = parse_unified_diff(diff_text)
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
        return ReviewResponse(**review_output)
        
    except GitHubAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))
