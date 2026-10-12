import json
from pathlib import Path
from typing import Optional, Dict, Any

_USERS_FILE = Path(__file__).resolve().parents[2] / "users.json"

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Simulates an SQLite database lookup by user_id.
    Returns the user's profile dictionary, or None if not found.
    """
    try:
        with _USERS_FILE.open("r", encoding="utf-8") as file:
            db = json.load(file)
        return db.get(user_id)
    except FileNotFoundError:
        print("Error: users.json database file not found.")
        return None
