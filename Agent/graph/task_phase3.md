# Phase 3: Stateful LangGraph Agent – Task List

## 1️⃣ Persistence Layer
- **Create** `profile_store.py` with SQLite fallback to JSON.
- Functions: `init_db()`, `get_profile(user_id)`, `update_profile(user_id, **fields)`.
- Ensure DB file lives at `data/profiles.db` (create `data/` if missing).
- Add simple JSON fallback `profiles.json` for environments without SQLite.

## 2️⃣ LangGraph Tool Wrappers
- **query_knowledge_base(input_str)**: Calls `SecurityMiddleware().secure_query(input_str)` and returns the Gemini‑RAG answer.
- **update_user_profile(user_id, key, value)**: Uses `profile_store.update_profile` and returns a confirmation message.
- **lookup_order(order_id)**: Returns a mock order dict (status, items, shipping date).
- Place these in `tools.py` (or separate modules) and expose via `__all__`.

## 3️⃣ State Model
- Define a Pydantic `AgentState` in `state.py` with fields:
  - `user_id: str`
  - `conversation_history: List[Message]` (Message = `{role, content}`)
  - `current_input: str`
  - `profile: dict` (populated from `profile_store` on start)

## 4️⃣ Graph Construction (`customer_support_graph.py`)
- Initialize LangGraph `graph = StateGraph(AgentState)`.
- **Node: process_input** – Parses `current_input`:
  - Regex detection for profile updates (e.g., `address\s+to\s+(.+)` or `new address is (.+)`).
  - If match → call `update_user_profile` tool, store result, then fall through to query.
  - Regex for order lookup (`order\s*#?\s*(\d+)`).
- **Node: call_tool** – Dispatches to the appropriate tool based on detection flags.
- **Node: generate_response** – After tool execution, if no tool was needed, call `query_knowledge_base`.
- Add **Condition** nodes or custom logic to decide which path to take.
- Include system prompt:
  > *If the user provides new profile information, automatically invoke `update_user_profile` before answering.*

## 5️⃣ Self‑Correction Logic
- Within `process_input`, after any tool call, re‑inject the original user query (if present) so the agent can answer with updated context.
- Ensure the graph loops back to `generate_response` after tool execution.

## 6️⃣ Demo / Test Script (`test_langgraph.py`)
- Initialise DB, create a mock user (`user_123`).
- Simulate a three‑turn conversation:
  1. Policy question → RAG answer.
  2. "I updated my address to 123 New St." → profile update confirmation.
  3. "What is my current shipping address?" → agent retrieves from DB (via tool or state) and responds.
- Print each turn and final DB content.
- Verify no PII leakage and that injection guard still blocks malicious prompts.

## 7️⃣ Documentation
- Add `README.md` in `Agent/graph/` describing:
  - How to run the demo.
  - Folder layout.
  - How self‑correction works.
  - Extending the graph with additional tools.

## 8️⃣ Validation
- Run `pytest` (or `python test_langgraph.py`).
- Confirm:
  - DB persists across runs.
  - Security middleware still logs redacted queries.
  - All three tools operate correctly.

---
**Once these files are in place, we can execute the demo and iterate.**

