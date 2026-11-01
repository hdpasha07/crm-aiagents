from pydantic import BaseModel
from typing import Literal

class PriorityOutput(BaseModel):
    priority: Literal["low", "medium", "high"]
    reason: str
