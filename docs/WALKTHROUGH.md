# OpenAPI Test Generator - Complete Walkthrough

Hey there! This guide will walk you through using the OpenAPI Test Generator from scratch. Whether you're a developer or just someone who wants to automate API testing, this doc has got you covered.

## Table of Contents

- [What Does This Thing Do?](#what-does-this-thing-do)
- [Before You Start](#before-you-start)
- [Starting Up the Services](#starting-up-the-services)
- [Using the Web Interface](#using-the-web-interface)
  - [Page 1: Upload Spec](#page-1-upload-spec)
  - [Page 2: Generate Tests](#page-2-generate-tests)
  - [Page 3: Run Tests](#page-3-run-tests)
- [Understanding What the Tests Actually Do](#understanding-what-the-tests-actually-do)
- [The Example API Endpoints](#the-example-api-endpoints)
- [Troubleshooting](#troubleshooting)
- [CLI Usage (No UI Needed)](#cli-usage-no-ui-needed)
- [API Endpoints Reference](#api-endpoints-reference)
- [Environment Variables](#environment-variables)
- [Running Tests Directly with pytest](#running-tests-directly-with-pytest)
- [One-Liner Workflow (Advanced)](#one-liner-workflow-advanced)
- [Project Structure](#project-structure-for-the-curious)
- [Quick Reference](#quick-reference)

## What Does This Thing Do?

In simple terms: you give it an OpenAPI spec (that YAML/JSON file describing your API), and it spits out working pytest tests. Then you can run those tests against any API server to see if things work as expected.

The whole flow looks like this:

```
OpenAPI Spec (YAML/JSON)
        |
        v
   [Upload to App]
        |
        v
   [Generate Tests]  <-- Uses Mock LLM or Real LLM (OpenAI/Anthropic)
        |
        v
   [Run Tests]
        |
        v
   Results (Pass/Fail with details)
```

---

## Before You Start

### What You Need Installed

1. **Python 3.10+** - Check with `python --version`
2. **pip** - Comes with Python, but verify with `pip --version`

### Getting the Code Ready

Open your terminal and navigate to the project folder:

```bash
cd c:\Users\charan4170\ai-test-project\spec-driven-development
```

Install all the dependencies:

```bash
pip install -r requirements.txt
```

This grabs everything you need - FastAPI, Streamlit, pytest, httpx, and all the other bits.

---

## Starting Up the Services

You'll need **two terminals** open for this. Think of it like having two tabs - one runs your test API, the other runs the web interface.

### Terminal 1: Start the Example API

This is a simple API server that we'll test against. It's got a few endpoints like creating items, fetching items, etc.

```bash
cd c:\Users\charan4170\ai-test-project\spec-driven-development
python run.py example
```

You should see something like:

```
INFO:     Uvicorn running on http://127.0.0.1:8001
INFO:     Started reloader process
```

Leave this running. Don't close this terminal!

### Terminal 2: Start the Streamlit UI

Open a new terminal window (keep the first one running) and do:

```bash
cd c:\Users\charan4170\ai-test-project\spec-driven-development
python run.py ui
```

You'll see:

```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

Now open your browser and go to **http://localhost:8501**

---

## Using the Web Interface

The Streamlit UI has three main pages. You'll go through them in order: Upload → Generate → Run.

### Page 1: Upload Spec

This is where you feed the app your OpenAPI specification.

**Option A: Use the Built-in Example (Easiest)**

1. Click "Load Example Spec" button
2. You'll see the spec appear in the text area
3. The right side shows a preview of all the endpoints found
4. Give it a name (or keep the default)
5. Click "Save Spec"

**Option B: Paste Your Own Spec**

1. Copy your OpenAPI YAML or JSON content
2. Paste it into the big text area on the left
3. Check the preview on the right - make sure it parsed correctly
4. Enter a name for this spec
5. Click "Save Spec"

**Option C: Upload a File**

1. Use the file uploader at the top
2. Select your `.yaml` or `.json` file
3. Preview shows up on the right
4. Name it and save

After saving, you'll see a green success message with a Spec ID. The app remembers this spec for later.

### Page 2: Generate Tests

Click on "Generate Tests" in the sidebar to go to this page.

**Step 1: Pick Your Spec**

Use the dropdown at the top to select the spec you just uploaded. If you only have one, it's already selected.

**Step 2: Choose Your LLM Provider**

This is where it gets interesting. You have three options:

| Provider | What It Does | Needs API Key? |
|----------|--------------|----------------|
| **Mock (Deterministic)** | Generates predictable, reliable tests based on your spec structure | No |
| **OpenAI** | Uses GPT to generate more creative tests | Yes - needs `OPENAI_API_KEY` |
| **Anthropic** | Uses Claude to generate tests | Yes - needs `ANTHROPIC_API_KEY` |

**My recommendation:** Start with **Mock**. It's free, fast, and generates tests that actually work. The real LLMs can sometimes make wrong assumptions about your API.

If you want to use OpenAI or Anthropic:
1. Select the provider from the dropdown
2. Paste your API key in the text field that appears
3. The key is only used for this session - it's not stored anywhere

**Step 3: Generate!**

Click the big "Generate Tests" button. You'll see a progress spinner, and then:

- A success message with the Generation ID
- A list of generated test files
- Expandable sections showing the actual test code

Take a look at the generated code if you're curious. Each test file contains pytest functions that make HTTP requests to your API and check the responses.

### Page 3: Run Tests

Click "Run Tests" in the sidebar.

**Step 1: Select Generation**

Pick the test generation you want to run from the dropdown. It shows the spec name and when it was generated.

**Step 2: Set Target URL**

This is the URL of the API you're testing against.

- If you started the example API earlier, keep the default: `http://localhost:8001`
- If you're testing a different API, enter its URL here

**Step 3: Run!**

Click "Run Tests" and wait. The tests will execute, and you'll see:

**Results Summary**

Five boxes showing:
- **Passed** (green) - Tests that worked
- **Failed** (red) - Tests that didn't work
- **Skipped** - Tests that were skipped
- **Errors** - Tests that crashed
- **Duration** - How long it took

**If Everything Passed:**

You'll see a green "All tests passed!" message. Nice work!

**If Something Failed:**

Each failure shows up in an expandable section with:
- The test name
- What went wrong (error message)
- The full traceback (useful for debugging)

**Test Output**

Expand "Test Output" to see the raw stdout/stderr from pytest. This is helpful when things go sideways.

**Download Options**

- **JUnit XML** - Standard test report format, works with CI tools like Jenkins
- **Results JSON** - All the details in JSON format

---

## Understanding What the Tests Actually Do

The generated tests cover three scenarios for each endpoint:

### 1. Happy Path Tests (`*_success`)

These test that your API works when given valid input:

```python
def test_create_item_success(client):
    """Test successful POST /items"""
    response = client.post("/items", json={"name": "Widget", "price": 9.99})
    assert response.status_code == 201
    assert response.json() is not None
```

### 2. Not Found Tests (`*_not_found`)

These test that your API returns 404 for missing resources:

```python
def test_get_item_not_found(client):
    """Test GET /items/{id} with non-existent resource"""
    response = client.get("/items/nonexistent-id-12345")
    assert response.status_code == 404
```

### 3. Validation Error Tests (`*_validation_error`)

These test that your API rejects bad input:

```python
def test_create_item_validation_error(client):
    """Test POST /items with missing required fields"""
    response = client.post("/items", json={})
    assert response.status_code == 422
```

---

## The Example API Endpoints

If you're using the built-in example API, here's what it supports:

| Method | Path | What It Does |
|--------|------|--------------|
| GET | `/health` | Returns `{"status": "ok"}` |
| POST | `/items` | Creates a new item with `name` and `price` |
| GET | `/items/{id}` | Gets an item by ID |
| DELETE | `/items/{id}` | Deletes an item by ID |

The API stores items in memory, so they disappear when you restart it.

---

## Troubleshooting

### "collected 0 items" - No Tests Found

This usually means the test files weren't generated properly. Try:
1. Go back to "Generate Tests" page
2. Generate tests again
3. Make sure you see the test files listed

### Tests Fail with Connection Errors

The target API isn't running or the URL is wrong:
1. Check that Terminal 1 (example API) is still running
2. Verify the URL is `http://localhost:8001`
3. Try opening that URL in your browser - you should see `{"detail":"Not Found"}`

### OpenAI/Anthropic Tests Fail

Real LLMs sometimes generate tests with wrong assumptions. Common issues:
- Expecting `error` field instead of `detail`
- Assuming items already exist
- Wrong status codes

**Solution:** Use Mock mode instead. It generates tests that match FastAPI conventions.

### "openai package is required" Error

You selected OpenAI but don't have the package:
```bash
pip install openai
```

Same for Anthropic:
```bash
pip install anthropic
```

### Database Issues

If things get weird, you can reset the database:
```bash
del data\app.db
```

Then restart the UI.

---

## CLI Usage (No UI Needed)

Prefer the command line? Here's how to do everything without touching the browser.

### Step 1: Start the Backend API

```bash
cd c:\Users\charan4170\ai-test-project\spec-driven-development
python run.py api
```

This starts the FastAPI backend on `http://localhost:8000`. Keep this terminal open.

### Step 2: Start the Example API (for testing)

Open another terminal:

```bash
cd c:\Users\charan4170\ai-test-project\spec-driven-development
python run.py example
```

Now you have the target API on `http://localhost:8001`.

### Step 3: Upload a Spec

Using `curl` (or any HTTP client):

```bash
# Upload the example spec
curl -X POST http://localhost:8000/specs \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"My API\", \"content\": \"$(cat openapi_specs/example_openapi.yaml)\"}"
```

Or with PowerShell:

```powershell
$spec = Get-Content -Raw openapi_specs\example_openapi.yaml
$body = @{ name = "My API"; content = $spec } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/specs -Method POST -Body $body -ContentType "application/json"
```

Response:
```json
{
  "id": "abc123-def456-...",
  "name": "My API",
  "title": "Example API",
  "version": "1.0.0",
  "endpoint_count": 4,
  "created_at": "2024-01-15T10:30:00"
}
```

Save that `id` - you'll need it.

### Step 4: Generate Tests

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d "{\"spec_id\": \"YOUR_SPEC_ID_HERE\"}"
```

PowerShell:
```powershell
$body = @{ spec_id = "YOUR_SPEC_ID_HERE" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/generate -Method POST -Body $body -ContentType "application/json"
```

Response:
```json
{
  "id": "gen-789...",
  "spec_id": "abc123...",
  "status": "completed",
  "files": [
    "C:\\...\\generated_tests\\abc123...\\conftest.py",
    "C:\\...\\generated_tests\\abc123...\\test_items.py"
  ],
  "created_at": "2024-01-15T10:31:00"
}
```

### Step 5: Run Tests

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d "{\"generation_id\": \"YOUR_GENERATION_ID\", \"target_url\": \"http://localhost:8001\"}"
```

PowerShell:
```powershell
$body = @{ generation_id = "YOUR_GENERATION_ID"; target_url = "http://localhost:8001" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/runs -Method POST -Body $body -ContentType "application/json"
```

Response:
```json
{
  "id": "run-999...",
  "generation_id": "gen-789...",
  "status": "completed",
  "passed": 6,
  "failed": 0,
  "skipped": 0,
  "errors": 0,
  "total": 6,
  "duration": 1.23,
  "created_at": "2024-01-15T10:32:00"
}
```

### Step 6: Get Detailed Results

```bash
curl http://localhost:8000/runs/YOUR_RUN_ID
```

This returns the full details including any failure messages and tracebacks.

### Step 7: Get JUnit XML (for CI)

```bash
curl http://localhost:8000/runs/YOUR_RUN_ID/junit > results.xml
```

---

## API Endpoints Reference

All endpoints are available at `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check - returns `{"status": "ok"}` |
| POST | `/specs` | Upload a new OpenAPI spec |
| GET | `/specs` | List all uploaded specs |
| GET | `/specs/{id}` | Get spec details with endpoints |
| DELETE | `/specs/{id}` | Delete a spec |
| POST | `/generate` | Generate tests for a spec |
| GET | `/generations` | List all generations |
| GET | `/generations/{id}` | Get generation details |
| POST | `/runs` | Run tests for a generation |
| GET | `/runs` | List all runs |
| GET | `/runs/{id}` | Get run details with failures |
| GET | `/runs/{id}/junit` | Get JUnit XML report |

---

## Environment Variables

You can configure the app using these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `mock` | Which LLM to use: `mock`, `openai`, or `anthropic` |
| `OPENAI_API_KEY` | - | Your OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Your Anthropic API key |
| `DEFAULT_TARGET_URL` | `http://localhost:8001` | Default URL for running tests |
| `DATABASE_PATH` | `data/app.db` | Where to store the SQLite database |
| `GENERATED_TESTS_DIR` | `generated_tests` | Where to write generated test files |
| `TEST_TIMEOUT` | `300` | Max seconds for test execution |

Example:
```bash
# Windows
set LLM_PROVIDER=openai
set OPENAI_API_KEY=sk-your-key-here
python run.py api

# Linux/Mac
export LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-your-key-here
python run.py api
```

---

## Running Tests Directly with pytest

Don't want to use the API at all? You can run generated tests directly:

```bash
cd c:\Users\charan4170\ai-test-project\spec-driven-development

# Run the project's own tests (to verify everything works)
python -m pytest tests/ -v

# Run generated tests against your API
set TARGET_BASE_URL=http://localhost:8001
python -m pytest generated_tests\<spec-id>\ -v

# Run with JUnit output for CI
python -m pytest generated_tests\<spec-id>\ --junitxml=results.xml -v
```

---

## One-Liner Workflow (Advanced)

For scripting or CI pipelines, here's a complete workflow in PowerShell:

```powershell
# Variables
$API_URL = "http://localhost:8000"
$TARGET_URL = "http://localhost:8001"
$SPEC_FILE = "openapi_specs\example_openapi.yaml"

# 1. Upload spec
$spec = Get-Content -Raw $SPEC_FILE
$uploadBody = @{ name = "CI Test"; content = $spec } | ConvertTo-Json -Depth 10
$specResult = Invoke-RestMethod -Uri "$API_URL/specs" -Method POST -Body $uploadBody -ContentType "application/json"
$specId = $specResult.id
Write-Host "Uploaded spec: $specId"

# 2. Generate tests
$genBody = @{ spec_id = $specId } | ConvertTo-Json
$genResult = Invoke-RestMethod -Uri "$API_URL/generate" -Method POST -Body $genBody -ContentType "application/json"
$genId = $genResult.id
Write-Host "Generated tests: $genId"

# 3. Run tests
$runBody = @{ generation_id = $genId; target_url = $TARGET_URL } | ConvertTo-Json
$runResult = Invoke-RestMethod -Uri "$API_URL/runs" -Method POST -Body $runBody -ContentType "application/json"

# 4. Check results
if ($runResult.failed -eq 0 -and $runResult.errors -eq 0) {
    Write-Host "All tests passed! ($($runResult.passed) passed)"
    exit 0
} else {
    Write-Host "Tests failed: $($runResult.failed) failed, $($runResult.errors) errors"
    exit 1
}
```

And for bash:

```bash
#!/bin/bash
API_URL="http://localhost:8000"
TARGET_URL="http://localhost:8001"
SPEC_FILE="openapi_specs/example_openapi.yaml"

# 1. Upload spec
SPEC_CONTENT=$(cat "$SPEC_FILE" | jq -Rs .)
SPEC_RESULT=$(curl -s -X POST "$API_URL/specs" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"CI Test\", \"content\": $SPEC_CONTENT}")
SPEC_ID=$(echo $SPEC_RESULT | jq -r '.id')
echo "Uploaded spec: $SPEC_ID"

# 2. Generate tests
GEN_RESULT=$(curl -s -X POST "$API_URL/generate" \
  -H "Content-Type: application/json" \
  -d "{\"spec_id\": \"$SPEC_ID\"}")
GEN_ID=$(echo $GEN_RESULT | jq -r '.id')
echo "Generated tests: $GEN_ID"

# 3. Run tests
RUN_RESULT=$(curl -s -X POST "$API_URL/runs" \
  -H "Content-Type: application/json" \
  -d "{\"generation_id\": \"$GEN_ID\", \"target_url\": \"$TARGET_URL\"}")

# 4. Check results
FAILED=$(echo $RUN_RESULT | jq -r '.failed')
ERRORS=$(echo $RUN_RESULT | jq -r '.errors')
PASSED=$(echo $RUN_RESULT | jq -r '.passed')

if [ "$FAILED" -eq 0 ] && [ "$ERRORS" -eq 0 ]; then
    echo "All tests passed! ($PASSED passed)"
    exit 0
else
    echo "Tests failed: $FAILED failed, $ERRORS errors"
    exit 1
fi
```

---

## Project Structure (For the Curious)

```
spec-driven-development/
├── app/                      # Main application code
│   ├── generator/            # Test generation logic
│   │   ├── llm_client.py     # Mock, OpenAI, Anthropic clients
│   │   └── test_generator.py # Generates pytest files
│   ├── runner/               # Test execution
│   │   ├── pytest_runner.py  # Runs pytest programmatically
│   │   └── junit_parser.py   # Parses test results
│   ├── storage/              # Database
│   │   └── db.py             # SQLite storage
│   ├── openapi_parser.py     # Parses OpenAPI specs
│   ├── routes.py             # FastAPI endpoints
│   └── config.py             # Configuration
├── streamlit_app/            # Web UI
│   ├── app.py                # Main entry
│   └── pages/                # UI pages
├── example_api/              # Sample API for testing
├── generated_tests/          # Where tests get written
├── data/                     # SQLite database
├── tests/                    # Project's own tests
└── run.py                    # Helper script to start things
```

---

## Quick Reference

| Command | What It Does |
|---------|--------------|
| `python run.py example` | Start the example API on port 8001 |
| `python run.py ui` | Start the Streamlit UI on port 8501 |
| `python run.py api` | Start the FastAPI backend on port 8000 |
| `python run.py test` | Run the project's own test suite |

---

## Need Help?

If you run into issues:

1. Check the terminal windows for error messages
2. Look at the "Test Output" section in the Run page
3. Try regenerating tests with Mock mode
4. Reset the database if things get stuck

Happy testing!
