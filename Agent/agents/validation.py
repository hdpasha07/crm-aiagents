from langchain_core.prompts import ChatPromptTemplate
from ..llm import get_llm
from ..schemas.validation import ValidationOutput
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a validation agent for an E-COMMERCE CUSTOMER SUPPORT SYSTEM.

Your job is to decide whether the user input is a VALID support request.

The request is VALID only if:
- It is related to e-commerce operations (orders, payments, delivery, refunds, products, account)
- It expresses an issue, complaint, feedback, or support request
- It is NOT casual conversation, jokes, general questions, or unrelated topics

INVALID examples:
- jokes, poems, chit-chat
- sports, politics, general knowledge
- greetings only ("hi", "hello")
- random or meaningless text

VALID examples:
- payment deducted but order not created
- delivery delayed for my order
- wrong product received
- feedback about product quality

Return STRICT JSON only.

Format:
{{
  "is_valid": true | false,
  "reason": "short explanation"
}}

User input:
{complaint}
""")

def validate_complaint(complaint_text: str) -> ValidationOutput:
    response = llm.invoke(
        prompt.format_messages(complaint=complaint_text)
    )

    clean_json = extract_json(response.content)
    return ValidationOutput.model_validate_json(clean_json)
