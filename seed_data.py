from Backend.db import SessionLocal
from Backend.models import Complaint

def seed():
    db = SessionLocal()

    complaints = [
        Complaint(
            email="alice@example.com",
            order_id="ORD-3001",
            complaint_text="Payment failed but money was deducted.",
            status="escalated",
            priority="high",
            escalation_required=True,
            email_sent=True
        ),
        Complaint(
            email="bob@example.com",
            order_id="ORD-3002",
            complaint_text="Package arrived late.",
            status="resolved",
            priority="medium",
            escalation_required=False,
            email_sent=True
        ),
        Complaint(
            email="charlie@example.com",
            order_id="ORD-3003",
            complaint_text="Just wanted to give positive feedback!",
            status="resolved",
            priority="low",
            escalation_required=False,
            email_sent=True
        ),
        Complaint(
            email="alice@example.com",
            order_id="ORD-3004",
            complaint_text="Wrong item delivered.",
            status="escalated",
            priority="high",
            escalation_required=True,
            email_sent=False
        ),
        Complaint(
            email="david@example.com",
            order_id="ORD-3005",
            complaint_text="How do I change my shipping address?",
            status="new",
            priority=None,
            escalation_required=False,
            email_sent=False
        ),
    ]

    db.add_all(complaints)
    db.commit()
    db.close()
    print("✅ Test complaints inserted")

if __name__ == "__main__":
    seed()
    