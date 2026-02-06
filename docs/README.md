# OpenAPI Test Generator - Documentation

## Quick Links

- [Main README](../README.md) - Quick start guide
- [Setup Guide](SETUP.md) - Detailed setup instructions
- [Codegen Log](codegen-log.md) - AI tool usage documentation

## Overview

Generate and run pytest tests from OpenAPI specifications.

### Features

- **Upload OpenAPI Specs**: Support for YAML and JSON formats
- **Generate Tests**: Automatically create pytest files with happy path and error tests
- **Run Tests**: Execute tests against any target API
- **View Results**: Detailed pass/fail reporting with failure details
- **Two Modes**: Mock LLM (deterministic) or Real LLM (optional)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Streamlit UI   │────▶│  FastAPI API    │────▶│   SQLite DB     │
│  (port 8501)    │     │  (port 8000)    │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Test Generator │
                        │  (Mock/Real LLM)│
                        └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Pytest Runner  │────▶ Target API
                        └─────────────────┘
```

## Project Structure

```
spec-driven-development/
├── run.py               # Simple runner script (start here!)
├── app/                 # FastAPI backend
│   ├── main.py         # Entry point
│   ├── routes.py       # API endpoints
│   ├── openapi_parser.py
│   ├── generator/      # Test generation
│   ├── runner/         # Test execution
│   └── storage/        # SQLite database
├── streamlit_app/       # Streamlit UI
├── example_api/         # Target API for testing
├── tests/               # Test suite (67 tests)
├── SPECS/               # Feature specifications
├── openapi_specs/       # Sample specs
└── docs/                # Documentation
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| POST | /specs | Upload OpenAPI spec |
| GET | /specs | List all specs |
| GET | /specs/{id} | Get spec details |
| DELETE | /specs/{id} | Delete spec |
| POST | /generate | Generate tests |
| GET | /generations/{id} | Get generation details |
| POST | /runs | Run tests |
| GET | /runs/{id} | Get run results |
| GET | /runs/{id}/junit | Get JUnit XML |

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| DATABASE_PATH | ./data/app.db | SQLite database path |
| GENERATED_TESTS_DIR | ./generated_tests | Output directory |
| DEFAULT_TARGET_URL | http://localhost:8001 | Default API URL |
| LLM_API_KEY | (none) | Enable real LLM mode |

## Mock vs Real LLM

**Mock Mode (default)**:
- Deterministic test generation
- No external API calls
- Ideal for CI/CD

**Real Mode** (set LLM_API_KEY):
- Uses OpenAI/Anthropic for generation
- More varied test scenarios
- Requires API key

## Spec-Driven Development

This project follows spec-first development:
- Every feature has a spec in `SPECS/`
- Implementation follows the spec
- Acceptance criteria are checked off

See [RULES.md](../RULES.md) for details.
