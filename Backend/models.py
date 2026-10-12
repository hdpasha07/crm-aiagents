from sqlalchemy import Column, String, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime
import uuid

from .db import Base

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, nullable=False)
    order_id = Column(String, nullable=False)
    complaint_text = Column(Text, nullable=False)

    status = Column(String, default="new")  # new | processed | escalated | resolved
    priority = Column(String, nullable=True)
    escalation_required = Column(Boolean, default=False)

    email_sent = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
