"""Tests for the AI completion module."""

import pytest


def test_complete_assignment_empty_raises(monkeypatch):
    """complete_assignment should raise ValueError for empty input."""
    from ai import complete_assignment

    with pytest.raises(ValueError, match="must not be empty"):
        complete_assignment("")


def test_complete_assignment_calls_claude(monkeypatch):
    """complete_assignment should call the Anthropic API and return text."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    # Mock the Anthropic client
    class FakeTextBlock:
        text = "This is the completed assignment."

    class FakeMessage:
        content = [FakeTextBlock()]

    class FakeMessages:
        def create(self, **kwargs):
            return FakeMessage()

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr("ai.anthropic.Anthropic", lambda **kwargs: FakeClient())

    from ai import complete_assignment

    result = complete_assignment("Write an essay about the water cycle.")
    assert result == "This is the completed assignment."


def test_complete_assignment_propagates_api_error(monkeypatch):
    """complete_assignment should propagate errors from the Anthropic API."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class FakeMessages:
        def create(self, **kwargs):
            raise RuntimeError("API quota exceeded")

    class FakeClient:
        messages = FakeMessages()

    monkeypatch.setattr("ai.anthropic.Anthropic", lambda **kwargs: FakeClient())

    from ai import complete_assignment

    with pytest.raises(RuntimeError, match="API quota exceeded"):
        complete_assignment("Describe photosynthesis.")
