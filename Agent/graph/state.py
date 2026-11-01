"""State model for the LangGraph Customer Support Agent.

We use Pydantic for type‑safety and easy serialization. The state holds the
current user identifier, the conversation history, and a cached copy of the
user's profile (loaded from ``profile_store`` at the start of each turn).
"""

from __future__ import annotations

from typing import List, Dict, Any

from pydantic import BaseModel, Field

from .profile_store import get_profile


class Message(BaseModel):
    role: str = Field(..., description="One of 'user', 'assistant', or 'system'.")
    content: str = Field(..., description="The text content of the message.")


class AgentState(BaseModel):
    user_id: str = Field(..., description="Identifier for the active user/session.")
    conversation_history: List[Message] = Field(default_factory=list, description="Chronological list of exchanged messages.")
    current_input: str = Field("", description="The latest user utterance to be processed.")
    profile: Dict[str, Any] = Field(default_factory=dict, description="Cached user profile loaded from persistence.")

    def load_profile(self) -> None:
        """Populate ``self.profile`` from the persistent store.

        Called at the beginning of each turn after ``user_id`` is known.
        """
        self.profile = get_profile(self.user_id)

    class Config:
        arbitrary_types_allowed = True

