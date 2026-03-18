"""Send text to the Hugging Face Inference API and retrieve generated questions."""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Model used for question generation (free, public Hugging Face model).
HF_MODEL = "vblagoje/bart_lfqa"
HF_API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"

# Maximum number of characters of source text to send in a single request.
MAX_TEXT_LENGTH = 1500

# Timeout for the HTTP request (seconds).
REQUEST_TIMEOUT = 30


def generate_questions_from_text(text: str) -> list[str]:
    """Call the Hugging Face Inference API and return a list of question strings.

    The function trims *text* to ``MAX_TEXT_LENGTH`` characters before sending
    to stay within model limits.

    Raises ``RuntimeError`` if the API key is missing or the request fails.
    """
    api_key = getattr(settings, "HUGGINGFACE_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "HUGGINGFACE_API_KEY is not configured. "
            "Add it to your .env file to use the question-generation feature."
        )

    trimmed = text[:MAX_TEXT_LENGTH].strip()
    if not trimmed:
        return []

    prompt = (
        "Generate a numbered list of important exam questions based on the "
        f"following notes:\n\n{trimmed}"
    )

    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "do_sample": False,
        },
    }

    try:
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error("Hugging Face API request failed: %s", exc)
        raise RuntimeError(f"API request failed: {exc}") from exc

    data = response.json()

    # The API returns a list of dicts with a "generated_text" key.
    if isinstance(data, list) and data:
        raw = data[0].get("generated_text", "")
    elif isinstance(data, dict):
        raw = data.get("generated_text", "")
    else:
        raw = ""

    return _parse_questions(raw)


def _parse_questions(text: str) -> list[str]:
    """Split *text* into individual question strings."""
    questions = []
    for line in text.splitlines():
        line = line.strip()
        # Keep lines that look like numbered questions or end with "?"
        if line and (line[0:1].isdigit() or line.endswith("?")):
            # Strip leading numbering like "1." or "1)"
            for sep in (". ", ") ", ": "):
                if sep in line[:4]:
                    line = line.split(sep, 1)[-1].strip()
                    break
            if line:
                questions.append(line)
    return questions
