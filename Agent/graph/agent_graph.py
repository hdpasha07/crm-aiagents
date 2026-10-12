"""
Stateful LangGraph Customer Support Agent
=========================================
Implements the multi-turn agent loop with:
- Token-optimized Shadow Context Injection (pre-routing interceptor)
- Tool calling (query_knowledge_base, update_user_profile, lookup_order, get_user_profile)
- Autonomous self-correction (automatic profile overwrite upon detecting user data changes)
- Conversation checkpointing across turns using thread_id
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Literal, Optional

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from Agent.llm import get_llm
from .database import get_db
from .shadow_context import get_shadow_injector
from .state import CustomerSupportAgentState
from .tools import ALL_AGENT_TOOLS, set_active_customer


BASE_SYSTEM_PROMPT = """You are an Enterprise AI Customer Support Agent for our e-commerce platform.
Your goal is to provide fast, accurate, and professional support to our customers.

You have access to the following specialized tools:
1. `query_knowledge_base(query)`:
   - Use to search official company policies: returns/refunds, shipping policies, warranty guidelines, or FAQs.
   - Automatically protected by Presidio PII anonymization and injection defenses.
2. `update_user_profile(key, value)`:
   - Updates or overwrites customer records (such as shipping address, name, email) in the database.
   - CRITICAL SELF-CORRECTION RULE: Whenever a customer states their personal info has changed (e.g., "I updated my address to...", "I moved to...", "Change my shipping address to..."), you MUST IMMEDIATELY call `update_user_profile` to overwrite the stale record in SQLite before answering.
3. `lookup_order(order_id)`:
   - Retrieves real-time tracking, carrier, item contents, and status for an order.
4. `get_user_profile()`:
   - Retrieves the customer's current verified profile from the database.
5. `extract_and_save_preference(preference_text)`:
   - Persists learned user preferences (formatting, tone, channel) to SQLite `Users.learned_preferences`.
6. `log_successful_resolution(issue_description, solution_steps)`:
   - Persists verified issue fixes to SQLite `Resolution_Log` AND embeds into ChromaDB `user_specific_workarounds` collection.
7. `search_past_resolutions(query)`:
   - Searches ChromaDB episodic memory for past successful troubleshooting workarounds.

CRITICAL INSTRUCTIONS & AUTONOMOUS EXTRACTION RULES:
- Whenever a user informs you of an address change or profile update, ALWAYS execute `update_user_profile` to maintain data consistency.
- Whenever you successfully resolve a user's problem, or the user confirms that a solution or workaround worked (e.g., "That worked!", "That fixed it!", "Issue is solved"), you MUST call `log_successful_resolution(issue_description, solution_steps)` before ending the conversation.
- Whenever the user explicitly states a preference (e.g., "I prefer concise bullet points", "Always send updates via email", "I like step-by-step instructions"), you MUST call `extract_and_save_preference(preference_text)` before ending the conversation.
- After tool execution, provide a clear, helpful confirmation to the customer.
- If a security error or blocked message is returned by a tool, respect it and explain that the request cannot be fulfilled due to security guidelines.
"""


def shadow_context_node(state: CustomerSupportAgentState) -> Dict[str, Any]:
    """
    Interceptor Gate:
    Queries the database and dynamically injects only query-relevant customer data.
    """
    customer_id = state.get("customer_id") or "CUST-1001"
    set_active_customer(customer_id)

    # Extract the last user message to determine context relevance
    messages = state.get("messages", [])
    last_user_query = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or (hasattr(msg, "type") and msg.type == "human"):
            last_user_query = str(msg.content)
            break

    injector = get_shadow_injector()
    shadow_prompt = injector.build_shadow_system_prompt(customer_id, last_user_query)

    return {
        "customer_id": customer_id,
        "shadow_context": shadow_prompt,
    }


def agent_node(state: CustomerSupportAgentState) -> Dict[str, Any]:
    """
    Main LLM reasoning node with bound tools.
    """
    customer_id = state.get("customer_id") or "CUST-1001"
    set_active_customer(customer_id)

    # Build active system prompt including shadow context if present
    system_text = BASE_SYSTEM_PROMPT
    shadow_ctx = state.get("shadow_context")
    if shadow_ctx:
        system_text += f"\n\n{shadow_ctx}"

    # Prepare message list for Gemini
    incoming_messages = state.get("messages", [])

    # Filter out any previous top-level SystemMessages to avoid duplicate system prompts
    non_system_messages = [
        m for m in incoming_messages
        if not (isinstance(m, SystemMessage) or (hasattr(m, "type") and m.type == "system"))
    ]

    full_conversation = [SystemMessage(content=system_text)] + non_system_messages

    # Initialize Gemini with bound tools
    llm = get_llm(temperature=0.0)
    llm_with_tools = llm.bind_tools(ALL_AGENT_TOOLS)

    response = llm_with_tools.invoke(full_conversation)
    current_step = state.get("step_count", 0) + 1

    return {
        "messages": [response],
        "step_count": current_step,
    }


def route_decision(state: CustomerSupportAgentState) -> Literal["tools", "__end__"]:
    """
    Determines whether the LLM produced tool calls or is ready to respond to the user.
    """
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def create_customer_support_graph(checkpointer: Optional[Any] = None):
    """
    Constructs and compiles the full Customer Support LangGraph workflow.
    """
    workflow = StateGraph(CustomerSupportAgentState)

    # Add Nodes
    workflow.add_node("shadow_interceptor", shadow_context_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(ALL_AGENT_TOOLS))

    # Add Edges
    workflow.add_edge(START, "shadow_interceptor")
    workflow.add_edge("shadow_interceptor", "agent")
    workflow.add_conditional_edges(
        "agent",
        route_decision,
        {
            "tools": "tools",
            END: END,
        },
    )
    workflow.add_edge("tools", "agent")

    memory = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=memory)


class CustomerSupportAgent:
    """
    High-level facade for managing sessions with the customer support agent graph.
    """

    def __init__(self, checkpointer: Optional[Any] = None):
        self.graph = create_customer_support_graph(checkpointer=checkpointer)

    def chat(
        self,
        user_message: str,
        customer_id: str = "CUST-1001",
        thread_id: str = "default_thread",
    ) -> Dict[str, Any]:
        """
        Execute a single user turn in a stateful conversation thread.
        """
        config = {"configurable": {"thread_id": thread_id}}
        set_active_customer(customer_id)

        input_payload = {
            "messages": [HumanMessage(content=user_message)],
            "customer_id": customer_id,
        }

        result = self.graph.invoke(input_payload, config=config)

        # Retrieve the final assistant response text
        final_answer = ""
        tool_actions_taken = []

        for msg in reversed(result.get("messages", [])):
            if isinstance(msg, AIMessage) or (hasattr(msg, "type") and msg.type == "ai"):
                if msg.content:
                    if isinstance(msg.content, list):
                        parts = []
                        for part in msg.content:
                            if isinstance(part, dict) and "text" in part:
                                parts.append(part["text"])
                            elif isinstance(part, str):
                                parts.append(part)
                            else:
                                parts.append(str(part))
                        final_answer = "\n".join(parts)
                    else:
                        final_answer = str(msg.content)
                    break

        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_actions_taken.append(tc)

        return {
            "answer": final_answer,
            "tool_calls": tool_actions_taken,
            "shadow_context": result.get("shadow_context"),
            "full_state": result,
        }

