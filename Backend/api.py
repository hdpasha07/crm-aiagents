import re
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from .db import SessionLocal, engine
from .models import Base
from .crud import (
    create_complaint,
    get_all_complaints,
    get_complaint_by_id,
    get_complaints_by_email,
    update_complaint,
    delete_complaint,
    get_metrics_summary,
    get_status_breakdown,
    get_priority_breakdown,
    get_daily_trend,
)
from .schemas import (
    ComplaintResponse,
    ComplaintUpdate,
    MetricsSummary,
    StatusBreakdown,
    PriorityBreakdown,
    DailyTrend,
)
from Agent.graph import build_graph
from Agent.security.pii_redactor import PIIRedactor
from Email.email_service import send_complaint_email

_pii_redactor = PIIRedactor()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Complaint Ingestion API")

# Initialize LangGraph Agent workflow
agent_app = build_graph()

DEFAULT_ESCALATION_MESSAGE = (
    "Your issue has been escalated to our support team. We will get back with you shortly."
)


def strip_source_metadata(text: str) -> str:
    """Strips internal source and chunk metadata brackets from customer response text."""
    if not text:
        return ""
    cleaned = re.sub(r"\[(?:Source|Chunk|Source Document|Chunk ID)[^\]]*\]", "", text)
    cleaned = re.sub(r" +([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
    return cleaned.strip()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ComplaintInput(BaseModel):
    email: EmailStr
    order_id: str
    complaint_text: str


@app.post("/complaints")
@app.post("/api/complaints")
def submit_complaint(data: ComplaintInput):
    db = SessionLocal()
    try:
        # 0. Redact PII from raw complaint text BEFORE any DB write or agent processing
        #    so the database and agent both only ever see the sanitised string.
        try:
            redaction = _pii_redactor.redact(data.complaint_text)
            safe_text = redaction.redacted_text
        except Exception as redact_err:
            print(f"PII redaction warning (continuing with original): {redact_err}")
            safe_text = data.complaint_text

        # 1. Run LangGraph agent workflow synchronously on the redacted text
        try:
            result = agent_app.invoke({
                "complaint_text": safe_text,
                "user_id": data.email,
            })
        except Exception as e:
            print(f"Agent invocation failed: {e}")
            result = {
                "escalation_required": True,
                "reevaluated_priority": "high",
                "response": DEFAULT_ESCALATION_MESSAGE,
                "response_email": DEFAULT_ESCALATION_MESSAGE,
            }

        # Handle invalid/guardrail-blocked complaints
        if result.get("is_valid") is False or result.get("guardrail_triggered"):
            guardrail_msg = (
                result.get("validation_reason")
                or "For your security, please do not share financial information here. How can I assist you with your order?"
            )
            complaint = create_complaint(
                db,
                email=data.email,
                order_id=data.order_id,
                text=safe_text,
                status="invalid",
                priority="none",
                escalation_required=False,
                email_sent=False,
            )
            return {
                "success": False,
                "is_valid": False,
                "guardrail_triggered": True,
                "status": "invalid",
                "escalation_required": False,
                "message": guardrail_msg,
                "response": guardrail_msg,
                "ai_response": None,
                "resolution": None,
                "complaint_id": complaint.id,
            }

        priority = (
            result.get("reevaluated_priority")
            or result.get("priority")
            or "medium"
        )
        escalation_required = bool(result.get("escalation_required", False))

        if escalation_required:
            status = "escalated"
            ai_response = None
            response_text = DEFAULT_ESCALATION_MESSAGE
            # Conditional Email Dispatch: only sent if escalation_required == True
            try:
                email_body = (
                    result.get("response")
                    or result.get("response_email")
                    or DEFAULT_ESCALATION_MESSAGE
                )
                send_complaint_email(
                    to_email=data.email,
                    subject="Regarding your recent support request - Escalated",
                    body=email_body,
                )
                email_sent = True
            except Exception as e:
                print(f"Error dispatching email: {e}")
                email_sent = False
        else:
            status = "Resolved"
            email_sent = False
            # Autonomous resolution: return the LLM's dynamic RAG generated response text (stripped of source metadata)
            raw_ai = (
                result.get("response")
                or result.get("response_email")
                or result.get("resolution")
                or ""
            )
            ai_response = strip_source_metadata(raw_ai)
            response_text = ai_response

        complaint = create_complaint(
            db,
            email=data.email,
            order_id=data.order_id,
            text=safe_text,
            status=status,
            priority=priority,
            escalation_required=escalation_required,
            email_sent=email_sent,
        )

        return {
            "success": True,
            "is_valid": True,
            "guardrail_triggered": False,
            "ai_response": ai_response if not escalation_required else None,
            "response": ai_response if not escalation_required else DEFAULT_ESCALATION_MESSAGE,
            "resolution": ai_response if not escalation_required else DEFAULT_ESCALATION_MESSAGE,
            "message": response_text,
            "escalation_required": escalation_required,
            "status": status,
            "complaint_id": complaint.id,
        }
    finally:
        db.close()


@app.get("/complaints", response_model=List[ComplaintResponse])
@app.get("/api/complaints", response_model=List[ComplaintResponse])
def list_complaints(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    db = SessionLocal()
    complaints = get_all_complaints(db, status, priority)
    db.close()
    return complaints


@app.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
@app.get("/api/complaints/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str):
    db = SessionLocal()
    complaint = get_complaint_by_id(db, complaint_id)
    db.close()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


@app.patch("/complaints/{complaint_id}", response_model=ComplaintResponse)
@app.patch("/api/complaints/{complaint_id}", response_model=ComplaintResponse)
def update_complaint_api(
    complaint_id: str,
    data: ComplaintUpdate
):
    db = SessionLocal()
    complaint = update_complaint(
        db,
        complaint_id,
        data.status,
        data.priority
    )
    db.close()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


@app.delete("/complaints/{complaint_id}")
@app.delete("/api/complaints/{complaint_id}")
def delete_complaint_api(complaint_id: str):
    db = SessionLocal()
    success = delete_complaint(db, complaint_id)
    db.close()

    if not success:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return {"message": "Complaint deleted successfully"}


@app.get(
    "/complaints/by-email/{email}",
    response_model=List[ComplaintResponse]
)
@app.get(
    "/api/complaints/by-email/{email}",
    response_model=List[ComplaintResponse]
)
def get_complaints_for_customer(email: str):
    db = SessionLocal()
    complaints = get_complaints_by_email(db, email)
    db.close()
    return complaints


@app.get("/analytics/summary", response_model=MetricsSummary)
@app.get("/api/analytics/summary", response_model=MetricsSummary)
def analytics_summary():
    db = SessionLocal()
    data = get_metrics_summary(db)
    db.close()
    return data


@app.get("/analytics/status", response_model=StatusBreakdown)
@app.get("/api/analytics/status", response_model=StatusBreakdown)
def analytics_by_status():
    db = SessionLocal()
    data = get_status_breakdown(db)
    db.close()
    return {"by_status": data}


@app.get("/analytics/priority", response_model=PriorityBreakdown)
@app.get("/api/analytics/priority", response_model=PriorityBreakdown)
def analytics_by_priority():
    db = SessionLocal()
    data = get_priority_breakdown(db)
    db.close()
    return {"by_priority": data}


@app.get("/analytics/trends", response_model=List[DailyTrend])
@app.get("/api/analytics/trends", response_model=List[DailyTrend])
def analytics_trends():
    db = SessionLocal()
    data = get_daily_trend(db)
    db.close()
    return data
