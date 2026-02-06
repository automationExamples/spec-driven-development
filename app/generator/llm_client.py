"""
LLM Client - Abstract interface and implementations for test generation.

Provides:
- MockLLMClient: Deterministic local/CI usage (no API calls)
- OpenAIClient: OpenAI GPT integration
- AnthropicClient: Anthropic Claude integration
"""

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from app.openapi_parser import Endpoint, NormalizedSpec


@dataclass
class GeneratedTestCase:
    """Represents a single test case to generate"""

    name: str
    description: str
    method: str
    path: str
    expected_status: int
    request_body: Optional[dict] = None
    path_params: Optional[dict] = None
    query_params: Optional[dict] = None
    assertions: list[str] = None

    def __post_init__(self):
        if self.assertions is None:
            self.assertions = []


# Backwards-compatible alias (avoid name starting with 'Test' for pytest)
TestCase = GeneratedTestCase


@dataclass
class GeneratedTestPlan:
    """Collection of test cases for an endpoint or spec"""

    endpoint_path: str
    endpoint_method: str
    test_cases: list[GeneratedTestCase]


# Backwards-compatible alias (avoid name starting with 'Test' for pytest)
TestPlan = GeneratedTestPlan


class LLMClient(ABC):
    """Abstract base class for LLM clients"""

    @abstractmethod
    def generate_test_plan(self, endpoint: Endpoint, spec: NormalizedSpec) -> GeneratedTestPlan:
        """Generate a test plan for a single endpoint."""
        pass

    @abstractmethod
    def generate_tests_for_spec(self, spec: NormalizedSpec) -> list[GeneratedTestPlan]:
        """Generate test plans for all endpoints in a spec."""
        pass


# =============================================================================
# Mock LLM Client (Default - No API calls)
# =============================================================================


