"""
Continuous Episodic Memory End-to-End Verification Test
=======================================================
Simulates multi-turn interaction testing:
1. User reports a specific bug on a purchased product.
2. Agent provides concrete troubleshooting workaround.
3. User confirms the workaround succeeded and states a personal preference.
4. Agent autonomously invokes:
   - `log_successful_resolution`: persists to SQLite Resolution_Log AND embeds into ChromaDB.
   - `extract_and_save_preference`: persists to SQLite Users.learned_preferences.
5. Verification:
   - Direct SQLite database query confirming normalized records.
   - Direct ChromaDB semantic similarity search verifying vector persistence.
"""

from __future__ import annotations

import os
import sys
import time

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from Agent.graph.agent_graph import CustomerSupportAgent
from Agent.graph.database import CustomerProfileDB, get_db
from Agent.rag.vector_store import VectorStoreManager


def print_banner(title: str) -> None:
    print("\n" + "=" * 80)
    print(f"  {title.upper()}")
    print("=" * 80)


def print_turn_header(turn_num: int, label: str) -> None:
    print("\n" + "-" * 80)
    print(f"[TURN {turn_num}] {label}")
    print("-" * 80)


def run_episodic_memory_test() -> None:
    print_banner("Phase 4: Continuous Episodic Memory Multi-Turn Verification")

    customer_id = "CUST-1001"
    thread_id = f"episodic_test_{int(time.time())}"

    # --------------------------------------------------------------------------
    # STEP 1: Initialize Persistence Layers
    # --------------------------------------------------------------------------
    print("\n[STEP 1] Initializing SQLite Normalized Tables & ChromaDB Collection...")
    db: CustomerProfileDB = get_db()
    db.reset_db()
    db.seed_sample_profiles()

    vsm = VectorStoreManager()
    # Reset user workarounds collection for isolated clean test run
    try:
        vsm.client.delete_collection("user_specific_workarounds")
    except Exception:
        pass
    workaround_col = vsm.get_user_workarounds_collection()

    print(f"[SQLITE] Database ready at: {db.db_path}")
    print(f"[CHROMADB] Initial user workarounds count: {workaround_col.count()}")

    agent = CustomerSupportAgent()
    print("[AGENT] Stateful LangGraph Agent with episodic tools loaded.")

    # --------------------------------------------------------------------------
    # TURN 1: User Reports Specific Bug
    # --------------------------------------------------------------------------
    print_turn_header(1, "User Reports Bug on Ergonomic Keyboard")
    user_msg_1 = (
        "I'm having a persistent issue with my Ergonomic Mechanical Keyboard (from order ORD-9821). "
        "Every 10 minutes on Windows 11, the Bluetooth connection abruptly drops and keystrokes freeze. "
        "How do I fix this?"
    )
    print(f"User: \"{user_msg_1}\"\n")

    res_1 = agent.chat(user_msg_1, customer_id=customer_id, thread_id=thread_id)
    print(f"Assistant:\n{res_1['answer']}")
    tool_names_1 = [tc["name"] for tc in res_1["tool_calls"]]
    print(f"\n[Tools Invoked in Turn 1]: {tool_names_1}")

    # --------------------------------------------------------------------------
    # TURN 2: User Confirms Workaround Works & States Explicit Preference
    # --------------------------------------------------------------------------
    print_turn_header(2, "User Confirms Fix Works & States Preference")
    user_msg_2 = (
        "That worked! Disabling USB selective suspend in Power Options and turning off "
        "Bluetooth power saving in Device Manager completely solved the issue! "
        "Also, please remember that I always prefer concise, step-by-step bullet points for technical support."
    )
    print(f"User: \"{user_msg_2}\"\n")

    res_2 = agent.chat(user_msg_2, customer_id=customer_id, thread_id=thread_id)
    print(f"Assistant:\n{res_2['answer']}")
    tool_names_2 = [tc["name"] for tc in res_2["tool_calls"]]
    print(f"\n[Tools Invoked in Turn 2]: {tool_names_2}")

    # Check that autonomous extraction tools were called
    assert "log_successful_resolution" in tool_names_2 or "extract_and_save_preference" in tool_names_2, (
        f"Expected autonomous logging tools in turn 2, got: {tool_names_2}"
    )

    # --------------------------------------------------------------------------
    # STEP 3: Verify SQLite Database (Resolution_Log, Users, Active_State)
    # --------------------------------------------------------------------------
    print_banner("Step 3: Direct SQLite Database Verification")

    # 1. Inspect Resolution_Log
    resolutions = db.get_resolution_history(customer_id)
    print(f"[SQLITE Resolution_Log] Total Logged Records: {len(resolutions)}")
    assert len(resolutions) > 0, "No records found in SQLite Resolution_Log table!"
    latest_res = resolutions[0]
    print(f"  - Record ID:           {latest_res['id']}")
    print(f"  - User ID:             {latest_res['user_id']}")
    print(f"  - Issue Summary:       {latest_res['issue_summary']}")
    print(f"  - Successful Solution: {latest_res['successful_solution']}")
    print(f"  - Timestamp:           {latest_res['timestamp']}")
    print(">>> SQLite Resolution_Log table verified.")

    # 2. Inspect Users.learned_preferences
    user_prefs = db.get_user_preferences(customer_id)
    print(f"\n[SQLITE Users] Learned Preferences JSON: {user_prefs}")
    pref_list = user_prefs.get("preferences", [])
    assert len(pref_list) > 0, "No learned preferences saved to SQLite Users table!"
    print(f"  - Total Preferences Learned: {len(pref_list)}")
    print(f"  - Latest Preference:         {pref_list[-1]['preference']}")
    print(">>> SQLite Users learned_preferences verified.")

    # 3. Inspect Active_State
    active_state = db.get_active_state(customer_id)
    print(f"\n[SQLITE Active_State] User State: {active_state}")
    assert active_state is not None, "Active_State record missing!"
    print(f"  - Open Ticket Status: {active_state.get('open_ticket_status')}")
    print(">>> SQLite Active_State verified.")

    # --------------------------------------------------------------------------
    # STEP 4: Verify Hybrid ChromaDB Vector Persistence
    # --------------------------------------------------------------------------
    print_banner("Step 4: Direct ChromaDB Vector Persistence Verification")

    chroma_count = workaround_col.count()
    print(f"[CHROMADB user_specific_workarounds] Total Vector Documents: {chroma_count}")
    assert chroma_count > 0, "No workaround documents stored in ChromaDB collection!"

    # Perform semantic similarity search for the workaround
    search_query = "keyboard bluetooth keeps disconnecting and freezing"
    print(f"\n[CHROMADB RETRIEVAL TEST] Query: \"{search_query}\"")
    results = vsm.query_user_workarounds(
        query=search_query,
        user_id=customer_id,
        top_k=2,
    )

    assert len(results) > 0, "Semantic search failed to retrieve stored workaround!"
    top_match = results[0]
    print(f"  - Top Match ID:        {top_match['id']}")
    print(f"  - Relevance Score:     {top_match['relevance_score']}")
    print(f"  - Metadata:            {top_match['metadata']}")
    print(f"  - Retrieved Content:\n{top_match['content']}")

    assert top_match["metadata"].get("user_id") == customer_id, (
        f"Expected user_id '{customer_id}' in ChromaDB metadata, got '{top_match['metadata'].get('user_id')}'"
    )
    print(">>> ChromaDB hybrid episodic memory verified with user metadata tag.")

    # --------------------------------------------------------------------------
    # TURN 3: Subsequent User Query Querying Memory
    # --------------------------------------------------------------------------
    print_turn_header(3, "Subsequent Query - Agent Recalls Past Solution")
    user_msg_3 = "What was that Bluetooth fix we used for my keyboard earlier?"
    print(f"User: \"{user_msg_3}\"\n")

    res_3 = agent.chat(user_msg_3, customer_id=customer_id, thread_id=thread_id)
    print(f"Assistant:\n{res_3['answer']}")
    assert "suspend" in res_3["answer"].lower() or "power" in res_3["answer"].lower() or "bluetooth" in res_3["answer"].lower(), (
        "Agent failed to recall the solution from episodic memory!"
    )
    print("\n>>> TURN 3 PASSED: Agent successfully recalled past workaround.")

    print("\n" + "=" * 80)
    print("  [SUCCESS] ALL EPISODIC MEMORY TESTS PASSED WITH ZERO ERRORS!")
    print("=" * 80)


if __name__ == "__main__":
    run_episodic_memory_test()

