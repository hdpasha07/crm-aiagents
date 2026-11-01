"""Utility tools for the LangGraph Customer Support Agent.

These functions are intended to be registered as LangGraph tools so that the
graph can invoke them during execution.
"""

from typing import Any, Dict

# Import the security middleware and the profile store we just created
from Agent.security.middleware import SecurityMiddleware
from .profile_store import get_profile, update_profile


def query_knowledge_base(user_input: str) -> str:
    """Securely query the Gemini RAG pipeline.

    The function delegates to ``SecurityMiddleware`` which performs PII redaction
    and injection protection before forwarding the cleaned query to the underlying
    Gemini RAG component.
    """
    middleware = SecurityMiddleware()
    result = middleware.secure_query(user_input)
    # ``secure_query`` returns a ``SecureQueryResult``; we assume it has ``answer``
    # attribute for the generated response.
    return getattr(result, "answer", str(result))


def update_user_profile(user_id: str, key: str, value: Any) -> str:
    """Update a single field in the user profile.

    Returns a short confirmation string.
    """
    update_profile(user_id, **{key: value})
    return f"✅ Profile field '{key}' updated to '{value}'."


def lookup_order(order_id: str) -> Dict[str, Any]:
    """Return a mock order record.

    In a production system this would query a real order DB. For the demo we
    return a static dictionary.
    """
    # Simple static mock – could be expanded later
    return {
        "order_id": order_id,
        "status": "shipped",
        "items": ["Widget A", "Widget B"],
        "estimated_delivery": "2026-10-20",
    }

__all__ = [
    "query_knowledge_base",
    "update_user_profile",
    "lookup_order",
]

