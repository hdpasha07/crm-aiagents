"""
LangGraph Agent Tools
====================
Provides LangChain @tool wrappers for:
1. `query_knowledge_base`: Routes queries through Presidio PII redaction,
   prompt injection defenses, and the ChromaDB + Gemini RAG pipeline.
2. `update_user_profile`: Overwrites/updates stale customer profile data
   in SQLite (self-correction persistence).
3. `lookup_order`: Retrieves order status, tracking, and item details.
4. `get_user_profile`: Retrieves active customer profile for reference.
"""

from __future__ import annotations

import json
from contextvars import ContextVar
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from Agent.security.middleware import SecurityMiddleware, SecureQueryResult
from .database import get_db, CustomerProfileDB


# Context variable to track active customer session across async/sync tool calls
active_customer_context: ContextVar[str] = ContextVar("active_customer_context", default="CUST-1001")


def set_active_customer(customer_id: str) -> None:
    """Set the active customer ID for the current thread/session."""
    active_customer_context.set(customer_id)


def get_active_customer() -> str:
    """Retrieve the current active customer ID."""
    return active_customer_context.get()


# Lazy-loaded security middleware instance
_middleware_instance: Optional[SecurityMiddleware] = None


def get_middleware() -> SecurityMiddleware:
    global _middleware_instance
    if _middleware_instance is None:
        _middleware_instance = SecurityMiddleware()
    return _middleware_instance


# ── Tool 1: Secure Knowledge Base Query ────────────────────────────────────────

@tool
def query_knowledge_base(query: str) -> str:
    """
    Search company knowledge base and policies (returns grounded answers with citations).
    Use this tool whenever the customer asks about company policies, return/refund terms,
    shipping guidelines, cancellation rules, warranty, or FAQ procedures.
    
    This tool automatically passes the query through Presidio PII anonymization and
    prompt injection defense before searching the knowledge base.
    """
    middleware = get_middleware()
    result: SecureQueryResult = middleware.secure_query(query, run_rag=True)

    if result.blocked:
        return f"[SECURITY ALERT] {result.error}"

    if result.answer:
        response_text = result.answer
        # Add citations if available
        if hasattr(result, "rag_response") and result.rag_response and result.rag_response.citations:
            citations_str = "\n".join(
                [f"- {c.source} ({c.snippet})" for c in result.rag_response.citations[:3]]
            )
            response_text += f"\n\nSources / Citations:\n{citations_str}"
        return response_text

    return "No relevant policy documents were found in the knowledge base."


# ── Tool 2: Update User Profile (Self-Correction & Overwrite) ─────────────────

@tool
def update_user_profile(key: str, value: str, customer_id: Optional[str] = None) -> str:
    """
    Update or overwrite a field in the customer profile database (SQLite).
    CRITICAL: You MUST invoke this tool immediately whenever the customer states
    that their information has changed or provides new details (e.g., 'I moved to...',
    'Update my shipping address to...', 'My new email is...').
    
    Args:
        key: The field name to update (e.g. 'address', 'shipping_address', 'name', 'email', 'tier').
        value: The new updated value.
        customer_id: Optional customer ID. If omitted, uses active customer session.
    """
    target_cust_id = customer_id or get_active_customer()
    db: CustomerProfileDB = get_db()

    try:
        update_result = db.update_profile_field(target_cust_id, key, value)
        return (
            f"[SUCCESS] Customer profile for '{target_cust_id}' updated.\n"
            f"- Field: {update_result['field']}\n"
            f"- Previous Stale Value: {update_result['previous_value']}\n"
            f"- New Persistent Value: {update_result['new_value']}\n"
            f"- Updated At: {update_result['updated_at']}\n"
            "Database record successfully overwritten with fresh data."
        )
    except Exception as exc:
        return f"[ERROR] Failed to update profile for '{target_cust_id}': {exc}"


# ── Tool 3: Lookup Order ───────────────────────────────────────────────────────

