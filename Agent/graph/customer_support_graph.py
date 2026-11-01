"""LangGraph definition for the Customer Support Agent.

The graph orchestrates three main tool actions:
- ``query_knowledge_base`` – secure RAG lookup.
- ``update_user_profile`` – modify persisted user profile.
- ``lookup_order`` – fetch mock order data.

It also implements lightweight self‑correction: when the user provides a
profile update (e.g., a new address) the graph detects it via regex, invokes
``update_user_profile`` automatically, and then proceeds to answer the user's
original query.
"""

from __future__ import annotations

import re
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

from .state import AgentState, Message
from .tools import query_knowledge_base, update_user_profile, lookup_order

# ---------------------------------------------------------------------------
# Helper regex patterns for detecting user intents
# ---------------------------------------------------------------------------
ADDRESS_UPDATE_RE = re.compile(r"(?:my\s+address\s+(?:is|to)\s+)(?P<addr>.+)", re.IGNORECASE)
ORDER_LOOKUP_RE = re.compile(r"order\s*#?\s*(?P<oid>\d+)", re.IGNORECASE)


def detect_intents(state: AgentState) -> Dict[str, Any]:
    """Return a dict describing what the user is trying to do.

    Keys:
        * ``action`` – one of ``update_profile``, ``lookup_order`` or ``query``.
        * ``payload`` – additional data needed by the chosen action.
    """
    text = state.current_input.strip()
    # 1. Address/profile update
    m = ADDRESS_UPDATE_RE.search(text)
    if m:
        return {"action": "update_profile", "payload": {"key": "address", "value": m.group("addr").strip()}}
    # 2. Order lookup
    m = ORDER_LOOKUP_RE.search(text)
    if m:
        return {"action": "lookup_order", "payload": {"order_id": m.group("oid")}}
    # Default – treat as knowledge base query
    return {"action": "query", "payload": {"query": text}}


def process_input(state: AgentState) -> AgentState:
    """Parse ``state.current_input`` and store routing info.
    """
    intent = detect_intents(state)
    setattr(state, "_next", intent)
    return state


def call_tool(state: AgentState) -> AgentState:
    """Execute the selected tool and store its result.
    """
    intent: Dict[str, Any] = getattr(state, "_next", {"action": "query", "payload": {"query": state.current_input}})
    action = intent["action"]
    payload = intent["payload"]
    if action == "update_profile":
        result = update_user_profile(state.user_id, payload["key"], payload["value"])
    elif action == "lookup_order":
        result = lookup_order(payload["order_id"])
    else:
        result = query_knowledge_base(payload["query"])
    setattr(state, "_tool_result", result)
    return state


def generate_response(state: AgentState) -> AgentState:
    """Compose the final assistant message.
    """
    tool_result = getattr(state, "_tool_result", "")
    if isinstance(tool_result, dict):
        content = f"📦 Order details:\n```
{tool_result}
```"
    else:
        content = str(tool_result)
    state.conversation_history.append(Message(role="assistant", content=content))
    state.current_input = ""
    return state

# Build the graph
graph = StateGraph(AgentState)

@graph.add_node(START)
def load_profile(state: AgentState) -> AgentState:
    state.load_profile()
    return state

graph.add_node("process_input", process_input)
graph.add_node("call_tool", call_tool)
graph.add_node("generate_response", generate_response)

graph.add_edge(START, "process_input")
graph.add_edge("process_input", "call_tool")
graph.add_edge("call_tool", "generate_response")
graph.add_edge("generate_response", END)

app = graph.compile()

def run_turn(state_dict: dict) -> dict:
    """Run a single turn of the agent.
    """
    state = AgentState(**state_dict)
    new_state = app(state)
    return new_state.dict()

if __name__ == "__main__":
    import json
    from .profile_store import update_profile
    user_id = "user_123"
    update_profile(user_id, name="John Doe", address="456 Old St")
    state = {"user_id": user_id, "conversation_history": [], "current_input": ""}
    print("Enter messages (type 'exit' to quit):")
    while True:
        inp = input("You: ")
        if inp.lower() in {"exit", "quit"}:
            break
        state["current_input"] = inp
        state = run_turn(state)
        if state["conversation_history"]:
            last_msg = state["conversation_history"][-1]
            print(f"Assistant: {last_msg['content']}")

