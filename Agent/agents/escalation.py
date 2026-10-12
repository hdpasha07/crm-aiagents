from langchain_core.prompts import ChatPromptTemplate
from ..schemas.escalation import EscalationOutput
from ..llm import get_llm
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are an escalation decision agent.

Complaint:
{complaint}

Final Priority: {priority}
Re-evaluation Reason: {reason}

STRICT RULES:
- You MUST return valid JSON
- You MUST return BOTH fields even if escalation is obvious
- Allowed values:
  - escalate: true or false
  - reason: short explanation

DO NOT explain outside JSON.
DO NOT return empty output.

If priority is "high", escalate = true.

Return ONLY JSON.

Example:
{{"escalate": true, "reason": "High-risk unresolved complaint"}}
""")

def decide_escalation(complaint, priority, reason):
    response = llm.invoke(
        prompt.format_messages(
            complaint=complaint,
            priority=priority,
            reason=reason
        )
    )

    clean_json = extract_json(response.content)
    return EscalationOutput.model_validate_json(clean_json)
