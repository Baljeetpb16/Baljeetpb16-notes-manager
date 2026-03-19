"""
Extractive text summarizer.

Uses a simple TF-IDF-inspired sentence scoring approach that requires no
external model downloads or heavy dependencies.
"""

import re
from collections import Counter


def _tokenize(text: str) -> list[str]:
    """Return lowercase word tokens, stripping punctuation."""
    return re.findall(r"[a-z]+", text.lower())


def _sentence_split(text: str) -> list[str]:
    """Split *text* into a list of non-empty sentences."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def summarize(text: str, num_sentences: int = 3) -> str:
    """Return an extractive summary of *text*.

    Args:
        text: Source text to summarize.
        num_sentences: Maximum number of sentences to include in the summary.

    Returns:
        A string containing the most important sentences from the source text,
        joined with spaces.  If *text* is too short to summarize, it is
        returned unchanged.
    """
    if not text or not text.strip():
        return ""

    sentences = _sentence_split(text)
    if len(sentences) <= num_sentences:
        return text.strip()

    # Build word frequency table (simple term-frequency proxy).
    words = _tokenize(text)
    freq: Counter = Counter(words)
    max_freq = max(freq.values()) if freq else 1

    # Score each sentence by the sum of normalised word frequencies.
    scores: dict[int, float] = {}
    for idx, sentence in enumerate(sentences):
        sentence_words = _tokenize(sentence)
        if not sentence_words:
            scores[idx] = 0.0
            continue
        score = sum(freq[w] / max_freq for w in sentence_words)
        # Slightly penalise very short sentences.
        scores[idx] = score / max(len(sentence_words), 1)

    # Pick the top-N highest-scoring sentence *indices* and restore order.
    top_indices = sorted(
        sorted(scores, key=scores.__getitem__, reverse=True)[:num_sentences]
    )
    return " ".join(sentences[i] for i in top_indices)
