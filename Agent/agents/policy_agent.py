from ..utils.policy_loader import load_policies

policies = load_policies()

def detect_high_priority_keywords(text: str) -> bool:
    text = text.lower()
    for keyword in policies["priority_rules"]["high"]:
        if keyword in text:
            return True
    return False


def can_auto_resolve(priority: str) -> bool:
    return policies["auto_resolution_allowed"].get(priority, False)


def get_faq_response(category: str):
    return policies["faq_responses"].get(category)
