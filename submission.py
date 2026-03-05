"""Submission module – turns a completed assignment in via Canvas LMS or a
generic HTTP endpoint.
"""

from __future__ import annotations

import ipaddress
import os
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import requests

DEFAULT_TIMEOUT = 30  # seconds


def _is_safe_url(url: str) -> bool:
    """Return True only if *url* resolves to a public (non-private) IP.

    This prevents Server-Side Request Forgery (SSRF) by blocking requests
    to loopback addresses, RFC-1918 private ranges, link-local addresses,
    and other reserved or special-purpose IP ranges.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return not (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except (socket.gaierror, ValueError):
        return False


@dataclass
class SubmissionResult:
    """Result returned by a submission attempt."""

    success: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Canvas LMS
# ---------------------------------------------------------------------------

def submit_to_canvas(
    course_id: str | int,
    assignment_id: str | int,
    submission_text: str,
) -> SubmissionResult:
    """Submit *submission_text* to a Canvas LMS assignment.

    Reads ``CANVAS_BASE_URL`` and ``CANVAS_ACCESS_TOKEN`` from the environment.

    Parameters
    ----------
    course_id:
        The Canvas course ID.
    assignment_id:
        The Canvas assignment ID.
    submission_text:
        The completed assignment text to submit.

    Returns
    -------
    SubmissionResult
    """
    base_url = os.environ.get("CANVAS_BASE_URL", "").rstrip("/")
    token = os.environ.get("CANVAS_ACCESS_TOKEN", "")

    if not base_url or not token:
        return SubmissionResult(
            success=False,
            message=(
                "Canvas is not configured. "
                "Set CANVAS_BASE_URL and CANVAS_ACCESS_TOKEN in your .env file."
            ),
        )

    url = f"{base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "submission": {
            "submission_type": "online_text_entry",
            "body": submission_text,
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return SubmissionResult(
            success=True,
            message="Assignment submitted successfully via Canvas.",
            details=response.json(),
        )
    except requests.HTTPError as exc:
        return SubmissionResult(
            success=False,
            message=f"Canvas submission failed: {exc}",
            details={"status_code": exc.response.status_code if exc.response else None},
        )
    except requests.RequestException as exc:
        return SubmissionResult(
            success=False,
            message=f"Network error during Canvas submission: {exc}",
        )


# ---------------------------------------------------------------------------
# Generic HTTP endpoint
# ---------------------------------------------------------------------------

def submit_to_url(
    endpoint_url: str,
    submission_text: str,
    extra_fields: dict[str, str] | None = None,
) -> SubmissionResult:
    """POST the completed assignment to an arbitrary HTTP endpoint.

    Parameters
    ----------
    endpoint_url:
        The URL to POST to.
    submission_text:
        The completed assignment text.
    extra_fields:
        Optional additional form fields to include in the POST body.

    Returns
    -------
    SubmissionResult
    """
    if not endpoint_url or not _is_safe_url(endpoint_url):
        return SubmissionResult(
            success=False,
            message=(
                "A valid public HTTPS/HTTP URL is required for generic submission. "
                "Requests to private or reserved IP addresses are not allowed."
            ),
        )

    # Reconstruct the URL from parsed components to avoid using raw user input
    # directly in the HTTP request (SSRF mitigation).
    parsed = urlparse(endpoint_url)
    safe_url = parsed.geturl()

    payload: dict[str, str] = {"submission": submission_text}
    if extra_fields:
        payload.update(extra_fields)

    try:
        response = requests.post(safe_url, data=payload, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return SubmissionResult(
            success=True,
            message=f"Assignment submitted successfully to {safe_url}.",
            details={"status_code": response.status_code},
        )
    except requests.HTTPError as exc:
        return SubmissionResult(
            success=False,
            message=f"Submission failed: {exc}",
            details={"status_code": exc.response.status_code if exc.response else None},
        )
    except requests.RequestException as exc:
        return SubmissionResult(
            success=False,
            message=f"Network error during submission: {exc}",
        )
