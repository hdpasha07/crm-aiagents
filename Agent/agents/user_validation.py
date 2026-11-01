import re
from typing import Dict, Any
from ..utils.db_mock import get_user_profile 
from Agent.security.pii_redactor import PIIRedactor
from Agent.security.injection_guard import InjectionGuard
from .validation import validate_complaint

pii_redactor = PIIRedactor()
injection_guard = InjectionGuard()

POLITE_PII_MESSAGE = (
    "For your security, please do not share financial information here. "
    "How can I assist you with your order?"
)

POLITE_NON_CONTEXTUAL_MESSAGE = (
    "We can only assist with e-commerce and order-related inquiries (such as order status, delivery, refunds, payments, and product questions). "
    "Please let us know how we can assist you with your order."
)

POLITE_SECURITY_MESSAGE = (
    "For your security and safety, this request cannot be processed as submitted. "
    "Please let us know how we can assist you with your order."
)


def validate_and_guardrail(complaint_text: str) -> Dict[str, Any]:
    """
    Actively masks sensitive numbers (12-16 digit cards) first,
    checks security guardrails (injection and PII-only inputs),
    and validates e-commerce context, overwriting any system reasons with polite customer-facing messages.
    """
    raw_text = (complaint_text or "").strip()
    if not raw_text:
        return {
            "is_valid": False,
            "guardrail_triggered": True,
            "guardrail_type": "empty",
            "reason": POLITE_NON_CONTEXTUAL_MESSAGE,
            "redacted_text": raw_text,
        }

    # 1. PII Redactor: Active masking of sensitive card numbers and PII
    redaction = pii_redactor.redact(raw_text)
    masked_text = redaction.redacted_text

    # 2. Injection Guard
    injection = injection_guard.scan(masked_text)
    if injection.blocked:
        return {
            "is_valid": False,
            "guardrail_triggered": True,
            "guardrail_type": "injection",
            "reason": POLITE_SECURITY_MESSAGE,
            "redacted_text": masked_text,
        }

    # 3. Check if input is exclusively sensitive financial information without an inquiry
    if redaction.pii_found:
        remaining_text = re.sub(r"<[A-Z_]+>", "", masked_text)
        substantive_words = [w for w in re.findall(r"\b[A-Za-z]{2,}\b", remaining_text)]
        has_card = any(e.get("entity_type") in ("CREDIT_CARD", "CVV", "US_BANK_NUMBER") for e in redaction.entities_detected)
        if has_card and len(substantive_words) < 3:
            return {
                "is_valid": False,
                "guardrail_triggered": True,
                "guardrail_type": "pii_financial",
                "reason": POLITE_PII_MESSAGE,
                "redacted_text": masked_text,
            }

    # 4. Context validation on safely masked text
    try:
        val_output = validate_complaint(masked_text)
        if not val_output.is_valid:
            return {
                "is_valid": False,
                "guardrail_triggered": True,
                "guardrail_type": "non_contextual",
                "reason": POLITE_NON_CONTEXTUAL_MESSAGE,
                "redacted_text": masked_text,
            }
        return {
            "is_valid": True,
            "guardrail_triggered": False,
            "guardrail_type": None,
            "reason": val_output.reason,
            "redacted_text": masked_text,
        }
    except Exception as e:
        print(f"Validation exception: {e}")
        return {
            "is_valid": True,
            "guardrail_triggered": False,
            "guardrail_type": None,
            "reason": "Default pass",
            "redacted_text": masked_text,
        }


def context_injection_node(state: dict) -> dict:
    """
    Intercepts the state, looks up the user, and injects their profile.
    """
    user_id = state.get("user_id", "user_123")
    profile = get_user_profile(user_id)
    if profile:
        state["user_profile"] = profile
        print(f"🔧 SYSTEM: Injected profile for {profile.get('name')} (Tier: {profile.get('tier')})")
    else:
        state["user_profile"] = {"tier": "Unknown", "note": "No profile found"}
        print("🔧 SYSTEM: No user profile found. Proceeding with unknown tier.")
        
    return state
