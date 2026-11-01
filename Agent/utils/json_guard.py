import json
import re

def extract_json(text: str) -> str:
# --- NEW: Safely handle LangChain returning a list of blocks ---
    if isinstance(text, list):
        # Loop through the blocks and extract the actual string text
        text = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item) 
            for item in text
        )
    # ---------------------------------------------------------------
    """
    Extract and validate JSON from LLM output.
    Fails explicitly if JSON is missing.
    """
    if not text or not text.strip():
        raise ValueError("LLM returned empty response, expected JSON")

    text = text.strip()

    # Remove markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text)
        text = re.sub(r"```$", "", text)
        text = text.strip()

    # Ensure it looks like JSON
    if not (text.startswith("{") and text.endswith("}")):
        raise ValueError(f"LLM output is not valid JSON: {text}")

    # Validate JSON
    json.loads(text)
    return text