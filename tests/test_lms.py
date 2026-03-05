"""Tests for the Canvas LMS client."""

import pytest
import requests

from lms import CanvasClient, SubmissionError


def test_submit_assignment_success(requests_mock):
    """submit_assignment should return the JSON response on success."""
    base_url = "https://canvas.example.com"
    course_id = "101"
    assignment_id = "202"
    api_token = "test-token"
    fake_response = {
        "id": 999,
        "submitted_at": "2026-03-05T12:00:00Z",
        "workflow_state": "submitted",
    }

    requests_mock.post(
        f"{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
        json=fake_response,
        status_code=201,
    )

    client = CanvasClient(base_url=base_url, api_token=api_token)
    result = client.submit_assignment(
        course_id=course_id,
        assignment_id=assignment_id,
        submission_body="My completed essay.",
    )

    assert result["id"] == 999
    assert result["workflow_state"] == "submitted"


def test_submit_assignment_api_error(requests_mock):
    """submit_assignment should raise SubmissionError on non-2xx responses."""
    base_url = "https://canvas.example.com"

    requests_mock.post(
        f"{base_url}/api/v1/courses/1/assignments/2/submissions",
        status_code=422,
        text="Unprocessable Entity",
    )

    client = CanvasClient(base_url=base_url, api_token="token")
    with pytest.raises(SubmissionError, match="422"):
        client.submit_assignment(
            course_id="1",
            assignment_id="2",
            submission_body="answer",
        )


def test_submit_assignment_network_error(requests_mock):
    """submit_assignment should raise SubmissionError on network errors."""
    base_url = "https://canvas.example.com"

    requests_mock.post(
        f"{base_url}/api/v1/courses/1/assignments/2/submissions",
        exc=requests.ConnectionError("connection refused"),
    )

    client = CanvasClient(base_url=base_url, api_token="token")
    with pytest.raises(SubmissionError, match="Network error"):
        client.submit_assignment(
            course_id="1",
            assignment_id="2",
            submission_body="answer",
        )


def test_canvas_client_strips_trailing_slash():
    """CanvasClient should strip trailing slashes from base_url."""
    client = CanvasClient(base_url="https://canvas.example.com/", api_token="tok")
    assert client.base_url == "https://canvas.example.com"
