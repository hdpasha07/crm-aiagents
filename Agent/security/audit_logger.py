import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# ── Constants ────────────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
AUDIT_LOG_FILE = LOG_DIR / "security_audit.jsonl"
MAX_LOG_BYTES = 10 * 1024 * 1024  # 10 MB rotation threshold

# Event type constants
EVENT_PII_DETECTED = "PII_DETECTED"
EVENT_INJECTION_BLOCKED = "INJECTION_BLOCKED"
EVENT_CLEAN_PASS = "CLEAN_PASS"


def _ensure_log_dir() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def _rotate_if_needed() -> None:
    """Rename the current log file to a timestamped archive if it exceeds MAX_LOG_BYTES."""
    if AUDIT_LOG_FILE.exists() and AUDIT_LOG_FILE.stat().st_size >= MAX_LOG_BYTES:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        archive = AUDIT_LOG_FILE.with_name(f"security_audit_{ts}.jsonl")
        AUDIT_LOG_FILE.rename(archive)


# ── SecurityAuditLogger ──────────────────────────────────────────────────────

class SecurityAuditLogger:
    """
    Writes structured JSONL audit records to logs/security_audit.jsonl.

    IMPORTANT: Only redacted text is ever written. Raw PII is never logged.
    Records include a UTC ISO-8601 timestamp, event type, redacted query,
    and relevant security metadata.
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or AUDIT_LOG_FILE
        _ensure_log_dir()

    def _write(self, record: dict) -> None:
        _rotate_if_needed()
        with open(self.log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log_clean_pass(
        self,
        redacted_query: str,
        pii_found: bool,
        entities_detected: Optional[List[dict]] = None,
    ) -> None:
        """
        Log a query that passed all security checks (PII already redacted).
        """
        entity_types = [e["entity_type"] for e in (entities_detected or [])]
        self._write({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": EVENT_PII_DETECTED if pii_found else EVENT_CLEAN_PASS,
            "redacted_query": redacted_query,
            "entities_detected": entity_types,
            "pii_count": len(entities_detected or []),
            "injection_blocked": False,
            "injection_threat_type": None,
            "injection_patterns": [],
        })

    def log_injection_blocked(
        self,
        redacted_query: str,
        threat_type: Optional[str],
        patterns_matched: List[str],
        cumulative_score: float,
    ) -> None:
        """
        Log a blocked injection attempt. Raw query is never passed here.
        """
        self._write({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": EVENT_INJECTION_BLOCKED,
            "redacted_query": redacted_query,
            "entities_detected": [],
            "pii_count": 0,
            "injection_blocked": True,
            "injection_threat_type": threat_type,
            "injection_patterns": patterns_matched,
            "injection_score": cumulative_score,
        })

    def read_recent(self, n: int = 20) -> List[dict]:
        """Return the last `n` audit records for inspection/testing."""
        if not self.log_file.exists():
            return []
        lines = self.log_file.read_text(encoding="utf-8").strip().splitlines()
        return [json.loads(line) for line in lines[-n:]]

