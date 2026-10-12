from Backend.db import SessionLocal
from Backend.crud import get_metrics_summary
import json

db = SessionLocal()
summary = get_metrics_summary(db)
print(json.dumps(summary, indent=2))
db.close()
