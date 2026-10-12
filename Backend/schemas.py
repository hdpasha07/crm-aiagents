from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime

class ComplaintResponse(BaseModel):
    id: str
    email: EmailStr
    order_id: str
    complaint_text: str
    status: str
    priority: Optional[str]
    escalation_required: bool
    email_sent: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ComplaintUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None

class MetricsSummary(BaseModel):
    total_complaints: int
    resolved: int
    escalated: int
    resolution_rate: float
    escalation_rate: float


class StatusBreakdown(BaseModel):
    by_status: Dict[str, int]


class PriorityBreakdown(BaseModel):
    by_priority: Dict[str, int]


class DailyTrend(BaseModel):
    date: str
    count: int
