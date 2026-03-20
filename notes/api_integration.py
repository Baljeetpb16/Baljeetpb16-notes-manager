"""Send text to the Google Gemini API and retrieve generated questions or summaries."""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 1500
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def _call_gemini(prompt: str) -> str:
    """Send a prompt to Gemini and return the response text."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured. "
            "Add it to your environment variables to use AI features."
        )

    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(
            f"{GEMINI_API_URL}?key={api_key}",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Gemini API request failed: %s", exc)
        raise RuntimeError(f"API request failed: {exc}") from exc

    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return ""


def generate_questions_from_text(text: str) -> list[str]:
    """Call Gemini API and return a list of question strings."""
    trimmed = text[:MAX_TEXT_LENGTH].strip()
    if not trimmed:
        return []

    prompt = (
        "Generate a numbered list of 10 important exam questions based on "
        f"the following notes:\n\n{trimmed}"
    )

    raw = _call_gemini(prompt)
    return _parse_questions(raw)


def summarize_text(text: str) -> str:
    """Call Gemini API and return a summary string."""
    trimmed = text[:MAX_TEXT_LENGTH].strip()
    if not trimmed:
        return ""

    prompt = f"Summarize the following notes in 3-5 clear sentences:\n\n{trimmed}"

    return _call_gemini(prompt)


def _parse_questions(text: str) -> list[str]:
    """Split text into individual question strings."""
    questions = []
    for line in text.splitlines():
        line = line.strip()
        if line and (line[0:1].isdigit() or line.endswith("?")):
            for sep in (". ", ") ", ": "):
                if sep in line[:4]:
                    line = line.split(sep, 1)[-1].strip()
                    break
            if line:
                questions.append(line)
    return questions
