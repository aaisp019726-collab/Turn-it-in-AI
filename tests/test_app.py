"""Tests for the Flask application routes."""

import pytest

import app as flask_app_module


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    flask_app_module.app.config["TESTING"] = True
    flask_app_module.app.config["WTF_CSRF_ENABLED"] = False
    with flask_app_module.app.test_client() as c:
        yield c


def test_index_get(client):
    """GET / should return 200 with the assignment form."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Turn-it-in-AI" in response.data
    assert b"assignment_text" in response.data


def test_complete_missing_text(client):
    """POST /complete with no text should redirect back to index with error."""
    response = client.post("/complete", data={"assignment_text": ""}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please provide assignment instructions" in response.data


def test_complete_success(client, monkeypatch):
    """POST /complete with valid text should call AI and show result page."""
    monkeypatch.setattr(
        "app.complete_assignment",
        lambda text: "Here is the completed assignment.",
    )

    response = client.post(
        "/complete",
        data={
            "assignment_text": "Write about the solar system.",
            "course_id": "42",
            "assignment_id": "99",
        },
    )
    assert response.status_code == 200
    assert b"Here is the completed assignment." in response.data
    assert b"Submit to Canvas" in response.data


def test_complete_ai_failure(client, monkeypatch):
    """POST /complete should redirect to index if AI raises an exception."""
    def boom(text):
        raise RuntimeError("OpenAI down")

    monkeypatch.setattr("app.complete_assignment", boom)

    response = client.post(
        "/complete",
        data={"assignment_text": "Some assignment"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"AI completion failed" in response.data


def test_submit_missing_text(client):
    """POST /submit with no completed text should redirect with error."""
    response = client.post(
        "/submit",
        data={"completed_text": "", "course_id": "", "assignment_id": ""},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"No completed assignment" in response.data


def test_submit_no_canvas_credentials(client, monkeypatch):
    """POST /submit without Canvas env vars should flash an error."""
    monkeypatch.delenv("CANVAS_BASE_URL", raising=False)
    monkeypatch.delenv("CANVAS_API_TOKEN", raising=False)

    response = client.post(
        "/submit",
        data={
            "completed_text": "My answer",
            "course_id": "1",
            "assignment_id": "2",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Canvas credentials are not configured" in response.data


def test_submit_missing_ids(client, monkeypatch):
    """POST /submit without course/assignment IDs should flash an error."""
    monkeypatch.setenv("CANVAS_BASE_URL", "https://canvas.example.com")
    monkeypatch.setenv("CANVAS_API_TOKEN", "tok")

    response = client.post(
        "/submit",
        data={
            "completed_text": "My answer",
            "course_id": "",
            "assignment_id": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Course ID and Assignment ID are required" in response.data


def test_submit_success(client, monkeypatch):
    """POST /submit with valid data should call Canvas and show submitted page."""
    monkeypatch.setenv("CANVAS_BASE_URL", "https://canvas.example.com")
    monkeypatch.setenv("CANVAS_API_TOKEN", "tok")

    fake_result = {"id": 55, "submitted_at": "2026-03-05T12:00:00Z", "workflow_state": "submitted"}

    class FakeClient:
        def submit_assignment(self, course_id, assignment_id, submission_body):
            return fake_result

    monkeypatch.setattr("app.CanvasClient", lambda **kwargs: FakeClient())

    response = client.post(
        "/submit",
        data={
            "completed_text": "My completed answer",
            "course_id": "10",
            "assignment_id": "20",
        },
    )
    assert response.status_code == 200
    assert b"Assignment Submitted" in response.data


def test_submit_canvas_error(client, monkeypatch):
    """POST /submit should flash error if Canvas submission fails."""
    monkeypatch.setenv("CANVAS_BASE_URL", "https://canvas.example.com")
    monkeypatch.setenv("CANVAS_API_TOKEN", "tok")

    from lms import SubmissionError

    class FakeClient:
        def submit_assignment(self, course_id, assignment_id, submission_body):
            raise SubmissionError("Canvas returned 422")

    monkeypatch.setattr("app.CanvasClient", lambda **kwargs: FakeClient())

    response = client.post(
        "/submit",
        data={
            "completed_text": "My answer",
            "course_id": "10",
            "assignment_id": "20",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Submission failed" in response.data