class MockLLMClient(LLMClient):
    """
    Deterministic mock LLM client for local development and CI.

    Generates test cases based purely on endpoint structure,
    without any randomness or external API calls.
    """

    def generate_test_plan(self, endpoint: Endpoint, spec: NormalizedSpec) -> GeneratedTestPlan:
        """Generate deterministic test plan for an endpoint"""
        test_cases = []

        # Generate happy path test
        happy_path = self._generate_happy_path(endpoint, spec)
        if happy_path:
            test_cases.append(happy_path)

        # Generate 404 test for endpoints with path parameters
        not_found = self._generate_not_found_test(endpoint)
        if not_found:
            test_cases.append(not_found)

        # Generate validation error test for POST/PUT with request body
        validation_error = self._generate_validation_error_test(endpoint)
        if validation_error:
            test_cases.append(validation_error)

        return GeneratedTestPlan(
            endpoint_path=endpoint.path,
            endpoint_method=endpoint.method,
            test_cases=test_cases,
        )

    def generate_tests_for_spec(self, spec: NormalizedSpec) -> list[GeneratedTestPlan]:
        """Generate test plans for all endpoints"""
        return [self.generate_test_plan(ep, spec) for ep in spec.endpoints]

    def _generate_happy_path(
        self, endpoint: Endpoint, spec: NormalizedSpec
    ) -> Optional[GeneratedTestCase]:
        """Generate a happy path test case"""
        expected_status = 200
        for response in endpoint.responses:
            if response.status_code in [200, 201, 204]:
                expected_status = response.status_code
                break

        path_params = {}
        for param in endpoint.parameters:
            if param.location == "path":
                if param.example:
                    path_params[param.name] = param.example
                else:
                    path_params[param.name] = self._generate_example_value(
                        param.schema_type
                    )

        request_body = None
        if endpoint.request_body:
            request_body = self._generate_example_body(
                endpoint.request_body.schema, spec.schemas
            )

        operation_id = (
            endpoint.operation_id
            or f"{endpoint.method.lower()}_{endpoint.path.replace('/', '_').strip('_')}"
        )
        test_name = f"test_{operation_id}_success"

        assertions = [f"assert response.status_code == {expected_status}"]
        if expected_status != 204:
            assertions.append("assert response.json() is not None")

        return GeneratedTestCase(
            name=test_name,
            description=f"Test successful {endpoint.method} {endpoint.path}",
            method=endpoint.method,
            path=endpoint.path,
            expected_status=expected_status,
            request_body=request_body,
            path_params=path_params if path_params else None,
            assertions=assertions,
        )

    def _generate_not_found_test(self, endpoint: Endpoint) -> Optional[GeneratedTestCase]:
        """Generate 404 test for endpoints with path parameters"""
        if endpoint.method not in ["GET", "PUT", "DELETE"]:
            return None

        path_params = [p for p in endpoint.parameters if p.location == "path"]
        if not path_params:
            return None

        has_404 = any(r.status_code == 404 for r in endpoint.responses)
        if not has_404:
            return None

        operation_id = (
            endpoint.operation_id
            or f"{endpoint.method.lower()}_{endpoint.path.replace('/', '_').strip('_')}"
        )
        test_name = f"test_{operation_id}_not_found"

        fake_params = {p.name: "nonexistent-id-12345" for p in path_params}

        return GeneratedTestCase(
            name=test_name,
            description=f"Test {endpoint.method} {endpoint.path} with non-existent resource",
            method=endpoint.method,
            path=endpoint.path,
            expected_status=404,
            path_params=fake_params,
            assertions=["assert response.status_code == 404"],
        )

    def _generate_validation_error_test(self, endpoint: Endpoint) -> Optional[GeneratedTestCase]:
        """Generate validation error test for POST/PUT with required body"""
        if endpoint.method not in ["POST", "PUT", "PATCH"]:
            return None

        if not endpoint.request_body:
            return None

        has_422 = any(r.status_code == 422 for r in endpoint.responses)
        if not has_422:
            return None

        operation_id = (
            endpoint.operation_id
            or f"{endpoint.method.lower()}_{endpoint.path.replace('/', '_').strip('_')}"
        )
        test_name = f"test_{operation_id}_validation_error"

        return GeneratedTestCase(
            name=test_name,
            description=f"Test {endpoint.method} {endpoint.path} with invalid/missing required fields",
            method=endpoint.method,
            path=endpoint.path,
            expected_status=422,
            request_body={},
            assertions=["assert response.status_code == 422"],
        )

    def _generate_example_value(self, schema_type: str) -> str:
        """Generate an example value for a schema type"""
        type_examples = {
            "string": "test-string",
            "integer": 1,
            "number": 1.0,
            "boolean": True,
            "uuid": "123e4567-e89b-12d3-a456-426614174000",
        }
        return type_examples.get(schema_type, "test-value")

    def _generate_example_body(self, schema: dict, all_schemas: dict) -> dict:
        """Generate an example request body from schema"""
        if not schema:
            return {}

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        body = {}
        for prop_name, prop_schema in properties.items():
            if prop_name in required or not required:
                body[prop_name] = self._schema_to_value(prop_schema, all_schemas)

        return body

    def _schema_to_value(self, schema: dict, all_schemas: dict):
        """Convert a schema to an example value"""
        if not schema:
            return None

        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            if ref_name in all_schemas:
                return self._generate_example_body(all_schemas[ref_name], all_schemas)
            return {}

        if "example" in schema:
            return schema["example"]

        schema_type = schema.get("type", "string")

        if schema_type == "object":
            return self._generate_example_body(schema, all_schemas)
        elif schema_type == "array":
            items = schema.get("items", {})
            return [self._schema_to_value(items, all_schemas)]
        elif schema_type == "string":
            if schema.get("format") == "uuid":
                return "123e4567-e89b-12d3-a456-426614174000"
            return "test-string"
        elif schema_type == "integer":
            return 1
        elif schema_type == "number":
            return 1.0
        elif schema_type == "boolean":
            return True

        return None


# =============================================================================
# Base Real LLM Client
# =============================================================================


