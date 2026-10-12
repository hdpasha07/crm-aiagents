from typing import TypedDict, Optional, List, Dict, Any

class ComplaintState(TypedDict):
    complaint_text: str
    user_id: Optional[str]
    user_profile: Optional[Dict[str, Any]]

    is_valid: Optional[bool]
    validation_reason: Optional[str]

    category: Optional[str]
    sentiment: Optional[str]
    priority: Optional[str]
    priority_reason: Optional[str]

    response_email: Optional[str]
    suggestions: Optional[List[str]]

    reevaluated_priority: Optional[str]
    escalation_required: Optional[bool]
    escalation_reason: Optional[str]
