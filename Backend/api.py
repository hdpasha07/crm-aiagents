import json
from typing import List, Optional, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from .db import SessionLocal, engine
from .models import Base
from .crud import create_complaint,get_all_complaints,get_complaint_by_id,get_complaints_by_email,update_complaint,delete_complaint,get_metrics_summary,get_status_breakdown,get_priority_breakdown,get_daily_trend
from .schemas import ComplaintResponse,ComplaintUpdate,MetricsSummary,StatusBreakdown,PriorityBreakdown,DailyTrend
from Agent.security.pii_redactor import PIIRedactor
from Agent.graph.agent_graph import CustomerSupportAgent

_agent_instance: Optional[CustomerSupportAgent] = None


def get_agent() -> CustomerSupportAgent:
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = CustomerSupportAgent()
    return _agent_instance

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Complaint Ingestion API")


class PresidioGuardrailMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts incoming JSON request payloads and scrubs sensitive PII
    (credit cards, SSNs, phone numbers, etc.) using Microsoft Presidio before the payload
    reaches route handlers, databases, or the agent graph.
    """
    def __init__(self, app, redactor: Optional[PIIRedactor] = None):
        super().__init__(app)
        self.redactor = redactor or PIIRedactor()

    async def dispatch(self, request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH") and "application/json" in request.headers.get("content-type", ""):
            try:
                body_bytes = await request.body()
                if body_bytes:
                    payload = json.loads(body_bytes.decode("utf-8"))

                    def scrub_value(key: str, val: Any) -> Any:
                        if isinstance(val, str):
                            # Retain top-level user account email if it is a single valid email address
                            if key.lower() == "email" and "@" in val and len(val.split()) == 1:
                                return val
                            return self.redactor.redact(val).redacted_text
                        elif isinstance(val, dict):
                            return {k: scrub_value(k, v) for k, v in val.items()}
                        elif isinstance(val, list):
                            return [scrub_value(key, item) for item in val]
                        return val

                    scrubbed = scrub_value("root", payload)
                    new_body = json.dumps(scrubbed).encode("utf-8")
                    request._body = new_body

                    async def receive():
                        return {"type": "http.request", "body": new_body}
                    request._receive = receive
            except Exception:
                pass
        return await call_next(request)


app.add_middleware(PresidioGuardrailMiddleware)

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
def submit_complaint(data: ComplaintInput):
    db = SessionLocal()
    complaint = create_complaint(
        db,
        data.email,
        data.order_id,
        data.complaint_text
    )
    db.close()

    # Invoke the LangGraph agent pipeline to generate the actual AI response
    try:
        agent = get_agent()
        user_message = (
            f"Regarding Order #{data.order_id}: {data.complaint_text}"
            if data.order_id
            else data.complaint_text
        )
        agent_result = agent.chat(
            user_message=user_message,
            customer_id=str(data.email),
            thread_id=f"complaint_{complaint.id}",
        )
        ai_response = agent_result.get("answer") or "Complaint submitted successfully and is being reviewed."
    except Exception as exc:
        ai_response = (
            f"Your complaint regarding Order #{data.order_id} has been submitted successfully "
            "and our support team is reviewing it."
        )

    return {
        "message": ai_response,
        "complaint_id": complaint.id
    }

@app.get("/complaints", response_model=List[ComplaintResponse])
def list_complaints(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None)
):
    db = SessionLocal()
    complaints = get_all_complaints(db, status, priority)
    db.close()
    return complaints


@app.get("/complaints/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(complaint_id: str):
    db = SessionLocal()
    complaint = get_complaint_by_id(db, complaint_id)
    db.close()

    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    return complaint


@app.patch("/complaints/{complaint_id}", response_model=ComplaintResponse)
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
def get_complaints_for_customer(email: str):
    db = SessionLocal()
    complaints = get_complaints_by_email(db, email)
    db.close()
    return complaints

@app.get("/analytics/summary", response_model=MetricsSummary)
def analytics_summary():
    db = SessionLocal()
    data = get_metrics_summary(db)
    db.close()
    return data


@app.get("/analytics/status", response_model=StatusBreakdown)
def analytics_by_status():
    db = SessionLocal()
    data = get_status_breakdown(db)
    db.close()
    return {"by_status": data}


@app.get("/analytics/priority", response_model=PriorityBreakdown)
def analytics_by_priority():
    db = SessionLocal()
    data = get_priority_breakdown(db)
    db.close()
    return {"by_priority": data}


@app.get("/analytics/trends", response_model=List[DailyTrend])
def analytics_trends():
    db = SessionLocal()
    data = get_daily_trend(db)
    db.close()
    return data
