import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ── Injection pattern library ────────────────────────────────────────────────
# Each entry: (compiled_regex, human_label, threat_score)
# Cumulative threat score >= BLOCK_THRESHOLD → request is blocked.

BLOCK_THRESHOLD: float = 0.6

_RAW_PATTERNS: List[Tuple[str, str, float]] = [
    # Direct instruction override
    (r"ignore\s+(previous|prior|all|above|system)\s+(instructions?|rules?|prompts?|directives?|context)",
     "INSTRUCTION_OVERRIDE", 0.9),
    (r"disregard\s+(all|previous|prior|the|any)\s+(instructions?|rules?|context|prompt)",
     "INSTRUCTION_OVERRIDE", 0.9),
    (r"forget\s+(everything|all|previous|prior|your\s+instructions?|your\s+rules?)",
     "INSTRUCTION_OVERRIDE", 0.8),
    (r"override\s+(your|the|all|previous)\s+(instructions?|rules?|constraints?|system)",
     "INSTRUCTION_OVERRIDE", 0.9),

    # Persona / mode hijack
    (r"you\s+(are\s+now|will\s+now\s+act\s+as|must\s+act\s+as|should\s+act\s+as)\s+.{0,60}",
     "PERSONA_HIJACK", 0.8),
    (r"act\s+as\s+(if\s+you\s+are|a\s+different|an?\s+unrestricted|a\s+new)",
     "PERSONA_HIJACK", 0.8),
    (r"\bDAN\b.*mode|\bDAN\s+mode\b|do\s+anything\s+now",
     "DAN_MODE", 0.95),
    (r"pretend\s+(you\s+are|you're|that\s+you\s+are|to\s+be)\s+.{0,60}",
     "PERSONA_HIJACK", 0.7),
    (r"new\s+persona|adopt\s+a\s+persona|switch\s+persona",
     "PERSONA_HIJACK", 0.7),

    # Jailbreak / bypass keywords
    (r"\bjailbreak\b|\buncensored\b|\bunfiltered\b|\bunrestricted\s+mode\b",
     "JAILBREAK_KEYWORD", 0.85),
    (r"bypass\s+(your|the|all|safety|content|filter|restriction|guardrail)",
     "BYPASS_ATTEMPT", 0.85),

    # System prompt / context exfiltration
    (r"(show|reveal|print|display|output|repeat|tell\s+me)\s+(your|the)\s+(system\s+prompt|instructions?|rules?|guidelines?|context)",
     "PROMPT_EXFILTRATION", 0.9),
    (r"what\s+(are|is)\s+your\s+(system\s+prompt|instructions?|initial\s+instructions?)",
     "PROMPT_EXFILTRATION", 0.8),

    # Structural injection markers (common in embedded attacks)
    (r"<<SYS>>|<</SYS>>|\[INST\]|\[/INST\]|<\|system\|>|<\|user\|>|<\|assistant\|>",
     "STRUCTURAL_INJECTION", 0.95),
    (r"###\s*System\s*:|###\s*Instruction\s*:|###\s*Override\s*:|SYSTEM\s*PROMPT\s*:",
     "STRUCTURAL_INJECTION", 0.85),

    # Role reversal
    (r"(you|your)\s+(real|true|actual|hidden|secret)\s+(purpose|goal|mission|instructions?)",
     "ROLE_REVERSAL", 0.75),

    # "Translate to X then do Y" encoding attacks
    (r"translate\s+.{0,40}(ignore|override|disregard|bypass)",
     "ENCODING_ATTACK", 0.8),

    # Continuation attacks: "Repeat the above", "Continue from"
    (r"repeat\s+(the\s+above|everything\s+above|your\s+previous)",
     "CONTINUATION_ATTACK", 0.6),
]

# Compile all patterns once at module load
INJECTION_PATTERNS: List[Tuple[re.Pattern, str, float]] = [
    (re.compile(raw, re.IGNORECASE | re.DOTALL), label, score)
    for raw, label, score in _RAW_PATTERNS
]


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class InjectionDetectionResult:
    """Describes whether a query contains prompt injection attempts."""
    blocked: bool
    threat_type: Optional[str] = None
    patterns_matched: List[str] = field(default_factory=list)
    cumulative_score: float = 0.0
    safe_message: str = ""

    @property
    def block_reason(self) -> str:
        if not self.blocked:
            return ""
        matched = ", ".join(self.patterns_matched) if self.patterns_matched else "UNKNOWN"
        return (
            f"[SECURITY] Request blocked — prompt injection detected. "
            f"Threat type: {self.threat_type}. "
            f"Patterns: {matched}. "
            f"Score: {self.cumulative_score:.2f} (threshold: {BLOCK_THRESHOLD})."
        )


# ── InjectionGuard ───────────────────────────────────────────────────────────

class InjectionGuard:
    """
    Lightweight prompt injection defense using weighted heuristic pattern matching.
    Evaluates a cumulative threat score; if it exceeds BLOCK_THRESHOLD the query
    is blocked and a structured InjectionDetectionResult is returned.
    """

    def __init__(self, threshold: float = BLOCK_THRESHOLD):
        self.threshold = threshold

    def scan(self, text: str) -> InjectionDetectionResult:
        """
        Scan `text` for prompt injection patterns.

        Args:
            text: The (already PII-redacted) query string.

        Returns:
            InjectionDetectionResult with blocked flag and matched pattern details.
        """
        if not text or not text.strip():
            return InjectionDetectionResult(blocked=False, cumulative_score=0.0)

        cumulative_score: float = 0.0
        patterns_matched: List[str] = []
        dominant_threat: Optional[str] = None
        highest_score: float = 0.0

        for pattern, label, score in INJECTION_PATTERNS:
            if pattern.search(text):
                patterns_matched.append(label)
                cumulative_score += score
                if score > highest_score:
                    highest_score = score
                    dominant_threat = label

        blocked = cumulative_score >= self.threshold

        if blocked:
            safe_msg = (
                "I'm sorry, but your request has been flagged by our security system. "
                "Please rephrase your question or contact a human support agent if you "
                "believe this is a mistake."
            )
        else:
            safe_msg = ""

        return InjectionDetectionResult(
            blocked=blocked,
            threat_type=dominant_threat if blocked else None,
            patterns_matched=patterns_matched if blocked else [],
            cumulative_score=round(cumulative_score, 3),
            safe_message=safe_msg,
        )

