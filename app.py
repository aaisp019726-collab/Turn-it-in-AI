"""Main Flask application for Turn-it-in-AI."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from ai_completion import complete_assignment
from submission import submit_to_canvas, submit_to_url

load_dotenv()

app = Flask(__name__)
_secret = os.environ.get("SECRET_KEY")
if not _secret:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Copy .env.example to .env and set a random SECRET_KEY."
    )
app.secret_key = _secret


@app.route("/", methods=["GET"])
def index():
    """Render the main assignment input page."""
    return render_template("index.html")


@app.route("/complete", methods=["POST"])
def complete():
    """Accept an assignment, complete it with AI, and render the result."""
    assignment_text = request.form.get("assignment_text", "").strip()

    if not assignment_text:
        flash("Please enter your assignment text before submitting.", "error")
        return redirect(url_for("index"))

    try:
        completed = complete_assignment(assignment_text)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("index"))

    return render_template(
        "result.html",
        assignment=assignment_text,
        completed=completed,
    )


@app.route("/submit", methods=["POST"])
def submit():
    """Turn in a completed assignment automatically."""
    completed_text = request.form.get("completed_text", "").strip()
    submission_type = request.form.get("submission_type", "canvas")

    if not completed_text:
        flash("No completed assignment text to submit.", "error")
        return redirect(url_for("index"))

    if submission_type == "canvas":
        course_id = request.form.get("course_id", "").strip()
        assignment_id = request.form.get("assignment_id", "").strip()

        if not course_id or not assignment_id:
            flash("Canvas course ID and assignment ID are required.", "error")
            return redirect(url_for("index"))

        result = submit_to_canvas(course_id, assignment_id, completed_text)
    else:
        endpoint_url = request.form.get("endpoint_url", "").strip()
        result = submit_to_url(endpoint_url, completed_text)

    if result.success:
        flash(result.message, "success")
    else:
        flash(result.message, "error")

    return render_template(
        "submitted.html",
        result=result,
        completed=completed_text,
    )


if __name__ == "__main__":
    # Development server only. Use a production WSGI server (e.g. gunicorn) for deployment.
    app.run(debug=False)
