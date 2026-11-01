from Backend.db import SessionLocal
from Backend.crud import (
    get_new_complaints,
    mark_complaint_as_spam,
    update_complaint_result,
    update_complaint_status,
    mark_email_sent,
)

from Agent.graph import build_graph
from FinalisingAgent.resolution import decide_resolution
from Email.email_service import send_email, send_complaint_email

app = build_graph()


def process_complaints():
    db = SessionLocal()
    complaints = get_new_complaints(db)

    print(f"Found {len(complaints)} new complaints")

    for c in complaints:
        print(f"\nProcessing complaint {c.id}")

        # Run agent
        try:
            result = app.invoke({"complaint_text": c.complaint_text})

            if result.get("is_valid") is False:
                print(f"🛑 Spam detected: {result.get('validation_reason')}")
                mark_complaint_as_spam(db, c.id, result.get("validation_reason", "Spam"))
                continue

        except Exception as e:
            print(f"❌ Agent failed for complaint {c.id}: {e}")
            continue

        priority = result.get("reevaluated_priority") or result.get("priority") or "medium"
        escalation_required = bool(result.get("escalation_required", False))
        email_body = result.get("response_email")

        # Check conditional email dispatch:
        # Emails are ONLY sent if the LangGraph agent workflow flags the complaint as requiring human escalation
        if escalation_required:
            subject = "Regarding your recent support request - Escalated"
            body = (
                email_body
                or "Your issue has been escalated to our support team. We will get back with you shortly."
            )

            send_complaint_email(
                to_email=c.email,
                subject=subject,
                body=body,
            )

            mark_email_sent(db, c.id)
            update_complaint_status(db, c.id, "escalated")
            update_complaint_result(
                db,
                complaint_id=c.id,
                priority=priority,
                escalated=True,
                status="escalated",
            )
            print("🚨 Escalated & acknowledgement email dispatched via send_complaint_email")
        else:
            # Autonomous resolution: bypass email dispatch entirely, but still log to DB with 'Resolved' status
            update_complaint_status(db, c.id, "Resolved")
            update_complaint_result(
                db,
                complaint_id=c.id,
                priority=priority,
                escalated=False,
                status="Resolved",
            )
            print("✅ Auto-resolved & email dispatch bypassed entirely (logged as 'Resolved')")

    db.close()
