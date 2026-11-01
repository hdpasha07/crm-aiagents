import json
from typing import Optional, Dict, Any

def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Simulates an SQLite database lookup by user_id.
    Returns the user's profile dictionary, or None if not found.
    """
    try:
        with open("users.json", "r") as file:
            db = json.load(file)
        return db.get(user_id)
    except FileNotFoundError:
        print("Error: users.json database file not found.")
        return None