"""
Turn-it-in-AI: Flask application that accepts assignments,
completes them with Anthropic Claude, and submits them automatically.
"""

import os
import logging

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for

from ai import complete_assignment
from lms import CanvasClient, SubmissionError

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")


@app.route("/")
def index():
    """Landing page with the assignment input form."""
    return render_template("index.html")


@app.route("/complete", methods=["POST"])
def complete():
    """Receive assignment details, call AI to complete it, show the result."""
    assignment_text = request.form.get("assignment_text", "").strip()
    course_id = request.form.get("course_id", "").strip()
    assignment_id = request.form.get("assignment_id", "").strip()

    if not assignment_text:
        flash("Please provide assignment instructions.", "error")
        return redirect(url_for("index"))

    try:
        completed = complete_assignment(assignment_text)
    except Exception as exc:
        logger.exception("AI completion failed")
        flash(f"AI completion failed: {exc}", "error")
        return redirect(url_for("index"))

    session["completed_text"] = completed
    session["course_id"] = course_id
    session["assignment_id"] = assignment_id

    return render_template(
        "result.html",
        assignment_text=assignment_text,
        completed_text=completed,
        course_id=course_id,
        assignment_id=assignment_id,
    )


@app.route("/submit", methods=["POST"])
def submit():
    """Submit the completed assignment to Canvas LMS."""
    completed_text = request.form.get("completed_text", "").strip()
    course_id = request.form.get("course_id", "").strip()
    assignment_id = request.form.get("assignment_id", "").strip()

    if not completed_text:
        flash("No completed assignment to submit.", "error")
        return redirect(url_for("index"))

    canvas_url = os.environ.get("CANVAS_BASE_URL", "")
    canvas_token = os.environ.get("CANVAS_API_TOKEN", "")

    if not canvas_url or not canvas_token:
        flash(
            "Canvas credentials are not configured. "
            "Set CANVAS_BASE_URL and CANVAS_API_TOKEN in your environment.",
            "error",
        )
        return render_template(
            "result.html",
            assignment_text="",
            completed_text=completed_text,
            course_id=course_id,
            assignment_id=assignment_id,
        )

    if not course_id or not assignment_id:
        flash("Course ID and Assignment ID are required for submission.", "error")
        return render_template(
            "result.html",
            assignment_text="",
            completed_text=completed_text,
            course_id=course_id,
            assignment_id=assignment_id,
        )

    client = CanvasClient(base_url=canvas_url, api_token=canvas_token)
    try:
        result = client.submit_assignment(
            course_id=course_id,
            assignment_id=assignment_id,
            submission_body=completed_text,
        )
        logger.info("Submission successful: %s", result)
        flash("Assignment submitted successfully!", "success")
        return render_template("submitted.html", submission=result)
    except SubmissionError as exc:
        logger.error("Submission failed: %s", exc)
        flash(f"Submission failed: {exc}", "error")
        return render_template(
            "result.html",
            assignment_text="",
            completed_text=completed_text,
            course_id=course_id,
            assignment_id=assignment_id,
        )


if __name__ == "__main__":
    app.run(debug=False)
