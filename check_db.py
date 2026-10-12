from Backend.db import SessionLocal
from Backend.models import Complaint
from sqlalchemy import func

db = SessionLocal()
statuses = db.query(Complaint.status, func.count(Complaint.id)).group_by(Complaint.status).all()
print("Current Statuses in DB:", statuses)
db.close()
