# agents/user_validation.py

# Adjust the import path based on where you saved db_mock.py
# If it is in the root folder, use: from db_mock import get_user_profile
from ..utils.db_mock import get_user_profile 

def context_injection_node(state: dict) -> dict:
    """
    Intercepts the state, looks up the user, and injects their profile.
    Future Guardrail: PII redaction and user authorization will happen here.
    """
    # 1. Extract the user ID (We default to "user_123" for our initial testing)
    user_id = state.get("user_id", "user_123")
    
    # 2. Fetch data from our mock database
    profile = get_user_profile(user_id)
    
    # 3. Inject the profile into the state
    if profile:
        state["user_profile"] = profile
        print(f"[SYSTEM] Injected profile for {profile.get('name')} (Tier: {profile.get('tier')})")
    else:
        state["user_profile"] = {"tier": "Unknown", "note": "No profile found"}
        print("[SYSTEM] No user profile found. Proceeding with unknown tier.")
        
    return state