from pydantic import BaseModel
from typing import Literal

class CategoryOutput(BaseModel):
    category: Literal[
        "payment_issue",
        "delivery_issue",
        "technical_issue",
        "feedback",
        "other"
    ]
