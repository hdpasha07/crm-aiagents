from pydantic import BaseModel

class ResponseOutput(BaseModel):
    subject: str
    body: str