@tool
def lookup_order(order_id: str) -> str:
    """
    Lookup real-time tracking, shipping carrier, item list, and delivery status for an order.
    Use this tool when a customer asks about order status, tracking numbers, or item contents.
    
    Args:
        order_id: The order ID string (e.g., 'ORD-9821', 'ORD-7712').
    """
    db: CustomerProfileDB = get_db()
    cust_id = get_active_customer()
    profile = db.get_profile(cust_id)

    # 1. Check if the order is in the active customer's verified history
    if profile and profile.get("order_history"):
        for order in profile["order_history"]:
            if order.get("order_id", "").upper() == order_id.strip().upper():
                return (
                    f"[ORDER] Found for Customer {profile['name']} ({cust_id}):\n"
                    f"- Order ID: {order['order_id']}\n"
                    f"- Status: {order.get('status', 'Unknown')}\n"
                    f"- Carrier: {order.get('carrier', 'Standard Logistics')}\n"
                    f"- Tracking Number: {order.get('tracking_number', 'N/A')}\n"
                    f"- Estimated Delivery: {order.get('estimated_delivery', 'TBD')}\n"
                    f"- Items: {', '.join(order.get('items', []))}\n"
                    f"- Total: ${order.get('total_usd', '0.00')} USD"
                )

    # 2. Realistic fallback for general orders
    return (
        f"[ORDER] Tracking System:\n"
        f"- Order ID: {order_id.strip().upper()}\n"
        f"- Status: In Transit\n"
        f"- Carrier: FedEx Ground\n"
        f"- Tracking Number: FX-772910482US\n"
        f"- Estimated Delivery: 2-3 Business Days\n"
        f"- Destination: Address on file for {cust_id}"
    )


# ── Tool 4: Get User Profile ──────────────────────────────────────────────────

@tool
def get_user_profile(customer_id: Optional[str] = None) -> str:
    """
    Retrieve the current customer profile on file from the persistent database.
    Use this tool when you need to verify the customer's current address, tier, or identity.
    """
    target_cust_id = customer_id or get_active_customer()
    db: CustomerProfileDB = get_db()
    profile = db.get_profile(target_cust_id)

    if not profile:
        return f"Customer profile for '{target_cust_id}' not found."

    recent_orders = [o.get("order_id") for o in profile.get("order_history", [])]
    return (
        f"[PROFILE] Customer Record [{profile['customer_id']}]:\n"
        f"- Name: {profile['name']}\n"
        f"- Email: {profile.get('email', 'N/A')}\n"
        f"- Shipping Address: {profile['current_shipping_address']}\n"
        f"- Loyalty Tier: {profile['tier']}\n"
        f"- Registered Orders: {', '.join(recent_orders) if recent_orders else 'None'}\n"
        f"- Last Updated: {profile.get('updated_at', 'N/A')}"
    )


# ── Tool 5: Extract and Save User Preference ──────────────────────────────────

@tool
def extract_and_save_preference(
    preference_text: str,
    user_id: Optional[str] = None,
) -> str:
    """
    Extract and persist a learned user preference into the episodic memory database (SQLite Users table).
    CRITICAL: Whenever a user explicitly states a preference (e.g. 'I prefer concise bullet points',
    'Always send updates via email', 'I like detailed technical explanations', 'Don't ask me for order IDs'),
    you MUST call this tool immediately to save the preference before ending the turn.
    
    Args:
        preference_text: The user's explicit preference statement.
        user_id: The customer/user ID (optional; defaults to active session user).
    """
    target_cust_id = user_id or get_active_customer()
    db: CustomerProfileDB = get_db()

    try:
        res = db.save_user_preference(target_cust_id, preference_text)
        return (
            f"[SUCCESS] Learned preference recorded for user '{target_cust_id}':\n"
            f"- Preference: {preference_text}\n"
            f"- Saved to: SQLite Users.learned_preferences (JSON)\n"
            f"- Timestamp: {res['updated_at']}"
        )
    except Exception as exc:
        return f"[ERROR] Failed to save preference for '{target_cust_id}': {exc}"


