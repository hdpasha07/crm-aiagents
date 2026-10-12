"""
Agent Security Subsystem
========================
Pre-execution security middleware for the Enterprise Customer Support Agent.

Components:
  - PIIRedactor       : Presidio-backed PII detection and placeholder substitution
  - InjectionGuard    : Weighted heuristic prompt injection / jailbreak scanner
  - SecurityAuditLogger : Structured JSONL audit logging (no raw PII on disk)
  - SecurityMiddleware  : Orchestration wrapper / decorator
  - SecureQueryResult   : Typed result dataclass
"""

from .pii_redactor import PIIRedactor, RedactionResult, DEFAULT_ENTITIES, PLACEHOLDER_MAP
from .injection_guard import InjectionGuard, InjectionDetectionResult, BLOCK_THRESHOLD
from .audit_logger import SecurityAuditLogger, EVENT_CLEAN_PASS, EVENT_PII_DETECTED, EVENT_INJECTION_BLOCKED
from .middleware import SecurityMiddleware, SecureQueryResult

__all__ = [
    # PII
    "PIIRedactor",
    "RedactionResult",
    "DEFAULT_ENTITIES",
    "PLACEHOLDER_MAP",
    # Injection
    "InjectionGuard",
    "InjectionDetectionResult",
    "BLOCK_THRESHOLD",
    # Logging
    "SecurityAuditLogger",
    "EVENT_CLEAN_PASS",
    "EVENT_PII_DETECTED",
    "EVENT_INJECTION_BLOCKED",
    # Middleware
    "SecurityMiddleware",
    "SecureQueryResult",
]

