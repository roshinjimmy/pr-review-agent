import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")
openrouter_key = os.getenv("OPENROUTER_API_KEY")
if not openrouter_key:
    raise RuntimeError("OPENROUTER_API_KEY not found in environment")

os.environ["OPENROUTER_API_KEY"] = openrouter_key

from fastapi import FastAPI
from src.models.diff import DiffRequest
from src.models.review import ReviewResponse
from src.services.orchestrator import run_review_pipeline
from src.utils.diff_parser import parse_unified_diff

app = FastAPI(title="PR Review Agent", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/review/diff", response_model=ReviewResponse)
async def review_diff(request: DiffRequest) -> ReviewResponse:
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
