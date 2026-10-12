from pydantic import BaseModel
from typing import Literal

class ReevaluationOutput(BaseModel):
    updated_priority: Literal["low", "medium", "high"]
    reason: str
