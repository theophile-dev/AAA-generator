import re
import json

def extract_json_from_llm_answer(answer: str):
    """
    Extracts and parses JSON data from an LLM answer string.
    Handles cases with or without ```json fences and with extra text.
    """
    # Step 1: Remove the "JSON Data:" prefix if present
    cleaned = re.sub(r"^\s*JSON\s+Data:\s*", "", answer, flags=re.IGNORECASE)

    # Step 2: Try to find JSON inside ```json ... ``` fences
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Step 3: No fences — try to find the first JSON object in the text
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in the LLM answer.")
        json_str = match.group(1)

    # Step 4: Try parsing into a Python object
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")

    return data


def extract_html_block(text):
    """
    Extracts the content between <html> and </html> tags from a string.
    Returns the HTML block including the tags, or None if not found.
    """
    match = re.search(r"<html.*?</html>", text, flags=re.DOTALL | re.IGNORECASE)
    return match.group(0) if match else None