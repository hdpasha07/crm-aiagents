from sqlalchemy.orm import Session
from .models import Complaint
from sqlalchemy import func

def create_complaint(
    db: Session,
    email: str,
    order_id: str,
    text: str,
    status: str = "new",
    priority: str | None = None,
    escalation_required: bool = False,
    email_sent: bool = False
):
    complaint = Complaint(
        email=email,
        order_id=order_id,
        complaint_text=text,
        status=status,
        priority=priority,
        escalation_required=escalation_required,
        email_sent=email_sent
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def get_new_complaints(db: Session):
    return db.query(Complaint).filter(Complaint.status == "new").all()


def update_complaint_result(
    db: Session,
    complaint_id: str,
    priority: str,
    escalated: bool,
    status: str | None = None
):
    complaint = db.query(Complaint).get(complaint_id)
    if complaint:
        complaint.priority = priority
        complaint.escalation_required = escalated
        if status is not None:
            complaint.status = status
        else:
            complaint.status = "escalated" if escalated else "Resolved"
        db.commit()
    return complaint

def update_complaint_status(
    db: Session,
    complaint_id: str,
    status: str
):
    complaint = db.query(Complaint).get(complaint_id)
    if complaint:
        complaint.status = status
        db.commit()
    return complaint

def mark_complaint_resolved(db: Session, complaint_id: str):
    complaint = db.query(Complaint).get(complaint_id)
    if complaint:
        complaint.status = "Resolved"
        complaint.escalation_required = False
        db.commit()
    return complaint

def mark_email_sent(db: Session, complaint_id: str):
    complaint = db.query(Complaint).get(complaint_id)
    if complaint:
        complaint.email_sent = True
        db.commit()
    return complaint

def get_all_complaints(
    db: Session,
    status: str | None = None,
    priority: str | None = None
):
    query = db.query(Complaint)
    if status:
        query = query.filter(func.lower(Complaint.status) == status.lower())
    if priority:
        query = query.filter(func.lower(Complaint.priority) == priority.lower())
    return query.order_by(Complaint.created_at.desc()).all()


def get_complaint_by_id(db: Session, complaint_id: str):
    return db.query(Complaint).filter(Complaint.id == complaint_id).first()


def get_complaints_by_email(db: Session, email: str):
    return (
        db.query(Complaint)
        .filter(Complaint.email == email)
        .order_by(Complaint.created_at.desc())
        .all()
    )


def update_complaint(
    db: Session,
    complaint_id: str,
    status: str | None,
    priority: str | None
):
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return None

    if status:
        complaint.status = status
    if priority:
        complaint.priority = priority

    db.commit()
    db.refresh(complaint)
    return complaint


def delete_complaint(db: Session, complaint_id: str):
    complaint = get_complaint_by_id(db, complaint_id)
    if not complaint:
        return False

    db.delete(complaint)
    db.commit()
    return True

def get_metrics_summary(db):
    total = db.query(func.count(Complaint.id)).scalar()
    resolved = (
        db.query(func.count(Complaint.id))
        .filter(func.lower(Complaint.status) == "resolved")
        .scalar()
    )
    escalated = (
        db.query(func.count(Complaint.id))
        .filter(func.lower(Complaint.status) == "escalated")
        .scalar()
    )

    resolution_rate = (resolved / total * 100) if total else 0
    escalation_rate = (escalated / total * 100) if total else 0

    return {
        "total_complaints": total,
        "resolved": resolved,
        "escalated": escalated,
        "resolution_rate": round(resolution_rate, 2),
        "escalation_rate": round(escalation_rate, 2),
    }


def get_status_breakdown(db):
    rows = (
        db.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
        .all()
    )
    return {status: count for status, count in rows}


def get_priority_breakdown(db):
    rows = (
        db.query(Complaint.priority, func.count(Complaint.id))
        .group_by(Complaint.priority)
        .all()
    )
    return {priority or "unassigned": count for priority, count in rows}


def get_daily_trend(db):
    rows = (
        db.query(
            func.date(Complaint.created_at),
            func.count(Complaint.id)
        )
        .group_by(func.date(Complaint.created_at))
        .order_by(func.date(Complaint.created_at))
        .all()
    )

    return [
        {"date": str(date), "count": count}
        for date, count in rows
    ]

def mark_complaint_as_spam(db, complaint_id: str, reason: str):
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if complaint:
        complaint.status = "spam"
        complaint.priority = "none"
        complaint.escalation_required = False
        db.commit()
