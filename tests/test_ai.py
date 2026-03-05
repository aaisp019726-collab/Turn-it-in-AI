"""Tests for the AI completion module."""

import pytest


def test_complete_assignment_empty_raises(monkeypatch):
    """complete_assignment should raise ValueError for empty input."""
    from ai import complete_assignment

    with pytest.raises(ValueError, match="must not be empty"):
        complete_assignment("")


def test_complete_assignment_calls_openai(monkeypatch):
    """complete_assignment should call the OpenAI API and return text."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Mock the OpenAI client
    class FakeMessage:
        content = "This is the completed assignment."

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletion:
        choices = [FakeChoice()]

    class FakeChatCompletions:
        def create(self, **kwargs):
            return FakeCompletion()

    class FakeChat:
        completions = FakeChatCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr("ai.OpenAI", lambda **kwargs: FakeClient())

    from ai import complete_assignment

    result = complete_assignment("Write an essay about the water cycle.")
    assert result == "This is the completed assignment."


def test_complete_assignment_propagates_api_error(monkeypatch):
    """complete_assignment should propagate errors from the OpenAI API."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class FakeChatCompletions:
        def create(self, **kwargs):
            raise RuntimeError("API quota exceeded")

    class FakeChat:
        completions = FakeChatCompletions()

    class FakeClient:
        chat = FakeChat()

    monkeypatch.setattr("ai.OpenAI", lambda **kwargs: FakeClient())

    from ai import complete_assignment

    with pytest.raises(RuntimeError, match="API quota exceeded"):
        complete_assignment("Describe photosynthesis.")
