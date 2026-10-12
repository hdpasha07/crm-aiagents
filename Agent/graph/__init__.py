"""
Agent Graph Package
==================
Contains the stateful LangGraph agent, SQLite persistence, shadow context injector,
and tool definitions. Also re-exports legacy build_graph for backward compatibility.
"""

from __future__ import annotations

# Re-export legacy build_graph for backward compatibility with worker/test_graph
try:
    from Agent.graph_legacy import (
        build_graph,
        categorize_node,
        policy_node,
        route_after_categorize,
        validation_node,
        escalation_node,
    )
except ImportError:
    build_graph = None
    categorize_node = None
    policy_node = None
    route_after_categorize = None
    validation_node = None
    escalation_node = None

from .database import CustomerProfileDB, get_db
from .shadow_context import ShadowContextInjector, get_shadow_injector
from .tools import (
    ALL_AGENT_TOOLS,
    query_knowledge_base,
    update_user_profile,
    lookup_order,
    get_user_profile,
    extract_and_save_preference,
    log_successful_resolution,
    search_past_resolutions,
    set_active_customer,
    get_active_customer,
)
from .state import CustomerSupportAgentState
from .agent_graph import (
    create_customer_support_graph,
    CustomerSupportAgent,
)

__all__ = [
    "build_graph",
    "CustomerProfileDB",
    "get_db",
    "ShadowContextInjector",
    "get_shadow_injector",
    "ALL_AGENT_TOOLS",
    "query_knowledge_base",
    "update_user_profile",
    "lookup_order",
    "get_user_profile",
    "extract_and_save_preference",
    "log_successful_resolution",
    "search_past_resolutions",
    "set_active_customer",
    "get_active_customer",
    "CustomerSupportAgentState",
    "create_customer_support_graph",
    "CustomerSupportAgent",
]