class BaseLLMClient(LLMClient):
    """Base class for real LLM clients with shared functionality"""

    def _build_prompt(self, endpoint: Endpoint, spec: NormalizedSpec) -> str:
        """Build the prompt for test generation"""
        # Format endpoint info
        params_str = ""
        if endpoint.parameters:
            params_list = [
                f"  - {p.name} ({p.location}): {p.schema_type}, required={p.required}"
                for p in endpoint.parameters
            ]
            params_str = "\n".join(params_list)

        request_body_str = ""
        if endpoint.request_body and endpoint.request_body.schema:
            request_body_str = json.dumps(endpoint.request_body.schema, indent=2)

        responses_str = "\n".join(
            [f"  - {r.status_code}: {r.description}" for r in endpoint.responses]
        )

        prompt = f"""Generate pytest test cases for this FastAPI endpoint.

API: {spec.title} v{spec.version}
Endpoint: {endpoint.method} {endpoint.path}
Operation ID: {endpoint.operation_id or 'N/A'}
Summary: {endpoint.summary or 'N/A'}

Parameters:
{params_str or '  None'}

Request Body Schema:
{request_body_str or '  None'}

Responses:
{responses_str}

IMPORTANT RULES:
1. This is a FastAPI application. Error responses use "detail" field, NOT "error" field.
   Example: {{"detail": "Item not found"}}
2. Test names MUST follow this pattern:
   - Happy path: test_{{operation_id}}_success
   - Not found: test_{{operation_id}}_not_found
   - Validation error: test_{{operation_id}}_validation_error
3. For GET/DELETE endpoints with path parameters (like /items/{{id}}):
   - The "success" test should have path_params with a placeholder value like "test-id"
   - Our test runner will automatically create a resource first and use its real ID
4. Health endpoint (/health) returns {{"status": "ok"}}
5. POST endpoints return 201 for successful creation, not 200
6. Use ONLY these assertions - do not check for fields that aren't in the schema:
   - assert response.status_code == <expected_status>
   - assert response.json() is not None (for non-204 responses)
   - assert "id" in response.json() (only for POST create responses)

Generate test cases as JSON array with this structure:
[
  {{
    "name": "test_{{operation_id}}_success",
    "description": "What this test verifies",
    "expected_status": 200,
    "path_params": {{"id": "test-id"}} or null,
    "query_params": {{"param": "value"}} or null,
    "request_body": {{"field": "value"}} or null,
    "assertions": ["assert response.status_code == 200"]
  }}
]

Generate tests for:
1. Happy path (successful request) - name must contain "success"
2. Not found (404) for GET/PUT/DELETE with path params - name must contain "not_found"
3. Validation error (422) for POST/PUT with missing required fields - name must contain "validation_error"

Return ONLY the JSON array, no other text."""

        return prompt

    def _parse_llm_response(
        self, response_text: str, endpoint: Endpoint
    ) -> list[GeneratedTestCase]:
        """Parse LLM response into TestCase objects"""
        try:
            # Try to extract JSON from response
            text = response_text.strip()

            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            test_data = json.loads(text)

            if not isinstance(test_data, list):
                test_data = [test_data]

            test_cases = []
            for i, tc in enumerate(test_data):
                test_cases.append(
                    GeneratedTestCase(
                        name=tc.get("name", f"test_{endpoint.operation_id}_{i}"),
                        description=tc.get("description", ""),
                        method=endpoint.method,
                        path=endpoint.path,
                        expected_status=tc.get("expected_status", 200),
                        request_body=tc.get("request_body"),
                        path_params=tc.get("path_params"),
                        query_params=tc.get("query_params"),
                        assertions=tc.get(
                            "assertions",
                            [f"assert response.status_code == {tc.get('expected_status', 200)}"],
                        ),
                    )
                )

            return test_cases

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"Warning: Failed to parse LLM response: {e}")
            # Fall back to mock generation
            mock = MockLLMClient()
            plan = mock.generate_test_plan(endpoint, NormalizedSpec(
                title="", version="", endpoints=[endpoint], schemas={}
            ))
            return plan.test_cases

    def generate_tests_for_spec(self, spec: NormalizedSpec) -> list[GeneratedTestPlan]:
        """Generate test plans for all endpoints"""
        return [self.generate_test_plan(ep, spec) for ep in spec.endpoints]


# =============================================================================
# OpenAI Client
# =============================================================================


