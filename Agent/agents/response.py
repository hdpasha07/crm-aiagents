from Agent.agents.policy_agent import (
    detect_high_priority_keywords,
    can_auto_resolve,
    get_faq_response
)

def generate_email_response(
    complaint_text: str,
    category: str,
    priority: str
) -> str:

    if detect_high_priority_keywords(complaint_text) or not can_auto_resolve(priority):
        return (
            "Thank you for contacting us.\n\n"
            "We have received your complaint and it is currently under review by our support team. "
            "An appropriate solution will be provided shortly.\n\n"
            "We appreciate your patience."
        )

    faq_reply = get_faq_response(category)

    if faq_reply:
        return (
            "Thank you for reaching out to us.\n\n"
            f"{faq_reply}\n\n"
            "Please let us know if you need any further assistance."
        )

    return (
        "Thank you for your message.\n\n"
        "Your concern has been noted and our team will get back to you shortly."
    )
