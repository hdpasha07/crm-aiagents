from langchain_core.prompts import ChatPromptTemplate
from ..schemas.sentiment import SentimentOutput
from ..llm import get_llm
from ..utils.json_guard import extract_json

llm = get_llm()

prompt = ChatPromptTemplate.from_template("""
You are a sentiment analysis agent.

Complaint:
{complaint}

Classify sentiment as EXACTLY one of:
- angry
- neutral
- chill

Return valid JSON with EXACTLY this field:
- sentiment

Example:
{{"sentiment": "angry"}}

Rules:
- No markdown
- No extra fields
""")

def analyze_sentiment(complaint: str) -> SentimentOutput:
    response = llm.invoke(
        prompt.format_messages(complaint=complaint)
    )

    clean_json = extract_json(response.content)
    return SentimentOutput.model_validate_json(clean_json)
