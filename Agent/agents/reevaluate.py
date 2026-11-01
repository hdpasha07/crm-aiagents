from langchain_core.prompts import ChatPromptTemplate
from ..schemas.reevaluation import ReevaluationOutput
from ..llm import get_llm
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a complaint re-evaluation agent.

Complaint:
{complaint}

Original Priority: {priority}
Response Drafted: {response}
Suggested Actions: {actions}

TASK:
Re-evaluate the urgency AFTER drafting the response.

IMPORTANT RULES:
- You MUST choose updated_priority from ONLY these values:
  ["low", "medium", "high"]
- Do NOT invent new labels like "critical" or "urgent"
- If it feels extremely urgent, choose "high"

Return valid JSON with EXACTLY:
- updated_priority
- reason

Example:
{{"updated_priority": "high", "reason": "Issue remains unresolved and customer is dissatisfied"}}
""")

def reevaluate_priority(complaint, priority, response, actions):
    llm_response = llm.invoke(
        prompt.format_messages(
            complaint=complaint,
            priority=priority,
            response=response,
            actions=actions
        )
    )

    clean_json = extract_json(llm_response.content)
    return ReevaluationOutput.model_validate_json(clean_json)
