"""
End-to-end tests for the complete workflow.

These tests run the full pipeline:
1. Start example API
2. Upload spec
3. Generate tests
4. Run tests against example API
5. Verify results
"""

import pytest
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient


# Read the example OpenAPI spec
EXAMPLE_SPEC_PATH = (
    Path(__file__).parent.parent.parent / "openapi_specs" / "example_openapi.yaml"
)


@pytest.fixture(scope="module")
def example_api():
    """Start the example API server for testing"""
    # Start the example API
    proc = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "example_api.main:app",
            "--port",
            "9999",
            "--host",
            "127.0.0.1",
        ],
        cwd=str(Path(__file__).parent.parent.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for it to start
    time.sleep(2)

    # Check if it's running
    import httpx

    for _ in range(10):
        try:
            response = httpx.get("http://127.0.0.1:9999/health", timeout=1)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)

    yield "http://127.0.0.1:9999"

    # Cleanup
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    # On Windows, we need to ignore errors when deleting temp files
    # as SQLite may still have the file locked
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture
def client(temp_dir, monkeypatch):
    """Create test client with isolated database"""
    from app.main import app
    from app.storage import db as db_module
    from app import config as config_module

    # Reset the database singleton FIRST
    db_module._db = None

    # Set environment variables for test
    monkeypatch.setenv("DATABASE_PATH", str(temp_dir / "test.db"))
    monkeypatch.setenv("GENERATED_TESTS_DIR", str(temp_dir / "generated_tests"))

    # Update config to use temp paths (must be done after singleton reset)
    config_module.config.DATABASE_PATH = temp_dir / "test.db"
    config_module.config.GENERATED_TESTS_DIR = temp_dir / "generated_tests"

    # Force create new database with correct path
    db_module.get_database(temp_dir / "test.db")

    yield TestClient(app)

    # Cleanup: reset database singleton to release file handle
    db_module._db = None


class TestFullWorkflow:
    """Full end-to-end workflow tests"""

    @pytest.mark.skipif(not EXAMPLE_SPEC_PATH.exists(), reason="Example spec not found")
    def test_complete_workflow(self, client, example_api, temp_dir):
        """Test the complete workflow: upload -> generate -> run"""
        # 1. Upload the example spec
        spec_content = EXAMPLE_SPEC_PATH.read_text()
        response = client.post(
            "/specs", json={"name": "Example API", "content": spec_content}
        )
        assert response.status_code == 201
        spec_id = response.json()["id"]

        # 2. Generate tests
        response = client.post("/generate", json={"spec_id": spec_id})
        assert response.status_code == 201
        generation = response.json()
        assert generation["status"] == "completed"
        assert len(generation["files"]) > 0
        generation_id = generation["id"]

        # 3. Run tests against example API
        response = client.post(
            "/runs", json={"generation_id": generation_id, "target_url": example_api}
        )
        assert response.status_code == 201
        run = response.json()
        assert run["status"] in ["completed", "failed"]
        assert run["total"] > 0
        run_id = run["id"]

        # 4. Get detailed results
        response = client.get(f"/runs/{run_id}")
        assert response.status_code == 200
        details = response.json()
        assert "failures" in details

        # 5. Verify JUnit XML is available
        response = client.get(f"/runs/{run_id}/junit")
        assert response.status_code == 200
        assert "<?xml" in response.text

    @pytest.mark.skipif(not EXAMPLE_SPEC_PATH.exists(), reason="Example spec not found")
    def test_generated_tests_pass(self, client, example_api, temp_dir):
        """Verify that generated tests actually pass against the example API"""
        # Upload spec
        spec_content = EXAMPLE_SPEC_PATH.read_text()
        response = client.post(
            "/specs", json={"name": "Example API", "content": spec_content}
        )
        spec_id = response.json()["id"]

        # Generate tests
        response = client.post("/generate", json={"spec_id": spec_id})
        generation_id = response.json()["id"]

        # Run tests
        response = client.post(
            "/runs", json={"generation_id": generation_id, "target_url": example_api}
        )
        run = response.json()

        # Check that at least some tests passed
        assert run["passed"] > 0, "Expected at least some tests to pass"

        # The health check test should definitely pass
        if run["failed"] > 0:
            # Get failure details
            response = client.get(f"/runs/{run['id']}")
            details = response.json()
            print("Failures:", details.get("failures", []))

    def test_workflow_with_inline_spec(self, client, temp_dir):
        """Test workflow with an inline minimal spec (no external API needed)"""
        # Create a minimal spec
        spec = """
openapi: "3.0.0"
info:
  title: Minimal API
  version: "1.0.0"
paths:
  /test:
    get:
      operationId: test_endpoint
      responses:
        "200":
          description: OK
"""
        # Upload spec
        response = client.post("/specs", json={"name": "Minimal", "content": spec})
        assert response.status_code == 201
        spec_id = response.json()["id"]

        # Generate tests
        response = client.post("/generate", json={"spec_id": spec_id})
        assert response.status_code == 201
        generation = response.json()

        # Verify files were generated
        assert len(generation["files"]) > 0

        # Verify test file contains expected content
        for file_path in generation["files"]:
            path = Path(file_path)
            if path.name.startswith("test_"):
                content = path.read_text()
                assert "def test_" in content
                assert "client" in content


class TestGeneratedTestsContent:
    """Tests to verify the content of generated tests"""

    def test_generated_tests_are_valid_python(self, client, temp_dir):
        """Generated test files should be syntactically valid Python"""
        import ast

        spec = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths:
  /items:
    get:
      operationId: list_items
      responses:
        "200":
          description: OK
    post:
      operationId: create_item
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
      responses:
        "201":
          description: Created
"""
        # Upload and generate
        response = client.post("/specs", json={"name": "Test", "content": spec})
        spec_id = response.json()["id"]

        response = client.post("/generate", json={"spec_id": spec_id})
        generation = response.json()

        # Verify all files are valid Python
        for file_path in generation["files"]:
            path = Path(file_path)
            content = path.read_text()
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Generated file {path.name} is not valid Python: {e}")

    def test_conftest_has_fixtures(self, client, temp_dir):
        """conftest.py should have required fixtures"""
        spec = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths:
  /test:
    get:
      responses:
        "200":
          description: OK
"""
        # Upload and generate
        response = client.post("/specs", json={"name": "Test", "content": spec})
        spec_id = response.json()["id"]

        response = client.post("/generate", json={"spec_id": spec_id})
        generation = response.json()

        # Find conftest.py
        conftest_path = None
        for file_path in generation["files"]:
            if Path(file_path).name == "conftest.py":
                conftest_path = Path(file_path)
                break

        assert conftest_path is not None, "conftest.py should be generated"
        content = conftest_path.read_text()

        assert "def base_url" in content, "Should have base_url fixture"
        assert "def client" in content, "Should have client fixture"
        assert "@pytest.fixture" in content, "Should use pytest fixtures"
