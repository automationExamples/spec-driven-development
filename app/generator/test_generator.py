"""
Test Generator - Generate pytest files from OpenAPI specs.

This module takes a normalized OpenAPI spec and generates
executable pytest test files.
"""

from pathlib import Path
from typing import Optional

from app.openapi_parser import NormalizedSpec
from .llm_client import LLMClient, MockLLMClient, TestPlan, TestCase


class PytestGenerator:
    """
    Generates pytest test files from OpenAPI specifications.
    """

    def __init__(
        self, llm_client: Optional[LLMClient] = None, output_dir: Optional[Path] = None
    ):
        """
        Initialize the test generator.

        Args:
            llm_client: LLM client to use for generation. Defaults to MockLLMClient.
            output_dir: Directory to write generated tests. Defaults to ./generated_tests
        """
        self.llm_client = llm_client or MockLLMClient()
        self.output_dir = output_dir or Path("./generated_tests")

    def generate(self, spec: NormalizedSpec, spec_id: str) -> list[Path]:
        """
        Generate pytest files for a spec.

        Args:
            spec: The normalized OpenAPI spec
            spec_id: Unique identifier for this spec (used in directory name)

        Returns:
            List of paths to generated test files
        """
        # Create output directory
        test_dir = self.output_dir / spec_id
        test_dir.mkdir(parents=True, exist_ok=True)

        # Generate test plans
        test_plans = self.llm_client.generate_tests_for_spec(spec)

        # Generate files
        generated_files = []

        # Generate conftest.py
        conftest_path = test_dir / "conftest.py"
        conftest_content = self._generate_conftest(spec)
        conftest_path.write_text(conftest_content)
        generated_files.append(conftest_path)

        # Group test plans by path for file organization
        plans_by_resource = self._group_by_resource(test_plans)

        for resource_name, plans in plans_by_resource.items():
            test_file = test_dir / f"test_{resource_name}.py"
            content = self._generate_test_file(plans, spec)
            test_file.write_text(content)
            generated_files.append(test_file)

        return generated_files

    def _group_by_resource(self, plans: list[TestPlan]) -> dict[str, list[TestPlan]]:
        """Group test plans by resource (first path segment)"""
        groups = {}
        for plan in plans:
            # Extract resource name from path
            path_parts = plan.endpoint_path.strip("/").split("/")
            resource = path_parts[0] if path_parts else "root"
            resource = resource.replace("{", "").replace("}", "")

            if resource not in groups:
                groups[resource] = []
            groups[resource].append(plan)

        return groups

    def _generate_conftest(self, spec: NormalizedSpec) -> str:
        """Generate conftest.py with fixtures"""
        base_url = spec.base_url or "http://localhost:8001"

        return f'''"""
Pytest fixtures for {spec.title} tests.
Auto-generated from OpenAPI spec.
"""
import os
import pytest
import httpx


@pytest.fixture
def base_url():
    """Base URL for the API under test"""
    return os.environ.get("TARGET_BASE_URL", "{base_url}")


@pytest.fixture
def client(base_url):
    """HTTP client for making requests"""
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture
def auth_headers():
    """Optional authentication headers"""
    token = os.environ.get("API_TOKEN")
    if token:
        return {{"Authorization": f"Bearer {{token}}"}}
    return {{}}
'''

    def _generate_test_file(self, plans: list[TestPlan], spec: NormalizedSpec) -> str:
        """Generate a test file for a set of test plans"""
        lines = [
            '"""',
            f"Auto-generated tests for {spec.title}",
            '"""',
            "import pytest",
            "",
            "",
        ]

        for plan in plans:
            for test_case in plan.test_cases:
                lines.extend(self._generate_test_function(test_case))
                lines.append("")

        return "\n".join(lines)

    def _generate_test_function(self, test_case: TestCase) -> list[str]:
        """Generate a single test function"""
        lines = []

        # Function definition
        lines.append(f"def {test_case.name}(client):")
        lines.append('    """')
        lines.append(f"    {test_case.description}")
        lines.append('    """')

        # Check if this is a success test for GET/DELETE with path params
        # These need to create the resource first
        test_name_lower = test_case.name.lower()
        is_error_test = any(
            term in test_name_lower
            for term in ["not_found", "notfound", "error", "invalid", "404", "422"]
        )
        needs_setup = (
            test_case.path_params
            and test_case.method in ["GET", "DELETE"]
            and not is_error_test
            and test_case.expected_status in [200, 204]
        )

        if needs_setup:
            # Generate setup code to create the resource first
            lines.extend(self._generate_resource_setup(test_case))
        else:
            # Build the request path directly
            path = test_case.path
            if test_case.path_params:
                for param_name, param_value in test_case.path_params.items():
                    path = path.replace(f"{{{param_name}}}", f"{param_value}")
                lines.append(f'    url = "{path}"')
            else:
                lines.append(f'    url = "{path}"')

            # Make the request
            method = test_case.method.lower()
            if test_case.request_body is not None:
                body_str = repr(test_case.request_body)
                lines.append(f"    response = client.{method}(url, json={body_str})")
            else:
                lines.append(f"    response = client.{method}(url)")

        # Add assertions
        lines.append("")
        for assertion in test_case.assertions:
            lines.append(f"    {assertion}")

        return lines

    def _generate_resource_setup(self, test_case: TestCase) -> list[str]:
        """Generate setup code to create a resource before GET/DELETE tests"""
        lines = []

        # Extract the collection path (e.g., /items from /items/{id})
        path_parts = test_case.path.split("/")
        # Find the part with {param} and take everything before it
        collection_parts = []
        for part in path_parts:
            if "{" in part:
                break
            collection_parts.append(part)
        collection_path = "/".join(collection_parts)

        # First create the resource
        lines.append(f'    # First, create a resource to {test_case.method.lower()}')
        lines.append(f'    create_response = client.post("{collection_path}", json={{"name": "Test Item", "price": 9.99}})')
        lines.append('    assert create_response.status_code in [200, 201], f"Setup failed: {create_response.text}"')
        lines.append('    created = create_response.json()')
        lines.append('    resource_id = created.get("id", created.get("_id", ""))')
        lines.append("")

        # Now make the actual request using the created ID
        # Replace path param with the dynamic ID
        path_template = test_case.path
        for param_name in test_case.path_params.keys():
            path_template = path_template.replace(f"{{{param_name}}}", "{resource_id}")

        lines.append(f'    url = f"{path_template}"')
        method = test_case.method.lower()
        lines.append(f"    response = client.{method}(url)")

        return lines


def generate_tests(
    spec: NormalizedSpec,
    spec_id: str,
    output_dir: Optional[Path] = None,
    llm_client: Optional[LLMClient] = None,
) -> list[Path]:
    """
    Convenience function to generate tests.

    Args:
        spec: The normalized OpenAPI spec
        spec_id: Unique identifier for this spec
        output_dir: Directory to write tests
        llm_client: LLM client to use

    Returns:
        List of generated file paths
    """
    generator = PytestGenerator(llm_client=llm_client, output_dir=output_dir)
    return generator.generate(spec, spec_id)
