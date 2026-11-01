from langgraph.graph import StateGraph, END
from .state import ComplaintState

from .agents.categorizer import categorize
from .agents.sentiment import analyze_sentiment
from .agents.priority import assign_priority
from .agents.response import generate_email_response
from .agents.suggestion import suggest_actions
from .agents.reevaluate import reevaluate_priority
from .agents.escalation import decide_escalation
from .agents.user_validation import context_injection_node, validate_and_guardrail

from .utils.memory_store import store_high_priority

def validation_node(state):
    guardrail_result = validate_and_guardrail(state["complaint_text"])
    state["complaint_text"] = guardrail_result["redacted_text"]
    state["is_valid"] = guardrail_result["is_valid"]
    state["guardrail_triggered"] = guardrail_result.get("guardrail_triggered", False)
    state["guardrail_type"] = guardrail_result.get("guardrail_type")
    state["validation_reason"] = guardrail_result["reason"]
    return state

def categorize_node(state):
    state["category"] = categorize(state["complaint_text"]).category
    return state


def sentiment_node(state):
    state["sentiment"] = analyze_sentiment(state["complaint_text"]).sentiment
    return state


def priority_node(state):
    result = assign_priority(
        state["complaint_text"],
        state["category"],
        state["sentiment"]
    )
    state["priority"] = result.priority
    state["priority_reason"] = result.reason
    return state


def response_node(state):
    email_text = generate_email_response(
        complaint_text=state["complaint_text"],
        category=state["category"],
        priority=state["priority"]
    )
    state["response"] = email_text
    state["response_email"] = email_text
    state["resolution"] = email_text
    return state

def suggestion_node(state):
    result = suggest_actions(
        state["complaint_text"],
        state["category"],
        state["priority"]
    )
    state["suggestions"] = result.actions
    return state


def reevaluate_node(state):
    result = reevaluate_priority(
        state["complaint_text"],
        state["priority"],
        state["response_email"],
        state["suggestions"]
    )
    state["reevaluated_priority"] = result.updated_priority
    state["escalation_reason"] = result.reason
    return state


def escalation_node(state):
    result = decide_escalation(
        state["complaint_text"],
        state["reevaluated_priority"],
        state["escalation_reason"]
    )
    state["escalation_required"] = result.escalate

    if result.escalate:
        try:
            store_high_priority(state)
        except Exception:
            pass  

    return state


def route_after_escalation(state):
    if state["escalation_required"]:
        return "human"
    return END

def route_after_validation(state):
    if not state["is_valid"]:
        return END
    return "inject_context"


def human_node(state):
    print("\n🚨 HUMAN ESCALATION REQUIRED 🚨\n")
    print(state)
    return state


def build_graph():
    graph = StateGraph(ComplaintState)

    graph.add_node("validate", validation_node)
    graph.add_node("inject_context", context_injection_node) 
    graph.add_node("categorize", categorize_node)
    graph.add_node("sentiment", sentiment_node)
    graph.add_node("priority", priority_node)
    graph.add_node("response", response_node)
    graph.add_node("suggestion", suggestion_node)
    graph.add_node("reevaluate", reevaluate_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("human", human_node)

    graph.set_entry_point("validate")
    
    graph.add_edge("inject_context", "categorize") 
    graph.add_edge("categorize", "sentiment")
    graph.add_edge("sentiment", "priority")
    graph.add_edge("priority", "response")
    graph.add_edge("response", "suggestion")
    graph.add_edge("suggestion", "reevaluate")
    graph.add_edge("reevaluate", "escalation")
    graph.add_conditional_edges("escalation", route_after_escalation)
    graph.add_conditional_edges("validate", route_after_validation)

    return graph.compile()
