"""
AI module: uses OpenAI to complete an assignment.
"""

import os

from openai import OpenAI

_SYSTEM_PROMPT = (
    "You are an expert academic assistant. "
    "When given assignment instructions, produce a complete, well-structured response "
    "that directly addresses all requirements. "
    "Write in clear academic prose. Do not include meta-commentary about what you are doing."
)


def complete_assignment(assignment_text: str) -> str:
    """Use OpenAI to complete the given assignment.

    Args:
        assignment_text: The assignment instructions or questions.

    Returns:
        The completed assignment as a string.

    Raises:
        ValueError: If assignment_text is empty.
        openai.OpenAIError: If the API call fails.
    """
    if not assignment_text:
        raise ValueError("assignment_text must not be empty")

    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": assignment_text},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content
