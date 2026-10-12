import json
from pathlib import Path

POLICY_FILE = Path(__file__).resolve().parent.parent / "policies" / "company_policies.json"

def load_policies():
    with open(POLICY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
