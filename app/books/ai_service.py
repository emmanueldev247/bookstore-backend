"""Cohere AI service for generating book summaries."""
import os
import cohere

from flask import current_app
from app.error_handlers import InvalidUsage


_COHERE_API_KEY = os.getenv("COHERE_API_KEY")
_co_client_v2 = None


def _ensure_cohere_client():
    """Ensure the Cohere client is initialized."""
    global _co_client_v2

    if _co_client_v2 is None:
        if not _COHERE_API_KEY:
            current_app.logger.error(
                "Cohere API key not configured. Set COHERE_API_KEY in env.",
            )
            raise InvalidUsage(
                message="Cohere API key not configured (set COHERE_API_KEY).",
                status_code=500,
            )
        try:

            _co_client_v2 = cohere.ClientV2(api_key=_COHERE_API_KEY)
        except Exception as e:
            current_app.logger.error(
                f"Failed to initialize Cohere ClientV2: {str(e)}"
            )
            raise InvalidUsage(
                message=f"Failed to initialize Cohere ClientV2: {str(e)}",
                status_code=500,
            )


def generate_summary(book):
    """Generate a summary of a book using Cohere’s text generation."""
    # 1) Ensure client is initialized
    _ensure_cohere_client()

    # 2) Ensure book has both title and author
    if not book.title or not book.author:
        current_app.logger.error(
            "Cannot generate summary without both title and author."
        )
        raise InvalidUsage(
            message="Cannot generate summary without both title and author.",
            status_code=400,
        )

    # 3) Build prompt
    title = book.title
    author = book.author
    description = book.description

    user_prompt = (
        f"Please provide a detailed summary of the following "
        f"book, using up to 250 tokens:\n"
        f"Title: {title}\n"
        f"Author: {author}\n"
        f"Description: {description}\n\n"
        f"Summary:"
    )

    # 4) Call Cohere
    try:
        response = _co_client_v2.chat(
            model="command-a-03-2025",
            messages=[{"role": "user", "content": user_prompt}],
            temperature=0.7,
            max_tokens=300,
        )
    except Exception as e:
        current_app.logger.error(f"Cohere API error: {str(e)}")
        # Any failure (network, invalid key, model error, etc.)
        raise InvalidUsage(
            message=f"Cohere API error: {str(e)}",
            status_code=502,
        )

    # 5) Extract text
    try:
        assistant_parts = response.message.content
        if not assistant_parts or not isinstance(assistant_parts, list):
            current_app.logger.error(
                "Cohere response content is empty or malformed."
            )
            raise ValueError("Empty or malformed response from Cohere Chat")

        first_part = assistant_parts[0]
        if not hasattr(first_part, "text"):
            current_app.logger.error(
                "Cohere response item has no 'text' attribute."
            )
            raise ValueError("Cohere response item has no 'text' attribute")

        summary_text = first_part.text.strip()
        if not summary_text:
            raise ValueError("Cohere returned an empty summary.")
    except Exception as e:
        raise InvalidUsage(
            message=f"Cohere returned unexpected content format: {str(e)}",
            status_code=502,
        )

    return summary_text
