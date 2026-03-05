"""AI completion module using the OpenAI API."""

from __future__ import annotations

import os

from openai import OpenAI


def get_client() -> OpenAI:
    """Return an OpenAI client configured from the environment."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Copy .env.example to .env and add your key."
        )
    return OpenAI(api_key=api_key)


def complete_assignment(assignment_text: str, model: str = "gpt-4o") -> str:
    """Send *assignment_text* to the AI and return the completed response.

    Parameters
    ----------
    assignment_text:
        The full text of the assignment or question(s) to be completed.
    model:
        OpenAI model to use.  Defaults to ``gpt-4o``.

    Returns
    -------
    str
        The AI-generated answer / completed assignment text.
    """
    if not assignment_text or not assignment_text.strip():
        raise ValueError("Assignment text must not be empty.")

    client = get_client()

    system_prompt = (
        "You are a helpful academic assistant. "
        "The user will give you an assignment, homework problem, or exam question. "
        "Provide a thorough, well-structured, and accurate answer. "
        "Use clear headings and paragraphs where appropriate."
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": assignment_text.strip()},
        ],
    )

    return response.choices[0].message.content or ""
