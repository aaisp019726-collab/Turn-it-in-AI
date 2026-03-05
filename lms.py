"""
LMS module: Canvas LMS integration for submitting assignments.
"""

import requests


class SubmissionError(Exception):
    """Raised when a Canvas assignment submission fails."""


class CanvasClient:
    """Thin wrapper around the Canvas REST API."""

    def __init__(self, base_url: str, api_token: str):
        """
        Args:
            base_url: Base URL of the Canvas instance,
                      e.g. ``https://myschool.instructure.com``.
            api_token: Canvas API access token.
        """
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }
        )

    def submit_assignment(
        self, course_id: str, assignment_id: str, submission_body: str
    ) -> dict:
        """Submit a text-entry assignment to Canvas.

        Args:
            course_id: Canvas course ID.
            assignment_id: Canvas assignment ID.
            submission_body: The completed assignment text (HTML or plain text).

        Returns:
            The Canvas API response dict for the created submission.

        Raises:
            SubmissionError: If the Canvas API returns an error.
        """
        url = (
            f"{self.base_url}/api/v1/courses/{course_id}"
            f"/assignments/{assignment_id}/submissions"
        )
        payload = {
            "submission": {
                "submission_type": "online_text_entry",
                "body": submission_body,
            }
        }
        try:
            response = self._session.post(url, json=payload, timeout=30)
        except requests.RequestException as exc:
            raise SubmissionError(f"Network error during submission: {exc}") from exc

        if not response.ok:
            raise SubmissionError(
                f"Canvas API error {response.status_code}: {response.text}"
            )

        return response.json()
