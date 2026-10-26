import logging
import re
import time

import requests

from config import GROQ_API_KEY

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b"

# Groq's free tier for this model (measured 2026-10-26): 8,000 tokens per
# MINUTE and 1,000 requests per day, shared by every user of the bot. A
# cleanup of a 2-minute clip costs ~1.5-3k tokens, so only a few can run in
# the same minute. When Groq answers 429 it says how long to wait; waiting a
# few seconds and retrying is far better than failing the user's request.
MAX_ATTEMPTS = 3
MAX_WAIT_SECONDS = 25

# "low" cut hidden reasoning tokens from ~430 to ~15 on a cleanup test
# (about a quarter of the total) with no loss for this correction task.
REASONING_EFFORT = "low"


def _seconds_from_header(value: str):
    """'12.12s' -> 12.12, '1m3.5s' -> 63.5, '5' -> 5."""
    match = re.fullmatch(r"(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s?)?", (value or "").strip())
    if not match or not any(match.groups()):
        return None
    return int(match.group(1) or 0) * 60 + float(match.group(2) or 0)


def _retry_wait(response) -> float:
    for header in ("retry-after", "x-ratelimit-reset-tokens"):
        seconds = _seconds_from_header(response.headers.get(header, ""))
        if seconds is not None:
            return seconds
    return 5.0


def chat(prompt: str, temperature: float) -> str:
    """One chat completion, waiting out short rate limits. Raises (so the
    caller can fall back) when the wait would be long - e.g. the daily
    quota - or after MAX_ATTEMPTS."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        response = requests.post(
            GROQ_CHAT_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "reasoning_effort": REASONING_EFFORT,
            },
            timeout=90,
        )

        if response.status_code == 429:
            wait = _retry_wait(response)
            if attempt == MAX_ATTEMPTS or wait > MAX_WAIT_SECONDS:
                logger.warning(f"Groq rate limit - giving up (would need to wait {wait:.0f}s)")
                response.raise_for_status()
            logger.info(f"Groq rate limited - waiting {wait:.1f}s (attempt {attempt}/{MAX_ATTEMPTS})")
            time.sleep(wait + 0.5)
            continue

        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
