"""
Integration tests for FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from app.main import app


# Sample OpenAPI spec for testing
SAMPLE_SPEC = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths:
  /health:
    get:
      operationId: health_check
      responses:
        "200":
          description: OK
  /items:
    get:
      operationId: list_items
      responses:
        "200":
          description: List of items
    post:
      operationId: create_item
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - name
              properties:
                name:
                  type: string
      responses:
        "201":
          description: Created
        "422":
          description: Validation error
  /items/{id}:
    get:
      operationId: get_item
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: Item found
        "404":
          description: Not found
"""


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts"""
    temp = tempfile.mkdtemp()
    yield Path(temp)
    # On Windows, we need to ignore errors when deleting temp files
    # as SQLite may still have the file locked
    shutil.rmtree(temp, ignore_errors=True)


@pytest.fixture(autouse=False)
def client(temp_dir, monkeypatch):
    """Create test client with isolated database"""
    # Import modules
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


class TestHealthEndpoint:
    """Tests for /health endpoint"""

    def test_health_check(self, client):
        """Health endpoint should return ok status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestSpecEndpoints:
    """Tests for /specs endpoints"""

    def test_create_spec(self, client):
        """POST /specs should create and return spec"""
        response = client.post(
            "/specs", json={"name": "Test API", "content": SAMPLE_SPEC}
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test API"
        assert data["title"] == "Test API"
        assert data["version"] == "1.0.0"
        assert data["endpoint_count"] == 4

    def test_create_spec_invalid(self, client):
        """POST /specs with invalid spec should return 400"""
        response = client.post(
            "/specs", json={"name": "Invalid", "content": "not valid yaml {{{"}
        )

        assert response.status_code == 400
        assert "Invalid OpenAPI spec" in response.json()["detail"]

    def test_list_specs(self, client):
        """GET /specs should return list of specs"""
        # Create a spec first
        client.post("/specs", json={"name": "Test", "content": SAMPLE_SPEC})

        response = client.get("/specs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

    def test_get_spec(self, client):
        """GET /specs/{id} should return spec details"""
        # Create a spec first
        create_response = client.post(
            "/specs", json={"name": "Test", "content": SAMPLE_SPEC}
        )
        spec_id = create_response.json()["id"]

        response = client.get(f"/specs/{spec_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == spec_id
        assert "endpoints" in data
        assert len(data["endpoints"]) == 4

    def test_get_spec_not_found(self, client):
        """GET /specs/{id} with invalid id should return 404"""
        response = client.get("/specs/nonexistent-id")
        assert response.status_code == 404

    def test_delete_spec(self, client):
        """DELETE /specs/{id} should delete spec"""
        # Create a spec first
        create_response = client.post(
            "/specs", json={"name": "Test", "content": SAMPLE_SPEC}
        )
        spec_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/specs/{spec_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/specs/{spec_id}")
        assert response.status_code == 404


class TestGenerationEndpoints:
    """Tests for /generate endpoints"""

    def test_generate_tests(self, client):
        """POST /generate should create test files"""
        # Create a spec first
        create_response = client.post(
            "/specs", json={"name": "Test", "content": SAMPLE_SPEC}
        )
        spec_id = create_response.json()["id"]

        # Generate tests
        response = client.post("/generate", json={"spec_id": spec_id})
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["spec_id"] == spec_id
        assert data["status"] == "completed"
        assert len(data["files"]) > 0

    def test_generate_spec_not_found(self, client):
        """POST /generate with invalid spec_id should return 404"""
        response = client.post("/generate", json={"spec_id": "nonexistent"})
        assert response.status_code == 404

    def test_get_generation(self, client):
        """GET /generations/{id} should return generation details"""
        # Create spec and generate
        create_response = client.post(
            "/specs", json={"name": "Test", "content": SAMPLE_SPEC}
        )
        spec_id = create_response.json()["id"]
        gen_response = client.post("/generate", json={"spec_id": spec_id})
        gen_id = gen_response.json()["id"]

        response = client.get(f"/generations/{gen_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == gen_id

    def test_list_generations(self, client):
        """GET /generations should return list"""
        # Create spec and generate
        create_response = client.post(
            "/specs", json={"name": "Test", "content": SAMPLE_SPEC}
        )
        spec_id = create_response.json()["id"]
        client.post("/generate", json={"spec_id": spec_id})

        response = client.get("/generations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1


class TestRunEndpoints:
    """Tests for /runs endpoints"""

    def test_list_runs_empty(self, client):
        """GET /runs should return empty list initially"""
        response = client.get("/runs")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_run_not_found(self, client):
        """GET /runs/{id} with invalid id should return 404"""
        response = client.get("/runs/nonexistent")
        assert response.status_code == 404

    # Note: Full run tests require a running target API
    # Those are covered in e2e tests
