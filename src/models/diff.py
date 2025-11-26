from pydantic import BaseModel


class DiffRequest(BaseModel):
    diff: str
