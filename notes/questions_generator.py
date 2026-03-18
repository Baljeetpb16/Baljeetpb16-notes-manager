"""Orchestrate file parsing and API calls to generate questions from a Note."""

from .api_integration import generate_questions_from_text
from .file_parser import parse_file
from .models import Note


def generate_questions_for_note(note: Note) -> list[str]:
    """Return important questions generated from *note*'s file content.

    Steps:
    1. Extract text from the uploaded file using :mod:`notes.file_parser`.
    2. Send the text to the Hugging Face API via :mod:`notes.api_integration`.
    3. Return the resulting list of question strings.

    Raises ``ValueError`` for unsupported file types and ``RuntimeError`` when
    the API key is missing or the request fails.
    """
    text = parse_file(note.file)
    return generate_questions_from_text(text)
