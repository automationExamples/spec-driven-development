# OpenAPI Test Generator

Generate and run API tests automatically from OpenAPI specifications.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Mac%20%7C%20Linux-lightgrey.svg)

---

## What This Does

1. **Upload** an OpenAPI spec (YAML or JSON)
2. **Generate** pytest test files automatically
3. **Run** tests against any API
4. **View** results with pass/fail details

---

## Quick Start

### 1. Install Dependencies
```bash
python run.py setup
```

### 2. Start the Application
```bash
python run.py all
```

### 3. Open Your Browser
Go to: **http://localhost:8501**

---

## Usage

| Command | What it does |
|---------|--------------|
| `python run.py setup` | Install dependencies |
| `python run.py all` | Start everything |
| `python run.py test` | Run tests |
| `python run.py help` | Show all commands |

---

## Features

- **Web UI**: Easy-to-use Streamlit interface
- **Multiple LLM Providers**: Mock (default), OpenAI, or Anthropic
- **Cross-platform**: Works on Windows, Mac, and Linux
- **Test Runner**: Execute tests and view detailed results

---

## LLM Providers

Choose your test generation engine:

| Provider | Models | API Key |
|----------|--------|---------|
| **Mock** (default) | Deterministic | Not needed |
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 | Required |
| **Anthropic** | Claude 3 Haiku/Sonnet/Opus | Required |

### Using OpenAI or Anthropic

Set your API key as an environment variable:
```bash
export OPENAI_API_KEY="your-key"      # For OpenAI
export ANTHROPIC_API_KEY="your-key"   # For Anthropic
```

Or enter it directly in the UI when generating tests.

---

## Services

| Service | URL |
|---------|-----|
| Web UI | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| Example API | http://localhost:8001 |

---

## Requirements

- Python 3.10 or higher
- pip (Python package manager)

---

## Documentation

- [Complete Walkthrough](docs/WALKTHROUGH.md) - Step-by-step guide for UI and CLI usage
- [Full Setup Guide](docs/SETUP.md) - Detailed instructions and troubleshooting
- [API Docs](http://localhost:8000/docs) - Interactive API documentation (when running)

---

## Project Structure

```
spec-driven-development/
├── run.py              # Runner script (start here!)
├── app/                # FastAPI backend
├── streamlit_app/      # Web UI (Streamlit)
├── example_api/        # Sample API for testing
├── tests/              # Test suite (67 tests)
├── openapi_specs/      # Example OpenAPI specs
├── SPECS/              # Feature specifications
└── docs/               # Documentation
```

---

## Running Tests

```bash
python run.py test
```

All 67 tests should pass on both Windows and Mac.

---

## Built With

- **FastAPI** - Backend API framework
- **Streamlit** - Web UI framework
- **pytest** - Testing framework
- **httpx** - HTTP client
- **SQLite** - Local database

---

## Development

See [docs/SETUP.md](docs/SETUP.md) for developer setup instructions.

### Quick Dev Commands
```bash
python run.py api       # Backend only
python run.py ui        # UI only
python run.py example   # Example API only
```
