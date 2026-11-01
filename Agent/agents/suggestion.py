from langchain_core.prompts import ChatPromptTemplate
from ..schemas.suggestion import SuggestionOutput
from ..llm import get_llm
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a customer support strategy agent.

Complaint:
{complaint}

Category: {category}
Priority: {priority}

Suggest next actions as a list.

Example:
{{"actions": ["Escalate to billing team"]}}

Rules:
- High → escalation, manual review, fast resolution
- Medium → standard support workflow
- Low → acknowledge and monitor

Return valid JSON with:
- actions (list of strings)

Do NOT include markdown.
""")

def suggest_actions(complaint, category, priority) -> SuggestionOutput:
    response = llm.invoke(
        prompt.format_messages(
            complaint=complaint,
            category=category,
            priority=priority
        )
    )

    clean_json = extract_json(response.content)
    return SuggestionOutput.model_validate_json(clean_json)
