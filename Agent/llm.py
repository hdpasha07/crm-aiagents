import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

def get_llm(model: str = None, temperature: float = 0):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("🚨 GEMINI_API_KEY not found! Check your .env file.")

    model_name = model or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    return ChatGoogleGenerativeAI(
        model=model_name,
        temperature=temperature,
        google_api_key=api_key
    )