from langchain_core.prompts import ChatPromptTemplate
from Agent.llm import get_llm
from Agent.utils.json_guard import extract_json
from .schema import ResolutionDecision

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a complaint resolution decision agent.

Complaint:
{complaint}

Final Priority: {priority}
Escalation Required: {escalated}

Decision rules:
- Low priority → auto_resolve = true
- Medium priority feedback → auto_resolve = true
- High priority → auto_resolve = false
- Legal, fraud, chargeback → auto_resolve = false

Return valid JSON with EXACTLY:
- auto_resolve (true/false)
- reason

Example:
{{"auto_resolve": true, "reason": "Low priority feedback complaint"}}
""")

def decide_resolution(complaint, priority, escalated) -> ResolutionDecision:
    response = llm.invoke(
        prompt.format_messages(
            complaint=complaint,
            priority=priority,
            escalated=escalated
        )
    )

    clean_json = extract_json(response.content)
    return ResolutionDecision.model_validate_json(clean_json)
