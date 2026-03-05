"""Tests for Turn-it-in-AI."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

# Ensure required env vars are set before importing the app module
os.environ.setdefault("SECRET_KEY", "test-secret-for-pytest")
os.environ.setdefault("OPENAI_API_KEY", "test-key-for-pytest")

from submission import SubmissionResult  # noqa: E402
from app import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as c:
        yield c


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

class TestIndexRoute:
    def test_get_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert b"Turn-it-in-AI" in response.data

    def test_index_contains_form(self, client):
        response = client.get("/")
        assert b"assignment_text" in response.data


class TestCompleteRoute:
    def test_empty_text_redirects(self, client):
        response = client.post("/complete", data={"assignment_text": ""})
        assert response.status_code == 302
        assert response.headers["Location"] == "/"

    def test_whitespace_only_redirects(self, client):
        response = client.post("/complete", data={"assignment_text": "   "})
        assert response.status_code == 302

    @patch("app.complete_assignment")
    def test_successful_completion(self, mock_complete, client):
        mock_complete.return_value = "Here is the completed answer."
        response = client.post(
            "/complete",
            data={"assignment_text": "What is 2 + 2?"},
        )
        assert response.status_code == 200
        assert b"Here is the completed answer." in response.data
        assert b"What is 2 + 2?" in response.data
        mock_complete.assert_called_once_with("What is 2 + 2?")

    @patch("app.complete_assignment")
    def test_api_error_shows_flash(self, mock_complete, client):
        mock_complete.side_effect = ValueError("OPENAI_API_KEY is not set.")
        response = client.post(
            "/complete",
            data={"assignment_text": "Some assignment"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"OPENAI_API_KEY is not set." in response.data


class TestSubmitRoute:
    def test_no_completed_text_redirects(self, client):
        response = client.post(
            "/submit",
            data={"completed_text": "", "submission_type": "canvas"},
        )
        assert response.status_code == 302
        assert response.headers["Location"] == "/"

    def test_canvas_missing_ids_redirects(self, client):
        response = client.post(
            "/submit",
            data={
                "completed_text": "My answer.",
                "submission_type": "canvas",
                "course_id": "",
                "assignment_id": "",
            },
        )
        assert response.status_code == 302

    @patch("app.submit_to_canvas")
    def test_canvas_success(self, mock_submit, client):
        mock_submit.return_value = SubmissionResult(
            success=True,
            message="Assignment submitted successfully via Canvas.",
        )
        response = client.post(
            "/submit",
            data={
                "completed_text": "My completed answer.",
                "submission_type": "canvas",
                "course_id": "123",
                "assignment_id": "456",
            },
        )
        assert response.status_code == 200
        assert b"Turned In" in response.data
        mock_submit.assert_called_once_with("123", "456", "My completed answer.")

    @patch("app.submit_to_url")
    def test_generic_url_success(self, mock_submit, client):
        mock_submit.return_value = SubmissionResult(
            success=True,
            message="Assignment submitted successfully to https://example.com/submit.",
        )
        response = client.post(
            "/submit",
            data={
                "completed_text": "My completed answer.",
                "submission_type": "generic",
                "endpoint_url": "https://example.com/submit",
            },
        )
        assert response.status_code == 200
        assert b"Turned In" in response.data

    @patch("app.submit_to_canvas")
    def test_canvas_failure_shown(self, mock_submit, client):
        mock_submit.return_value = SubmissionResult(
            success=False,
            message="Canvas submission failed: 401 Unauthorized",
        )
        response = client.post(
            "/submit",
            data={
                "completed_text": "My completed answer.",
                "submission_type": "canvas",
                "course_id": "123",
                "assignment_id": "456",
            },
        )
        assert response.status_code == 200
        assert b"Submission Failed" in response.data


# ---------------------------------------------------------------------------
# AI completion unit tests
# ---------------------------------------------------------------------------

class TestAiCompletion:
    def test_empty_text_raises(self):
        from ai_completion import complete_assignment
        with pytest.raises(ValueError, match="must not be empty"):
            complete_assignment("")

    def test_whitespace_only_raises(self):
        from ai_completion import complete_assignment
        with pytest.raises(ValueError):
            complete_assignment("   ")

    def test_missing_api_key_raises(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from ai_completion import get_client
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_client()

    @patch("ai_completion.get_client")
    def test_calls_openai(self, mock_get_client):
        mock_choice = MagicMock()
        mock_choice.message.content = "The answer is 42."
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        from ai_completion import complete_assignment
        result = complete_assignment("What is the answer to everything?")

        assert result == "The answer is 42."
        mock_client.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# Submission unit tests
# ---------------------------------------------------------------------------

class TestSubmission:
    def test_canvas_no_config_returns_failure(self, monkeypatch):
        monkeypatch.delenv("CANVAS_BASE_URL", raising=False)
        monkeypatch.delenv("CANVAS_ACCESS_TOKEN", raising=False)
        from submission import submit_to_canvas
        result = submit_to_canvas("1", "2", "My answer")
        assert not result.success
        assert "Canvas is not configured" in result.message

    def test_generic_invalid_url_returns_failure(self):
        from submission import submit_to_url
        result = submit_to_url("not-a-url", "My answer")
        assert not result.success
        assert "valid public" in result.message

    def test_generic_private_ip_blocked(self):
        from submission import submit_to_url
        result = submit_to_url("http://127.0.0.1/submit", "My answer")
        assert not result.success
        assert "valid public" in result.message

    @patch("submission.requests.post")
    def test_canvas_http_success(self, mock_post, monkeypatch):
        monkeypatch.setenv("CANVAS_BASE_URL", "https://canvas.example.com")
        monkeypatch.setenv("CANVAS_ACCESS_TOKEN", "test-token")
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 99}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from submission import submit_to_canvas
        result = submit_to_canvas("10", "20", "Answer text")

        assert result.success
        assert "Canvas" in result.message
        mock_post.assert_called_once()

    @patch("submission._is_safe_url", return_value=True)
    @patch("submission.requests.post")
    def test_generic_url_success(self, mock_post, _mock_safe):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        from submission import submit_to_url
        result = submit_to_url("https://example.com/submit", "Answer text")

        assert result.success
        mock_post.assert_called_once()

    @patch("submission.requests.post")
    def test_canvas_http_error(self, mock_post, monkeypatch):
        import requests as req
        monkeypatch.setenv("CANVAS_BASE_URL", "https://canvas.example.com")
        monkeypatch.setenv("CANVAS_ACCESS_TOKEN", "bad-token")
        err_response = MagicMock()
        err_response.status_code = 401
        http_error = req.HTTPError(response=err_response)
        mock_post.return_value.raise_for_status.side_effect = http_error

        from submission import submit_to_canvas
        result = submit_to_canvas("10", "20", "Answer text")

        assert not result.success
        assert "failed" in result.message.lower()
