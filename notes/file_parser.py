"""Parse text content from uploaded note/assignment files."""

import os

SUPPORTED_EXTENSIONS = {".txt"}


def parse_file(file_field) -> str:
    """Return the text content of *file_field* (a Django FieldFile).

    Only plain-text (``.txt``) files are supported.  Other formats raise
    ``ValueError``.  If the file cannot be read an ``OSError`` is raised.
    """
    name = file_field.name or ""
    ext = os.path.splitext(name)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. "
            f"Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    file_field.open("rb")
    try:
        raw = file_field.read()
    finally:
        file_field.close()

    return raw.decode("utf-8", errors="replace")
