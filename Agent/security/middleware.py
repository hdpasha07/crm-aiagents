"""
Security Middleware Orchestrator
=================================
`SecurityMiddleware` is the single entrypoint that wraps `GeminiRAG`.
Every customer query is routed through three sequential gates before
it ever touches ChromaDB or the Gemini LLM:

  [1] PII Redaction  ─── Microsoft Presidio + supplemental regex
  [2] Injection Guard ── Weighted heuristic pattern scanner
  [3] Audit Logging  ── Structured JSONL, redacted text only

Usage (standalone):
    from Agent.security.middleware import SecurityMiddleware
    mw = SecurityMiddleware()
    result = mw.secure_query("What is the refund window?")
    print(result.answer or result.error)

Usage (decorator-style):
    @SecurityMiddleware.wrap
    def my_query_fn(query: str, **kwargs):
        ...
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .pii_redactor import PIIRedactor, RedactionResult
from .injection_guard import InjectionGuard, InjectionDetectionResult
from .audit_logger import SecurityAuditLogger


# ── Structured result ─────────────────────────────────────────────────────────

@dataclass
class SecureQueryResult:
    """Full output of the SecurityMiddleware pipeline."""
    # Security processing
    raw_query: str                      # Kept only in-memory; never logged
    redacted_query: str
    pii_found: bool
    entities_detected: List[dict] = field(default_factory=list)

    # Injection
    injection_blocked: bool = False
    injection_result: Optional[InjectionDetectionResult] = None

    # RAG answer (populated when not blocked)
    answer: Optional[str] = None
    rag_response: Optional[object] = None  # Holds the full RAGResponse object

    # Error surface (populated when blocked)
    error: Optional[str] = None
    blocked: bool = False

    @property
    def redaction_summary(self) -> str:
        if not self.entities_detected:
            return "No PII detected."
        from collections import Counter
        c = Counter(e["entity_type"] for e in self.entities_detected)
        return "PII redacted: " + ", ".join(f"{et}x{n}" for et, n in sorted(c.items()))


# ── SecurityMiddleware ────────────────────────────────────────────────────────

class SecurityMiddleware:
    """
    Pre-execution security gate for the Enterprise Customer Support RAG Agent.

    Instantiate once and call `.secure_query(raw_input)` for every user request.
    The RAG engine is initialised lazily on first use to avoid cold-start cost
    during testing of the security layer alone.
    """

    _BLOCKED_RESPONSE = (
        "For your security and safety, this request cannot be processed as submitted. "
        "Please let us know how we can assist you with your order."
    )

    def __init__(
        self,
        pii_redactor: Optional[PIIRedactor] = None,
        injection_guard: Optional[InjectionGuard] = None,
        audit_logger: Optional[SecurityAuditLogger] = None,
        rag_engine: Optional[object] = None,  # GeminiRAG
        lazy_rag: bool = True,
    ):
        self.pii_redactor = pii_redactor or PIIRedactor()
        self.injection_guard = injection_guard or InjectionGuard()
        self.audit_logger = audit_logger or SecurityAuditLogger()
        self._rag_engine = rag_engine
        self._lazy_rag = lazy_rag

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _get_rag_engine(self):
        """Lazily initialise GeminiRAG to avoid import cost during security-only tests."""
        if self._rag_engine is None:
            from Agent.rag.llm_rag import GeminiRAG
            self._rag_engine = GeminiRAG()
        return self._rag_engine

    # ── Primary entrypoint ────────────────────────────────────────────────────

    def secure_query(
        self,
        raw_input: str,
        top_k: int = 4,
        run_rag: bool = True,
    ) -> SecureQueryResult:
        """
        Route a raw customer query through all security gates before RAG.

        Pipeline:
          1. PII Redaction  → replace sensitive data with placeholders
          2. Injection Guard → block malicious instruction overrides
          3. Audit Logging  → write JSONL record (redacted text only)
          4. RAG Generation → call GeminiRAG with clean, redacted query

        Args:
            raw_input: The unprocessed customer message (may contain PII).
            top_k: Number of ChromaDB chunks to retrieve for RAG.
            run_rag: Set False to skip RAG (useful for security-only unit tests).

        Returns:
            SecureQueryResult with answer, PII metadata, and security flags.
        """
        # ── Gate 1: PII Redaction ─────────────────────────────────────────────
        redaction: RedactionResult = self.pii_redactor.redact(raw_input)

        partial_result = SecureQueryResult(
            raw_query=raw_input,  # In-memory only — never written to disk
            redacted_query=redaction.redacted_text,
            pii_found=redaction.pii_found,
            entities_detected=redaction.entities_detected,
        )

        # ── Gate 2: Prompt Injection Scan (on redacted text) ──────────────────
        injection: InjectionDetectionResult = self.injection_guard.scan(
            redaction.redacted_text
        )

        if injection.blocked:
            self.audit_logger.log_injection_blocked(
                redacted_query=redaction.redacted_text,
                threat_type=injection.threat_type,
                patterns_matched=injection.patterns_matched,
                cumulative_score=injection.cumulative_score,
            )
            partial_result.injection_blocked = True
            partial_result.injection_result = injection
            partial_result.blocked = True
            partial_result.error = self._BLOCKED_RESPONSE
            return partial_result

        # ── Gate 3: Audit log (clean pass — PII already stripped) ─────────────
        self.audit_logger.log_clean_pass(
            redacted_query=redaction.redacted_text,
            pii_found=redaction.pii_found,
            entities_detected=redaction.entities_detected,
        )
        partial_result.injection_result = injection

        # ── Gate 4: RAG Generation ─────────────────────────────────────────────
        if not run_rag:
            return partial_result

        try:
            rag_engine = self._get_rag_engine()
            rag_response = rag_engine.generate_grounded_response(
                query=redaction.redacted_text,
                top_k=top_k,
                customer_facing=True,
            )
            partial_result.rag_response = rag_response
            partial_result.answer = rag_response.answer
        except Exception as exc:
            partial_result.error = f"RAG generation error: {exc}"

        return partial_result

    # ── Decorator factory ─────────────────────────────────────────────────────

    @staticmethod
    def wrap(
        fn: Optional[Callable] = None,
        *,
        middleware_instance: Optional["SecurityMiddleware"] = None,
    ):
        """
        Decorator that wraps any function whose first positional argument is a
        query string. The query is intercepted, secured, and replaced before
        the original function is called.
        """
        mw = middleware_instance or SecurityMiddleware()

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(raw_query: str, *args, **kwargs):
                result = mw.secure_query(raw_query, run_rag=False)
                if result.blocked:
                    return result.error
                return f(result.redacted_query, *args, **kwargs)
            return wrapper

        if fn is not None:
            return decorator(fn)
        return decorator
