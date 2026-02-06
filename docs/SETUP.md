# OpenAPI Test Generator - Setup & Usage Guide

A tool that generates and runs API tests from OpenAPI specifications.

---

## LLM Providers

This tool supports multiple LLM providers for test generation:

| Provider | Description | API Key Required |
|----------|-------------|------------------|
| **Mock** (default) | Deterministic generation, no API calls | No |
| **OpenAI** | GPT-4, GPT-4o, GPT-3.5 | Yes |
| **Anthropic** | Claude 3 (Haiku, Sonnet, Opus) | Yes |

### Setting Up API Keys

**Option 1: Environment Variables (Recommended)**
```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-key"

# Optional: Set default provider
export LLM_PROVIDER="openai"  # or "anthropic" or "mock"
```

**Option 2: Enter in UI**
- Select provider in the Generate Tests page
- Enter your API key directly (not stored)

---

## Quick Start (3 Steps)

### Step 1: Install Python
Make sure you have **Python 3.10 or higher** installed.

Check your version:
```bash
python --version
```

If you don't have Python, download it from: https://www.python.org/downloads/

### Step 2: Install Dependencies
Open a terminal/command prompt in this folder and run:

```bash
python run.py setup
```

### Step 3: Start the Application
```bash
python run.py all
```

Then open your browser to: **http://localhost:8501**

That's it! You're ready to use the application.

---

## How to Use the Application

### 1. Upload an OpenAPI Spec
- Go to the **"Upload Spec"** page in the sidebar
- Paste your OpenAPI YAML/JSON or click **"Load Example"**
- Click **"Save Spec"**

### 2. Generate Tests
- Go to the **"Generate Tests"** page
- Select your saved spec from the dropdown
- Click **"Generate Tests"**
- View the generated test code

### 3. Run Tests
- Go to the **"Run Tests"** page
- Select a generation to run
- Enter your target API URL (or use the default example)
- Click **"Run Tests"**
- View results: passed, failed, and failure details

---

## Available Commands

| Command | Description |
|---------|-------------|
| `python run.py setup` | Install all dependencies |
| `python run.py all` | Start all services (recommended) |
| `python run.py ui` | Start only the web UI |
| `python run.py api` | Start only the backend API |
| `python run.py example` | Start only the example target API |
| `python run.py test` | Run all tests |
| `python run.py clean` | Clean generated files |
| `python run.py help` | Show help message |

---

## Service URLs

When running `python run.py all`:

| Service | URL | Description |
|---------|-----|-------------|
| Web UI | http://localhost:8501 | Main user interface |
| Backend API | http://localhost:8000 | FastAPI backend |
| Example API | http://localhost:8001 | Sample API for testing |

---

## Troubleshooting

### "Python not found"
- Make sure Python is installed and added to your PATH
- On Windows, try `py` instead of `python`

### "Port already in use"
- Another application is using the port
- Stop other services or change the port in the command

### "Module not found"
- Run `python run.py setup` to install dependencies

### Tests failing on Windows
- This is normal for file cleanup - the tests themselves pass
- SQLite files may be locked temporarily

---

## Project Structure

```
spec-driven-development/
├── run.py              # Simple runner script (use this!)
├── app/                # FastAPI backend
├── streamlit_app/      # Web UI
├── example_api/        # Sample API for testing
├── tests/              # Test suite
├── openapi_specs/      # Example OpenAPI specs
└── requirements.txt    # Python dependencies
```

---

## For Developers

### Running Individual Services

If you prefer to run services separately:

**Terminal 1 - Backend API:**
```bash
python run.py api
```

**Terminal 2 - Example API:**
```bash
python run.py example
```

**Terminal 3 - Web UI:**
```bash
python run.py ui
```

### Running Tests

```bash
python run.py test
```

### Using Make (Mac/Linux only)

If you have `make` installed:
```bash
make install    # Install dependencies
make dev        # Run backend
make ui         # Run UI
make test       # Run tests
```

---

## Need Help?

- Check the API docs: http://localhost:8000/docs (when API is running)
- Review the example spec in `openapi_specs/example_openapi.yaml`
