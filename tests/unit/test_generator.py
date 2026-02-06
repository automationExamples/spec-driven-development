"""
Unit tests for the test generator.
"""

import ast
import pytest

from app.openapi_parser import (
    NormalizedSpec,
    Endpoint,
    Parameter,
    RequestBody,
    Response,
)
from app.generator.llm_client import MockLLMClient, GeneratedTestCase
from app.generator.test_generator import PytestGenerator


class TestMockLLMClient:
    """Tests for MockLLMClient"""

    @pytest.fixture
    def client(self):
        return MockLLMClient()

    @pytest.fixture
    def sample_spec(self):
        return NormalizedSpec(
            title="Test API", version="1.0.0", endpoints=[], schemas={}
        )

    def test_generates_deterministic_output(self, client, sample_spec):
        """MockLLMClient should produce identical output for identical input"""
        endpoint = Endpoint(
            path="/items",
            method="GET",
            operation_id="list_items",
            responses=[Response(status_code=200, description="OK")],
        )

        result1 = client.generate_test_plan(endpoint, sample_spec)
        result2 = client.generate_test_plan(endpoint, sample_spec)

        assert len(result1.test_cases) == len(result2.test_cases)
        assert result1.test_cases[0].name == result2.test_cases[0].name
        assert (
            result1.test_cases[0].expected_status
            == result2.test_cases[0].expected_status
        )

    def test_generates_happy_path_for_get(self, client, sample_spec):
        """Should generate happy path test for GET endpoint"""
        endpoint = Endpoint(
            path="/items",
            method="GET",
            operation_id="list_items",
            responses=[Response(status_code=200, description="OK")],
        )

        result = client.generate_test_plan(endpoint, sample_spec)

        assert len(result.test_cases) >= 1
        happy_path = result.test_cases[0]
        assert "success" in happy_path.name
        assert happy_path.expected_status == 200

    def test_generates_happy_path_for_post(self, client, sample_spec):
        """Should generate happy path test for POST endpoint"""
        endpoint = Endpoint(
            path="/items",
            method="POST",
            operation_id="create_item",
            request_body=RequestBody(
                schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                }
            ),
            responses=[Response(status_code=201, description="Created")],
        )

        result = client.generate_test_plan(endpoint, sample_spec)

        happy_path = result.test_cases[0]
        assert happy_path.expected_status == 201
        assert happy_path.request_body is not None

    def test_generates_404_test_for_path_params(self, client, sample_spec):
        """Should generate 404 test for endpoints with path parameters"""
        endpoint = Endpoint(
            path="/items/{id}",
            method="GET",
            operation_id="get_item",
            parameters=[Parameter(name="id", location="path", required=True)],
            responses=[
                Response(status_code=200, description="OK"),
                Response(status_code=404, description="Not found"),
            ],
        )

        result = client.generate_test_plan(endpoint, sample_spec)

        not_found_tests = [t for t in result.test_cases if t.expected_status == 404]
        assert len(not_found_tests) == 1
        assert "not_found" in not_found_tests[0].name

    def test_generates_validation_test_for_post(self, client, sample_spec):
        """Should generate validation error test for POST endpoints"""
        endpoint = Endpoint(
            path="/items",
            method="POST",
            operation_id="create_item",
            request_body=RequestBody(
                required=True,
                schema={
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            ),
            responses=[
                Response(status_code=201, description="Created"),
                Response(status_code=422, description="Validation Error"),
            ],
        )

        result = client.generate_test_plan(endpoint, sample_spec)

        validation_tests = [t for t in result.test_cases if t.expected_status == 422]
        assert len(validation_tests) == 1
        assert validation_tests[0].request_body == {}

    def test_generates_tests_for_all_endpoints(self, client, sample_spec):
        """Should generate test plans for all endpoints in spec"""
        sample_spec.endpoints = [
            Endpoint(
                path="/health", method="GET", responses=[Response(status_code=200)]
            ),
            Endpoint(
                path="/items", method="GET", responses=[Response(status_code=200)]
            ),
            Endpoint(
                path="/items", method="POST", responses=[Response(status_code=201)]
            ),
        ]

        results = client.generate_tests_for_spec(sample_spec)

        assert len(results) == 3


class TestPytestGenerator:
    """Tests for PytestGenerator"""

    @pytest.fixture
    def generator(self, tmp_path):
        return PytestGenerator(output_dir=tmp_path)

    @pytest.fixture
    def sample_spec(self):
        return NormalizedSpec(
            title="Test API",
            version="1.0.0",
            base_url="http://localhost:8001",
            endpoints=[
                Endpoint(
                    path="/health",
                    method="GET",
                    operation_id="health_check",
                    responses=[Response(status_code=200, description="OK")],
                ),
                Endpoint(
                    path="/items",
                    method="GET",
                    operation_id="list_items",
                    responses=[Response(status_code=200, description="OK")],
                ),
                Endpoint(
                    path="/items",
                    method="POST",
                    operation_id="create_item",
                    request_body=RequestBody(
                        schema={
                            "type": "object",
                            "properties": {"name": {"type": "string"}},
                        }
                    ),
                    responses=[
                        Response(status_code=201, description="Created"),
                        Response(status_code=422, description="Validation Error"),
                    ],
                ),
                Endpoint(
                    path="/items/{id}",
                    method="GET",
                    operation_id="get_item",
                    parameters=[Parameter(name="id", location="path", required=True)],
                    responses=[
                        Response(status_code=200, description="OK"),
                        Response(status_code=404, description="Not Found"),
                    ],
                ),
            ],
            schemas={},
        )

    def test_generates_files(self, generator, sample_spec, tmp_path):
        """Should generate test files"""
        files = generator.generate(sample_spec, "test-spec-1")

        assert len(files) > 0
        assert all(f.exists() for f in files)

    def test_generates_conftest(self, generator, sample_spec, tmp_path):
        """Should generate conftest.py with fixtures"""
        generator.generate(sample_spec, "test-spec-1")

        conftest = tmp_path / "test-spec-1" / "conftest.py"
        assert conftest.exists()
        content = conftest.read_text()
        assert "def base_url" in content
        assert "def client" in content
        assert "http://localhost:8001" in content

    def test_generated_code_is_valid_python(self, generator, sample_spec, tmp_path):
        """Generated test files should be syntactically valid Python"""
        files = generator.generate(sample_spec, "test-spec-1")

        for file_path in files:
            content = file_path.read_text()
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Generated file {file_path} has syntax error: {e}")

    def test_test_names_are_stable(self, generator, sample_spec, tmp_path):
        """Test names should be stable across generations"""
        files1 = generator.generate(sample_spec, "test-spec-1")
        files2 = generator.generate(sample_spec, "test-spec-2")

        # Compare content (excluding conftest which has the same content)
        for f1, f2 in zip(sorted(files1), sorted(files2)):
            if f1.name == f2.name and f1.name != "conftest.py":
                content1 = f1.read_text()
                content2 = f2.read_text()
                # Test names should match
                assert content1 == content2

    def test_groups_tests_by_resource(self, generator, sample_spec, tmp_path):
        """Should group tests by resource (first path segment)"""
        files = generator.generate(sample_spec, "test-spec-1")

        test_files = [f for f in files if f.name.startswith("test_")]
        # Should have test_health.py and test_items.py
        file_names = {f.name for f in test_files}
        assert "test_health.py" in file_names
        assert "test_items.py" in file_names

    def test_generates_httpx_requests(self, generator, sample_spec, tmp_path):
        """Generated tests should use httpx client"""
        files = generator.generate(sample_spec, "test-spec-1")

        for file_path in files:
            if file_path.name.startswith("test_"):
                content = file_path.read_text()
                # Should use client fixture methods
                assert "client." in content


class TestGeneratedTestCase:
    """Tests for GeneratedTestCase dataclass"""

    def test_defaults(self):
        """GeneratedTestCase should have sensible defaults"""
        tc = GeneratedTestCase(
            name="test_example",
            description="Test",
            method="GET",
            path="/test",
            expected_status=200,
        )
        assert tc.assertions == []
        assert tc.request_body is None
        assert tc.path_params is None
