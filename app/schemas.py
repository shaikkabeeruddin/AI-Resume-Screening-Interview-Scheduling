from pydantic import BaseModel

class ProcessResponse(BaseModel):
    success: bool
    message: str
    candidate_id: str | None = None
    match_score: int | None = None
    recommendation: str | None = None