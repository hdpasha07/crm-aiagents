from pydantic import BaseModel

class ResolutionDecision(BaseModel):
    auto_resolve: bool
    reason: str
