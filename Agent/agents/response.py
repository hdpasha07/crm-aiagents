import re
from Agent.agents.policy_agent import (
    detect_high_priority_keywords,
    can_auto_resolve,
    get_faq_response
)

def strip_source_metadata(text: str) -> str:
    """Strips internal source and chunk metadata brackets from text."""
    if not text:
        return ""
    cleaned = re.sub(r"\[(?:Source|Chunk|Source Document|Chunk ID)[^\]]*\]", "", text)
    cleaned = re.sub(r" +([.,!?;:])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = "\n".join(line.rstrip() for line in cleaned.splitlines())
    return cleaned.strip()

def generate_email_response(
    complaint_text: str,
    category: str,
    priority: str
) -> str:
    # High-priority escalated complaints that cannot be auto-resolved
    if detect_high_priority_keywords(complaint_text) or not can_auto_resolve(priority):
        return (
            "Thank you for contacting us.\n\n"
            "We have received your complaint and it is currently under review by our support team. "
            "An appropriate solution will be provided shortly.\n\n"
            "We appreciate your patience."
        )

    # For auto-resolvable inquiries, dynamically generate the grounded response using GeminiRAG
    try:
        from Agent.rag.llm_rag import GeminiRAG
        rag_engine = GeminiRAG()
        rag_response = rag_engine.generate_grounded_response(complaint_text, customer_facing=True)
        if rag_response and rag_response.answer and rag_response.answer.strip():
            return strip_source_metadata(rag_response.answer)
    except Exception as e:
        print(f"GeminiRAG generation exception: {e}")

    # Fallback to FAQ response from policy config if available
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
