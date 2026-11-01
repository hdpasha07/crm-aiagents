from pydantic import BaseModel
from typing import Literal

class SentimentOutput(BaseModel):
    sentiment: Literal["angry", "neutral", "chill"]
