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

# Active interceptor regex patterns for sensitive card numbers and CVVs
CARD_NUMBER_REGEX = re.compile(r"\b(?:\d[ -]?){11,18}\d\b")
CVV_REGEX = re.compile(r"\b(?:cvv|cvc|cid|security code)[:\s]+(\d{3,4})\b", re.IGNORECASE)


# ── Supplemental regex recognisers (fill Presidio blind spots) ───────────────

def _build_credit_card_recognizer() -> PatternRecognizer:
    """Supplemental recogniser — catches common card formats including unformatted 12-16 digits."""
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
        # 12-16 digit continuous card numbers
        Pattern(
            name="credit_card_unformatted",
            regex=r"\b\d{12,19}\b",
            score=0.85,
        ),
        Pattern(
            name="credit_card_flexible",
            regex=r"\b(?:\d[ -]?){11,18}\d\b",
            score=0.85,
        ),
    ]
    return PatternRecognizer(
        supported_entity="CREDIT_CARD",
        patterns=patterns,
        context=["card", "credit", "debit", "visa", "mastercard", "amex", "charged", "payment", "number", "account"],
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
    Wraps Microsoft Presidio Analyzer + Anonymizer with active pre-masking.
    Interception actively masks 12-16 digit card numbers and sensitive numbers
    before evaluating prompt intent, replacing them with <CREDIT_CARD>.
    """

    def __init__(
        self,
        entities: Optional[List[str]] = None,
        score_threshold: float = 0.4,
    ):
        self.entities = entities or DEFAULT_ENTITIES
        self.score_threshold = score_threshold

        try:
            self.analyzer = AnalyzerEngine()
            self.analyzer.registry.add_recognizer(_build_credit_card_recognizer())
            self.analyzer.registry.add_recognizer(_build_ssn_recognizer())
            self.anonymizer = AnonymizerEngine()
            self._operators = {
                entity: OperatorConfig("replace", {"new_value": placeholder})
                for entity, placeholder in PLACEHOLDER_MAP.items()
            }
        except Exception as e:
            print(f"Warning: Presidio initialization exception: {e}")
            self.analyzer = None
            self.anonymizer = None
            self._operators = {}

    def redact(self, text: str) -> RedactionResult:
        """
        Scan `text` for sensitive financial PII (actively masking 12-16 digit cards)
        and other PII entities, replacing them with labelled placeholders.
        """
        if not text or not text.strip():
            return RedactionResult(redacted_text=text)

        entities_detected: List[Dict] = []
        pii_found = False

        # Active Interception: mask sensitive 12-16 digit card numbers first
        def mask_card_match(match: re.Match) -> str:
            val = match.group(0)
            digits = re.sub(r"\D", "", val)
            if 12 <= len(digits) <= 19:
                entities_detected.append({
                    "entity_type": "CREDIT_CARD",
                    "score": 1.0,
                    "start": match.start(),
                    "end": match.end(),
                })
                return "<CREDIT_CARD>"
            return val

        active_masked_text = CARD_NUMBER_REGEX.sub(mask_card_match, text)

        # Also mask CVV if present
        def mask_cvv_match(match: re.Match) -> str:
            entities_detected.append({
                "entity_type": "CVV",
                "score": 0.95,
                "start": match.start(),
                "end": match.end(),
            })
            return "CVV <CVV>"

        active_masked_text = CVV_REGEX.sub(mask_cvv_match, active_masked_text)

        if entities_detected:
            pii_found = True

        # Run Presidio on active_masked_text to catch additional entities (SSN, emails, names, phones)
        if self.analyzer and self.anonymizer:
            try:
                analyzer_results = self.analyzer.analyze(
                    text=active_masked_text,
                    entities=self.entities,
                    language="en",
                    score_threshold=self.score_threshold,
                )

                if analyzer_results:
                    pii_found = True
                    for r in analyzer_results:
                        entities_detected.append({
                            "entity_type": r.entity_type,
                            "score": round(r.score, 3),
                            "start": r.start,
                            "end": r.end,
                        })

                    anonymized = self.anonymizer.anonymize(
                        text=active_masked_text,
                        analyzer_results=analyzer_results,
                        operators=self._operators,
                    )
                    active_masked_text = anonymized.text
            except Exception as e:
                print(f"Warning: Presidio analyze failed: {e}")

        return RedactionResult(
            redacted_text=active_masked_text,
            entities_detected=entities_detected,
            pii_found=pii_found,
        )
