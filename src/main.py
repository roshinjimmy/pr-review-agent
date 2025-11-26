from fastapi import FastAPI

from src.models.diff import DiffRequest
from src.utils.diff_parser import parse_unified_diff


app = FastAPI(title="PR Review Agent", version="0.1.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/review/diff")
async def review_diff(request: DiffRequest) -> dict:
    parsed = parse_unified_diff(request.diff)

    files = []
    for fd in parsed:
        files.append(
            {
                "file": fd.file,
                "changes": [
                    {
                        "type": c.type,
                        "line": c.line,
                        "content": c.content,
                    }
                    for c in fd.changes
                ],
            }
        )

    return {"files": files}
