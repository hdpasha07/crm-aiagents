import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


# ── Placeholder labels ──────────────────────────────────────────────────────
PLACEHOLDER_MAP: Dict[str, str] = {
    "CREDIT_CARD":       "<CREDIT_CARD>",
    "PHONE_NUMBER":      "<PHONE_NUMBER>",
    "EMAIL_ADDRESS":     "<EMAIL_ADDRESS>",
    "US_SSN":            "<US_SSN>",
    "PERSON":            "<PERSON>",
    "US_BANK_NUMBER":    "<US_BANK_NUMBER>",
    "US_ITIN":           "<US_ITIN>",
    "IBAN_CODE":         "<IBAN_CODE>",
    "CRYPTO":            "<CRYPTO_ADDRESS>",
    "IP_ADDRESS":        "<IP_ADDRESS>",
    "US_PASSPORT":       "<US_PASSPORT>",
    "MEDICAL_LICENSE":   "<MEDICAL_LICENSE>",
    "DATE_TIME":         "<DATE_TIME>",
}

# Entities that Presidio's regex/spaCy recognisers handle well.
# DATE_TIME is intentionally excluded from default scan to avoid over-redaction on
# support queries referencing order dates.
DEFAULT_ENTITIES = [
    "CREDIT_CARD",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "US_SSN",
    "PERSON",
    "US_BANK_NUMBER",
    "US_ITIN",
    "IBAN_CODE",
    "CRYPTO",
    "IP_ADDRESS",
    "US_PASSPORT",
]


# ── Supplemental regex recognisers (fill Presidio blind spots) ───────────────

def _build_credit_card_recognizer() -> PatternRecognizer:
    """Supplemental recogniser — catches common card formats that Presidio misses."""
    patterns = [
        # 16-digit cards with spaces, dashes, or unformatted
        Pattern(
            name="credit_card_dashes_spaces",
            regex=r"\b(?:\d{4}[\s\-]){3}\d{4}\b",
            score=0.85,
        ),
        # Amex 15-digit
        Pattern(
            name="credit_card_amex",
            regex=r"\b3[47]\d{2}[\s\-]\d{6}[\s\-]\d{5}\b",
            score=0.85,
        ),
    ]
    return PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=patterns,
        context=["card", "credit", "debit", "visa", "mastercard", "amex", "charged"],
    )


def _build_ssn_recognizer() -> PatternRecognizer:
    """Supplemental SSN recogniser for strict NNN-NN-NNNN format."""
    return PatternRecognizer(
        supported_entity="US_SSN",
        patterns=[
            Pattern(
                name="us_ssn_dashes",
                regex=r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b",
                score=0.85,
            )
        ],
        context=["ssn", "social security", "social", "taxpayer"],
    )


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class RedactionResult:
    """Holds the outcome of a PII redaction pass."""
    redacted_text: str
    entities_detected: List[Dict] = field(default_factory=list)
    pii_found: bool = False

    def summary(self) -> str:
        if not self.entities_detected:
            return "No PII detected."
        counts: Dict[str, int] = {}
        for e in self.entities_detected:
            counts[e["entity_type"]] = counts.get(e["entity_type"], 0) + 1
        parts = [f"{et}×{n}" for et, n in sorted(counts.items())]
        return "PII detected: " + ", ".join(parts)


# ── PIIRedactor ──────────────────────────────────────────────────────────────

class PIIRedactor:
    """
    Wraps Microsoft Presidio Analyzer + Anonymizer.
    Augments built-in recognisers with extra regex patterns for credit cards and SSNs.
    Replaces all detected PII with labelled placeholders (e.g. <CREDIT_CARD>).
    """

    def __init__(
        self,
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.4,
    ):
        self.entities = entities or DEFAULT_ENTITIES
        self.score_threshold = score_threshold

        self.analyzer = AnalyzerEngine()
        # Register supplemental recognisers
        self.analyzer.registry.add_recognizer(_build_credit_card_recognizer())
        self.analyzer.registry.add_recognizer(_build_ssn_recognizer())

        self.anonymizer = AnonymizerEngine()

        # Build operator map: each entity gets a labelled replacement
        self._operators = {
            entity: OperatorConfig("replace", {"new_value": placeholder})
            for entity, placeholder in PLACEHOLDER_MAP.items()
        }

    def redact(self, text: str) -> RedactionResult:
        """
        Scan `text` for PII and replace with placeholders.

        Args:
            text: Raw input from the customer.

        Returns:
            RedactionResult with redacted text and entity metadata.
        """
        if not text or not text.strip():
            return RedactionResult(redacted_text=text)

        analyzer_results = self.analyzer.analyze(
            text=text,
            entities=self.entities,
            language="en",
            score_threshold=self.score_threshold,
        )

        if not analyzer_results:
            return RedactionResult(redacted_text=text, pii_found=False)

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=analyzer_results,
            operators=self._operators,
        )

        entities_meta = [
            {
                "entity_type": r.entity_type,
                "score": round(r.score, 3),
                "start": r.start,
                "end": r.end,
            }
            for r in analyzer_results
        ]

        return RedactionResult(
            redacted_text=anonymized.text,
            entities_detected=entities_meta,
            pii_found=True,
        )