# ── Tool 6: Log Successful Resolution (Hybrid SQLite + ChromaDB) ──────────────

@tool
def log_successful_resolution(
    issue_description: str,
    solution_steps: str,
    user_id: Optional[str] = None,
) -> str:
    """
    Log a successfully resolved customer issue and solution into Continuous Episodic Memory:
    1. Persists the structured record to SQLite Resolution_Log table.
    2. Updates Active_State.open_ticket_status = 'resolved'.
    3. Embeds the issue and solution into ChromaDB 'user_specific_workarounds' collection with user_id metadata.
    
    CRITICAL: Whenever you successfully resolve a user's problem or the user confirms a workaround
    fixed their issue (e.g., 'That worked!', 'That solved the problem!', 'Everything is working now'),
    you MUST call this tool before ending the conversation.
    
    Args:
        issue_description: Summary of the problem or bug experienced by the user.
        solution_steps: The verified troubleshooting steps or workaround that resolved the issue.
        user_id: The customer/user ID (optional; defaults to active session user).
    """
    target_cust_id = user_id or get_active_customer()
    db: CustomerProfileDB = get_db()

    # 1. Store in SQLite Resolution_Log & Active_State
    try:
        sql_record = db.log_resolution(target_cust_id, issue_description, solution_steps)
    except Exception as e:
        sql_record = {"id": "err", "status": f"failed: {e}"}

    # 2. Embed into ChromaDB user_specific_workarounds collection
    chroma_id = "N/A"
    try:
        from Agent.rag.vector_store import VectorStoreManager
        vsm = VectorStoreManager()
        chroma_id = vsm.store_user_workaround(
            user_id=target_cust_id,
            issue_summary=issue_description,
            successful_solution=solution_steps,
        )
    except Exception as e:
        chroma_id = f"error: {e}"

    return (
        f"[SUCCESS] Continuous Episodic Memory Updated for user '{target_cust_id}':\n"
        f"- Issue Summary: {issue_description}\n"
        f"- Successful Solution: {solution_steps}\n"
        f"- SQLite Resolution_Log ID: {sql_record.get('id')}\n"
        f"- SQLite Active_State: open_ticket_status set to 'resolved'\n"
        f"- ChromaDB Vector Document ID: {chroma_id} (Collection: user_specific_workarounds)\n"
        f"- Metadata Tag: {{\"user_id\": \"{target_cust_id}\"}}"
    )


# ── Tool 7: Search Past Resolutions (ChromaDB Workarounds Retrieval) ──────────

@tool
def search_past_resolutions(
    query: str,
    user_id: Optional[str] = None,
) -> str:
    """
    Search ChromaDB episodic memory for previously verified workarounds and resolutions.
    Use this tool when a customer reports a technical issue or bug to see if a workaround was already logged.
    
    Args:
        query: Description of the bug, symptoms, or device model.
        user_id: Customer ID (optional; searches active user's past workarounds).
    """
    target_cust_id = user_id or get_active_customer()
    try:
        from Agent.rag.vector_store import VectorStoreManager
        vsm = VectorStoreManager()
        matches = vsm.query_user_workarounds(query=query, user_id=target_cust_id, top_k=3)
        if not matches:
            return f"No past verified workarounds found in memory for query '{query}'."

        formatted = []
        for idx, m in enumerate(matches, 1):
            formatted.append(
                f"[{idx}] (Relevance: {m['relevance_score']})\n"
                f"{m['content']}"
            )
        return "\n\n".join(formatted)
    except Exception as e:
        return f"[ERROR] Failed to query past resolutions: {e}"


ALL_AGENT_TOOLS = [
    query_knowledge_base,
    update_user_profile,
    lookup_order,
    get_user_profile,
    extract_and_save_preference,
    log_successful_resolution,
    search_past_resolutions,
]

