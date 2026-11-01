import os
import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

# Directory to store persistence files
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database path
SQLITE_DB_PATH = DATA_DIR / "profiles.db"
# JSON fallback path
JSON_PATH = DATA_DIR / "profiles.json"


def _use_sqlite() -> bool:
    """Check if SQLite is usable (i.e., file can be created)."""
    try:
        # Try to open a connection; if fails, fallback
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        conn.close()
        return True
    except Exception:
        return False


def init_db() -> None:
    """Initialize the persistence layer.

    Creates the SQLite table if possible; otherwise ensures the JSON file exists.
    """
    if _use_sqlite():
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                user_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    else:
        # Ensure JSON file exists
        if not JSON_PATH.exists():
            JSON_PATH.write_text(json.dumps({}), encoding="utf-8")


def _load_json_store() -> Dict[str, Dict[str, Any]]:
    if not JSON_PATH.exists():
        return {}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json_store(store: Dict[str, Dict[str, Any]]) -> None:
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)


def get_profile(user_id: str) -> Dict[str, Any]:
    """Retrieve a user profile dictionary.

    Returns an empty dict if the profile does not exist.
    """
    if _use_sqlite():
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cur = conn.cursor()
        cur.execute("SELECT profile_json FROM profiles WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        else:
            return {}
    else:
        store = _load_json_store()
        return store.get(user_id, {})


def update_profile(user_id: str, **fields: Any) -> None:
    """Create or update a user profile.

    Fields are merged into the existing profile (or a new one if none).
    """
    profile = get_profile(user_id)
    profile.update(fields)
    if _use_sqlite():
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO profiles (user_id, profile_json) VALUES (?, ?)",
            (user_id, json.dumps(profile)),
        )
        conn.commit()
        conn.close()
    else:
        store = _load_json_store()
        store[user_id] = profile
        _save_json_store(store)

# Initialize storage on import
init_db()

