from langchain_core.prompts import ChatPromptTemplate
from ..schemas.category import CategoryOutput
from ..llm import get_llm
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a customer support categorization agent.

Complaint:
{complaint}

You MUST classify the complaint into EXACTLY ONE of the following:
- payment_issue
- delivery_issue
- technical_issue
- feedback
- other

You MUST return valid JSON with EXACTLY this field:
- category

Example:
{{"category": "payment_issue"}}

Rules:
- Do NOT use any other field names
- Do NOT include markdown
- Do NOT include explanations
""")

def categorize(complaint: str) -> CategoryOutput:
    response = llm.invoke(
        prompt.format_messages(complaint=complaint)
    )

    clean_json = extract_json(response.content)
    return CategoryOutput.model_validate_json(clean_json)
