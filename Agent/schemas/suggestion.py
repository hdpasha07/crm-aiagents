from pydantic import BaseModel
from typing import List

class SuggestionOutput(BaseModel):
    actions: List[str]
