"""
AI module: uses Anthropic Claude to complete an assignment.
"""

import os

import anthropic

_SYSTEM_PROMPT = (
    "You are an expert academic assistant. "
    "When given assignment instructions, produce a complete, well-structured response "
    "that directly addresses all requirements. "
    "Write in clear academic prose. Do not include meta-commentary about what you are doing."
)


def complete_assignment(assignment_text: str) -> str:
    """Use Anthropic Claude to complete the given assignment.

    Args:
        assignment_text: The assignment instructions or questions.

    Returns:
        The completed assignment as a string.

    Raises:
        ValueError: If assignment_text is empty.
        anthropic.APIError: If the API call fails.
    """
    if not assignment_text:
        raise ValueError("assignment_text must not be empty")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": assignment_text},
        ],
    )

    return message.content[0].text
