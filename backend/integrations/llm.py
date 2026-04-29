# backend/ai_engine/summariser_ai.py

import requests


def llm_summarise(text: str) -> str:
    """
    Calls local Ollama model for summarisation.
    Enforces clean output without intro phrases.
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": f"""
Summarize the following in strictly 2-3 professional sentences.

Do NOT:
- Add any introduction
- Write phrases like "Here is the summary", "Certainly", etc.
- Infer or expand any dates
- Assume US date format

Only output the summary itself.

TEXT:
{text}
""",
                "stream": False
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json().get("response", "").strip()

            # 🔥 Safety cleanup: remove unwanted intro phrases just in case
            unwanted_phrases = [
                "Here is a professional summary",
                "Here is the summary",
                "Certainly",
                "Below is the summary",
            ]

            for phrase in unwanted_phrases:
                if result.startswith(phrase):
                    result = result[len(phrase):].strip(" :-\n")

            return result

        return text[:300]

    except Exception:
        return text[:300]