class OpenAIClient(BaseLLMClient):
    """
    OpenAI GPT client for test generation.

    Requires OPENAI_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAIClient")

        # Import here to make it optional
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "openai package is required. Install with: pip install openai"
            )

    def generate_test_plan(self, endpoint: Endpoint, spec: NormalizedSpec) -> GeneratedTestPlan:
        """Generate test plan using OpenAI GPT"""
        prompt = self._build_prompt(endpoint, spec)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert API tester. Generate comprehensive pytest test cases for API endpoints. Always respond with valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            response_text = response.choices[0].message.content
            test_cases = self._parse_llm_response(response_text, endpoint)

            return TestPlan(
                endpoint_path=endpoint.path,
                endpoint_method=endpoint.method,
                test_cases=test_cases,
            )

        except Exception as e:
            print(f"Warning: OpenAI API call failed: {e}")
            # Fall back to mock
            mock = MockLLMClient()
            return mock.generate_test_plan(endpoint, spec)


# =============================================================================
# Anthropic Client
# =============================================================================


class AnthropicClient(BaseLLMClient):
    """
    Anthropic Claude client for test generation.

    Requires ANTHROPIC_API_KEY environment variable.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
    ):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
        self.model = model

        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for AnthropicClient")

        # Import here to make it optional
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package is required. Install with: pip install anthropic"
            )

    def generate_test_plan(self, endpoint: Endpoint, spec: NormalizedSpec) -> GeneratedTestPlan:
        """Generate test plan using Anthropic Claude"""
        prompt = self._build_prompt(endpoint, spec)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": f"You are an expert API tester. Generate comprehensive pytest test cases. Always respond with valid JSON only, no other text.\n\n{prompt}",
                    }
                ],
            )

            response_text = response.content[0].text
            test_cases = self._parse_llm_response(response_text, endpoint)

            return TestPlan(
                endpoint_path=endpoint.path,
                endpoint_method=endpoint.method,
                test_cases=test_cases,
            )

        except Exception as e:
            print(f"Warning: Anthropic API call failed: {e}")
            # Fall back to mock
            mock = MockLLMClient()
            return mock.generate_test_plan(endpoint, spec)


# =============================================================================
# Legacy RealLLMClient (for backwards compatibility)
# =============================================================================


class RealLLMClient(BaseLLMClient):
    """
    Legacy real LLM client - routes to OpenAI or Anthropic based on provider.

    Kept for backwards compatibility.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.api_key = api_key

        if self.provider == "openai":
            self._client = OpenAIClient(api_key=api_key, model=model or "gpt-4o-mini")
        elif self.provider == "anthropic":
            self._client = AnthropicClient(api_key=api_key, model=model or "claude-3-haiku-20240307")
        else:
            raise ValueError(f"Unknown provider: {provider}. Use 'openai' or 'anthropic'")

    def generate_test_plan(self, endpoint: Endpoint, spec: NormalizedSpec) -> GeneratedTestPlan:
        return self._client.generate_test_plan(endpoint, spec)

    def generate_tests_for_spec(self, spec: NormalizedSpec) -> list[GeneratedTestPlan]:
        return self._client.generate_tests_for_spec(spec)


# =============================================================================
# Factory Function
# =============================================================================


def get_llm_client(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> LLMClient:
    """
    Factory function to get the appropriate LLM client.

    Args:
        provider: "mock", "openai", or "anthropic". Defaults to env LLM_PROVIDER or "mock"
        api_key: API key for the provider. Defaults to env variable
        model: Model name. Defaults to provider's default model

    Returns:
        Configured LLM client

    Environment variables:
        LLM_PROVIDER: Default provider (mock, openai, anthropic)
        OPENAI_API_KEY: OpenAI API key
        ANTHROPIC_API_KEY: Anthropic API key
        LLM_API_KEY: Fallback API key for any provider
        OPENAI_MODEL: Default OpenAI model
        ANTHROPIC_MODEL: Default Anthropic model
    """
    # Determine provider
    if provider is None:
        provider = os.environ.get("LLM_PROVIDER", "mock")

    provider = provider.lower()

    # Mock client (default)
    if provider == "mock":
        return MockLLMClient()

    # OpenAI client
    if provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
        if not key:
            print("Warning: No OpenAI API key found, falling back to mock")
            return MockLLMClient()
        mdl = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        return OpenAIClient(api_key=key, model=mdl)

    # Anthropic client
    if provider == "anthropic":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
        if not key:
            print("Warning: No Anthropic API key found, falling back to mock")
            return MockLLMClient()
        mdl = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
        return AnthropicClient(api_key=key, model=mdl)

    # Unknown provider
    print(f"Warning: Unknown provider '{provider}', falling back to mock")
    return MockLLMClient()
