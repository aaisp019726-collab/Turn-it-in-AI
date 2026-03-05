# Turn-it-in-AI

An AI app that takes your assignments, completes them using OpenAI, and turns them in fully automatically.

## Features

- Paste any assignment, homework, or exam question into the web UI
- AI (GPT-4o) generates a thorough, well-structured answer
- One-click submission to **Canvas LMS** or any custom HTTP endpoint

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your OPENAI_API_KEY and (optionally) Canvas credentials
```

### 3. Run the app

```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |
| `SECRET_KEY` | ✅ | A random string for Flask session security |
| `CANVAS_BASE_URL` | Optional | Base URL of your Canvas instance, e.g. `https://school.instructure.com` |
| `CANVAS_ACCESS_TOKEN` | Optional | Canvas user access token (for auto-submission) |

## Project Structure

```
app.py              # Flask web application
ai_completion.py    # OpenAI completion logic
submission.py       # Canvas LMS & generic HTTP submission
templates/          # HTML templates
  index.html        # Assignment input page
  result.html       # AI answer + turn-in form
  submitted.html    # Submission confirmation page
tests/
  test_app.py       # Pytest test suite
```

## Running Tests

```bash
pytest tests/ -v
```
