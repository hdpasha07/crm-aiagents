from pydantic import BaseModel


class ValidationOutput(BaseModel):
    is_valid: bool
    reason: str
