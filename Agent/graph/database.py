"""
Customer Profile & Episodic Memory Database (SQLite Persistence Layer)
====================================================================
Normalized SQLite persistence supporting continuous episodic memory:
- `Users`: user_id, name, tier, learned_preferences (JSON text), email, current_shipping_address.
- `Active_State`: user_id, recent_order_id, open_ticket_status.
- `Resolution_Log`: id, user_id, issue_summary, successful_solution, timestamp.
- `customer_profiles`: Backwards-compatible consolidated profile cache.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "customer_profiles.db"


class CustomerProfileDB:
    """Persistent SQLite database manager for customer profiles and episodic memory."""

    def __init__(self, db_path: Optional[str | Path] = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create normalized episodic memory tables if they do not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Normalized Users table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    tier TEXT DEFAULT 'Standard',
                    learned_preferences TEXT DEFAULT '{}',
                    email TEXT,
                    current_shipping_address TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # 2. Normalized Active_State table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Active_State (
                    user_id TEXT PRIMARY KEY,
                    recent_order_id TEXT,
                    open_ticket_status TEXT DEFAULT 'none',
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES Users(user_id)
                )
                """
            )

            # 3. Normalized Resolution_Log table (Continuous Episodic Memory)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS Resolution_Log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    issue_summary TEXT NOT NULL,
                    successful_solution TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES Users(user_id)
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_resolution_user ON Resolution_Log(user_id)"
            )

            # 4. Backwards-compatible consolidated customer_profiles table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS customer_profiles (
                    customer_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    current_shipping_address TEXT NOT NULL,
                    tier TEXT DEFAULT 'Standard',
                    order_history TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_customer_email ON customer_profiles(email)"
            )

            conn.commit()

    # ── Users & Learned Preferences ──────────────────────────────────────────

    def save_user_preference(
        self,
        user_id: str,
        preference_text: str,
        category: str = "general",
    ) -> Dict[str, Any]:
        """
        Record an extracted user preference into the Users.learned_preferences JSON field.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT learned_preferences FROM Users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                # If user not in Users table, insert a base record
                cursor.execute(
                    """
                    INSERT INTO Users (user_id, name, tier, learned_preferences, created_at, updated_at)
                    VALUES (?, ?, 'Standard', '{}', ?, ?)
                    """,
                    (user_id, user_id, now_iso, now_iso),
                )
                prefs = {}
            else:
                try:
                    prefs = json.loads(row["learned_preferences"] or "{}")
                except Exception:
                    prefs = {}

            # Append or update preference list
            if "preferences" not in prefs or not isinstance(prefs["preferences"], list):
                prefs["preferences"] = []

            pref_entry = {
                "category": category,
                "preference": preference_text.strip(),
                "learned_at": now_iso,
            }
            # Avoid direct duplicate entries
            if not any(p.get("preference") == preference_text.strip() for p in prefs["preferences"]):
                prefs["preferences"].append(pref_entry)

            prefs["last_updated"] = now_iso
            updated_json = json.dumps(prefs)

            cursor.execute(
                "UPDATE Users SET learned_preferences = ?, updated_at = ? WHERE user_id = ?",
                (updated_json, now_iso, user_id),
            )
            conn.commit()

        return {
            "user_id": user_id,
            "preference": preference_text,
            "category": category,
            "all_preferences": prefs.get("preferences", []),
            "updated_at": now_iso,
        }

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieve the learned preferences dictionary for a user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT learned_preferences FROM Users WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return {}
            try:
                return json.loads(row["learned_preferences"] or "{}")
            except Exception:
                return {}

    # ── Active State ──────────────────────────────────────────────────────────

    def get_active_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve active session state (recent order ID, open ticket status)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, recent_order_id, open_ticket_status, updated_at FROM Active_State WHERE user_id = ?",
                (user_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_active_state(
        self,
        user_id: str,
        recent_order_id: Optional[str] = None,
        open_ticket_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update or insert active state record for a user."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT recent_order_id, open_ticket_status FROM Active_State WHERE user_id = ?",
                (user_id,),
            )
            existing = cursor.fetchone()
            new_order_id = recent_order_id if recent_order_id is not None else (existing["recent_order_id"] if existing else None)
            new_ticket_status = open_ticket_status if open_ticket_status is not None else (existing["open_ticket_status"] if existing else "none")

            cursor.execute(
                """
                INSERT INTO Active_State (user_id, recent_order_id, open_ticket_status, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    recent_order_id = excluded.recent_order_id,
                    open_ticket_status = excluded.open_ticket_status,
                    updated_at = excluded.updated_at
                """,
                (user_id, new_order_id, new_ticket_status, now_iso),
            )
            conn.commit()

        return {
            "user_id": user_id,
            "recent_order_id": new_order_id,
            "open_ticket_status": new_ticket_status,
            "updated_at": now_iso,
        }

    # ── Resolution Log (Episodic Memory) ──────────────────────────────────────

    def log_resolution(
        self,
        user_id: str,
        issue_summary: str,
        successful_solution: str,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a successfully resolved problem into the normalized Resolution_Log table.
        Also marks active ticket status as 'resolved'.
        """
        now_iso = timestamp or datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO Resolution_Log (user_id, issue_summary, successful_solution, timestamp)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, issue_summary.strip(), successful_solution.strip(), now_iso),
            )
            inserted_id = cursor.lastrowid

            # Update active ticket status
            cursor.execute(
                """
                INSERT INTO Active_State (user_id, open_ticket_status, updated_at)
                VALUES (?, 'resolved', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    open_ticket_status = 'resolved',
                    updated_at = excluded.updated_at
                """,
                (user_id, now_iso),
            )
            conn.commit()

        return {
            "id": inserted_id,
            "user_id": user_id,
            "issue_summary": issue_summary.strip(),
            "successful_solution": successful_solution.strip(),
            "timestamp": now_iso,
            "status": "logged_to_sqlite",
        }

    def get_resolution_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent resolution logs for a specific user."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, user_id, issue_summary, successful_solution, timestamp
                FROM Resolution_Log
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    # ── Consolidated Profile & Legacy Compatibility ──────────────────────────

    def get_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve combined customer profile, merging customer_profiles, Users,
        Active_State, and recent resolutions.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT customer_id, name, email, current_shipping_address, tier, order_history, created_at, updated_at
                FROM customer_profiles
                WHERE customer_id = ?
                """,
                (customer_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None

            data = dict(row)
            try:
                data["order_history"] = json.loads(data.get("order_history") or "[]")
            except Exception:
                data["order_history"] = []

            # Merge learned preferences from Users table
            data["learned_preferences"] = self.get_user_preferences(customer_id)

            # Merge active state
            state = self.get_active_state(customer_id)
            if state:
                data["recent_order_id"] = state.get("recent_order_id")
                data["open_ticket_status"] = state.get("open_ticket_status")
            else:
                data["recent_order_id"] = None
                data["open_ticket_status"] = "none"

            # Attach latest resolution if present
            recent_res = self.get_resolution_history(customer_id, limit=3)
            data["recent_resolutions"] = recent_res

            return data

    def update_profile_field(
        self,
        customer_id: str,
        key: str,
        value: Any,
    ) -> Dict[str, Any]:
        """Update or overwrite a profile field across both customer_profiles and Users."""
        field_alias_map = {
            "address": "current_shipping_address",
            "shipping_address": "current_shipping_address",
            "shipping": "current_shipping_address",
            "current_shipping_address": "current_shipping_address",
            "name": "name",
            "email": "email",
            "tier": "tier",
            "customer_tier": "tier",
            "order_history": "order_history",
        }

        target_field = field_alias_map.get(key.lower().strip(), key.strip())
        existing = self.get_profile(customer_id)
        if not existing:
            raise ValueError(f"Customer '{customer_id}' not found in database.")

        now_iso = datetime.now(timezone.utc).isoformat()

        if target_field == "order_history" and isinstance(value, (list, dict)):
            serialized_value = json.dumps(value)
        else:
            serialized_value = str(value)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE customer_profiles
                SET {target_field} = ?, updated_at = ?
                WHERE customer_id = ?
                """,
                (serialized_value, now_iso, customer_id),
            )

            # Also update Users table if field exists there
            if target_field in ("name", "email", "tier", "current_shipping_address"):
                cursor.execute(
                    f"""
                    UPDATE Users
                    SET {target_field} = ?, updated_at = ?
                    WHERE user_id = ?
                    """,
                    (serialized_value, now_iso, customer_id),
                )

            conn.commit()

        updated = self.get_profile(customer_id)
        return {
            "success": True,
            "customer_id": customer_id,
            "field": target_field,
            "previous_value": existing.get(target_field),
            "new_value": updated.get(target_field) if updated else serialized_value,
            "updated_at": now_iso,
        }

    def upsert_profile(
        self,
        customer_id: str,
        name: str,
        current_shipping_address: str,
        email: Optional[str] = None,
        tier: str = "Standard",
        order_history: Optional[List[Dict[str, Any]]] = None,
        learned_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Insert or replace customer record across customer_profiles, Users, and Active_State."""
        now_iso = datetime.now(timezone.utc).isoformat()
        orders_json = json.dumps(order_history or [])
        prefs_json = json.dumps(learned_preferences or {})

        recent_oid = order_history[0].get("order_id") if order_history else None

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Upsert customer_profiles
            cursor.execute(
                """
                INSERT INTO customer_profiles (
                    customer_id, name, email, current_shipping_address, tier, order_history, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id) DO UPDATE SET
                    name = excluded.name,
                    email = excluded.email,
                    current_shipping_address = excluded.current_shipping_address,
                    tier = excluded.tier,
                    order_history = excluded.order_history,
                    updated_at = excluded.updated_at
                """,
                (customer_id, name, email, current_shipping_address, tier, orders_json, now_iso, now_iso),
            )

            # Upsert Users table
            cursor.execute(
                """
                INSERT INTO Users (
                    user_id, name, tier, learned_preferences, email, current_shipping_address, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name = excluded.name,
                    tier = excluded.tier,
                    email = excluded.email,
                    current_shipping_address = excluded.current_shipping_address,
                    updated_at = excluded.updated_at
                """,
                (customer_id, name, tier, prefs_json, email, current_shipping_address, now_iso, now_iso),
            )

            # Upsert Active_State
            cursor.execute(
                """
                INSERT INTO Active_State (user_id, recent_order_id, open_ticket_status, updated_at)
                VALUES (?, ?, 'none', ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    recent_order_id = excluded.recent_order_id,
                    updated_at = excluded.updated_at
                """,
                (customer_id, recent_oid, now_iso),
            )

            conn.commit()

        return self.get_profile(customer_id) or {}

    def seed_sample_profiles(self) -> None:
        """Seed initial normalized customer profiles with preferences and active orders."""
        sample_customers = [
            {
                "customer_id": "CUST-1001",
                "name": "Alex Mercer",
                "email": "alex.mercer@example.com",
                "current_shipping_address": "123 Old Oak Street, Apt 4B, Seattle, WA 98101",
                "tier": "Gold",
                "learned_preferences": {
                    "preferences": [
                        {
                            "category": "support",
                            "preference": "Prefers concise, step-by-step technical instructions",
                            "learned_at": "2026-10-01T12:00:00Z",
                        }
                    ]
                },
                "order_history": [
                    {
                        "order_id": "ORD-9821",
                        "date": "2026-10-05",
                        "status": "In Transit",
                        "carrier": "FedEx",
                        "tracking_number": "FX-883920194",
                        "items": ["Ergonomic Mechanical Keyboard", "USB-C Hub 7-in-1"],
                        "total_usd": 189.50,
                        "estimated_delivery": "2026-10-15",
                    },
                    {
                        "order_id": "ORD-7712",
                        "date": "2026-09-12",
                        "status": "Delivered",
                        "carrier": "UPS",
                        "tracking_number": "1Z999AA10123456784",
                        "items": ["UltraWide 34-inch Monitor"],
                        "total_usd": 499.00,
                        "estimated_delivery": "2026-09-16",
                    },
                ],
            },
            {
                "customer_id": "CUST-2002",
                "name": "Sarah Connor",
                "email": "sarah.connor@cyberdyne.org",
                "current_shipping_address": "450 Bunker Hill Rd, Los Angeles, CA 90012",
                "tier": "Platinum VIP",
                "learned_preferences": {
                    "preferences": [
                        {
                            "category": "security",
                            "preference": "High security alert profile",
                            "learned_at": "2026-10-02T08:00:00Z",
                        }
                    ]
                },
                "order_history": [
                    {
                        "order_id": "ORD-4490",
                        "date": "2026-10-09",
                        "status": "Processing",
                        "carrier": "DHL Express",
                        "tracking_number": "DHL-55201948",
                        "items": ["Reinforced Titanium Laptop Case"],
                        "total_usd": 320.00,
                        "estimated_delivery": "2026-10-14",
                    }
                ],
            },
        ]

        for cust in sample_customers:
            self.upsert_profile(**cust)

    def reset_db(self) -> None:
        """Drop all normalized tables and recreate cleanly."""
        with self._get_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS Resolution_Log")
            conn.execute("DROP TABLE IF EXISTS Active_State")
            conn.execute("DROP TABLE IF EXISTS Users")
            conn.execute("DROP TABLE IF EXISTS customer_profiles")
            conn.commit()
        self.init_db()


_db_instance: Optional[CustomerProfileDB] = None


def get_db(db_path: Optional[str | Path] = None) -> CustomerProfileDB:
    global _db_instance
    if _db_instance is None or db_path is not None:
        _db_instance = CustomerProfileDB(db_path)
    return _db_instance
