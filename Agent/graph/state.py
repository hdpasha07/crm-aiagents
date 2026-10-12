"""
State Definition for Customer Support LangGraph Agent
=====================================================
Defines the state structure maintained across the multi-turn conversation,
incorporating messages, active customer ID, and dynamically injected shadow context.
"""

from __future__ import annotations

from typing import Optional
from langgraph.graph import MessagesState


class CustomerSupportAgentState(MessagesState):
    """
    State container for the stateful tool-calling agent.
    Inherits `messages` list with automatic LangGraph message reduction/appending.
    """
    customer_id: str = "CUST-1001"
    shadow_context: Optional[str] = None
    step_count: int = 0

