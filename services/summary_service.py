import requests

from config import GROQ_API_KEY
from utils.network_retry import call_sync_with_retry

# Same Groq chat model/endpoint as ai_cleanup_service.py - kept as its own
# small call here (not shared) to match this project's existing pattern
# of each service owning its own Groq call rather than a shared client.
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b"


def _call_groq_chat(prompt: str) -> str:
    response = requests.post(
        GROQ_CHAT_URL,
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        },
        timeout=60,
    )

    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def summarize_transcript(transcript: str) -> str:
    """
    Produce a short bullet-point summary of an already-cleaned transcript,
    in the SAME language as the transcript itself (not the bot's interface
    language) - matches how clean_transcript() also preserves the
    original language, and keeps this independent of a separate
    translation step.
    """

    prompt = f"""
You are summarizing a cleaned speech transcript for someone who hasn't read it.

STRICT RULES:

1. Return ONLY the summary. Do not return anything else.
2. Do NOT add a heading like "Summary:".
3. Do NOT add an introduction or explanation.
4. Write 3 to 5 bullet points, each starting with "• ".
5. Each bullet must be a single, complete, self-contained point.
6. Cover only what is actually in the transcript - never add information,
   opinions, or context that isn't there.
7. Do NOT quote long passages verbatim - paraphrase concisely.
8. Write the summary in the SAME language as the transcript below.

<TRANSCRIPT>
{transcript}
</TRANSCRIPT>

Return ONLY the bullet-point summary.
"""

    summary = call_sync_with_retry(_call_groq_chat, prompt).strip()

    # If the model adds a heading despite the instruction, strip common ones.
    for heading in ("Summary:", "Here is a summary:", "Here's a summary:"):
        position = summary.lower().find(heading.lower())
        if position != -1:
            summary = summary[position + len(heading):].strip()
            break

    return summary
