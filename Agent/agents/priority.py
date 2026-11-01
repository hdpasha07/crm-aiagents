from langchain_core.prompts import ChatPromptTemplate
from ..schemas.priority import PriorityOutput
from ..llm import get_llm
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a priority assessment agent.

Complaint:
{complaint}

Category: {category}
Sentiment: {sentiment}
                                          
Example:
{{"priority": "high", "reason": "Payment issue with angry sentiment"}}


Rules:
- Angry + payment or delivery = high
- Neutral feedback = low
- Otherwise = medium

You MUST return valid JSON with EXACTLY these fields:
- priority: one of ["low", "medium", "high"]
- reason: a short explanation of WHY this priority was chosen

Return ONLY JSON. No markdown. No extra fields.
""")

def assign_priority(complaint, category, sentiment) -> PriorityOutput:
    response = llm.invoke(
        prompt.format_messages(
            complaint=complaint,
            category=category,
            sentiment=sentiment
        )
    )

    clean_json = extract_json(response.content)
    return PriorityOutput.model_validate_json(clean_json)
