"""
OpenAPI Parser - Parse and normalize OpenAPI 3.x specs.

This module provides functionality to parse OpenAPI specifications
from YAML or JSON format and normalize them into a consistent internal model.
"""

import json
import yaml
from dataclasses import dataclass, field
from typing import Any, Optional


class OpenAPIParseError(Exception):
    """Raised when parsing an OpenAPI spec fails"""

    pass


@dataclass
class Parameter:
    """Represents an API parameter (path, query, header, cookie)"""

    name: str
    location: str  # path, query, header, cookie
    required: bool = False
    schema_type: str = "string"
    description: Optional[str] = None
    example: Any = None


@dataclass
class RequestBody:
    """Represents a request body schema"""

    content_type: str = "application/json"
    schema: dict = field(default_factory=dict)
    required: bool = False
    example: Any = None


@dataclass
class Response:
    """Represents an API response"""

    status_code: int
    description: str = ""
    schema: Optional[dict] = None
    example: Any = None


@dataclass
class Endpoint:
    """Represents a single API endpoint"""

    path: str
    method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    request_body: Optional[RequestBody] = None
    responses: list[Response] = field(default_factory=list)


@dataclass
class NormalizedSpec:
    """Normalized OpenAPI specification"""

    title: str
    version: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    endpoints: list[Endpoint] = field(default_factory=list)
    schemas: dict = field(default_factory=dict)


def parse_spec(content: str) -> dict:
    """
    Parse OpenAPI spec from YAML or JSON string.

    Args:
        content: The raw spec content as a string

    Returns:
        Parsed spec as a dictionary

    Raises:
        OpenAPIParseError: If the content cannot be parsed
    """
    if not content or not content.strip():
        raise OpenAPIParseError("Empty spec content")

    content = content.strip()

    # Try JSON first
    if content.startswith("{"):
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise OpenAPIParseError(f"Invalid JSON: {e}")

    # Try YAML
    try:
        result = yaml.safe_load(content)
        if not isinstance(result, dict):
            raise OpenAPIParseError("Spec must be a YAML/JSON object")
        return result
    except yaml.YAMLError as e:
        raise OpenAPIParseError(f"Invalid YAML: {e}")


def _resolve_ref(ref: str, spec: dict) -> dict:
    """
    Resolve a $ref pointer in the spec.

    Args:
        ref: The $ref string (e.g., "#/components/schemas/Item")
        spec: The full spec to resolve against

    Returns:
        The resolved schema
    """
    if not ref.startswith("#/"):
        return {}

    parts = ref[2:].split("/")
    result = spec
    for part in parts:
        if isinstance(result, dict) and part in result:
            result = result[part]
        else:
            return {}
    return result if isinstance(result, dict) else {}


def _resolve_schema(schema: dict, spec: dict) -> dict:
    """
    Recursively resolve $ref in a schema.

    Args:
        schema: The schema that may contain $ref
        spec: The full spec to resolve against

    Returns:
        The resolved schema
    """
    if not schema:
        return {}

    if "$ref" in schema:
        resolved = _resolve_ref(schema["$ref"], spec)
        # Merge any additional properties from the original schema
        result = resolved.copy()
        for key, value in schema.items():
            if key != "$ref":
                result[key] = value
        return result

    return schema


def _parse_parameter(param_data: dict, spec: dict) -> Parameter:
    """Parse a parameter definition"""
    # Resolve if it's a reference
    if "$ref" in param_data:
        param_data = _resolve_ref(param_data["$ref"], spec)

    schema = param_data.get("schema", {})
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], spec)

    return Parameter(
        name=param_data.get("name", ""),
        location=param_data.get("in", "query"),
        required=param_data.get("required", False),
        schema_type=schema.get("type", "string"),
        description=param_data.get("description"),
        example=param_data.get("example") or schema.get("example"),
    )


def _parse_request_body(body_data: dict, spec: dict) -> Optional[RequestBody]:
    """Parse a request body definition"""
    if not body_data:
        return None

    # Resolve if it's a reference
    if "$ref" in body_data:
        body_data = _resolve_ref(body_data["$ref"], spec)

    content = body_data.get("content", {})

    # Prefer application/json
    if "application/json" in content:
        content_type = "application/json"
        media_type = content["application/json"]
    elif content:
        content_type = next(iter(content))
        media_type = content[content_type]
    else:
        return None

    schema = media_type.get("schema", {})
    schema = _resolve_schema(schema, spec)

    return RequestBody(
        content_type=content_type,
        schema=schema,
        required=body_data.get("required", False),
        example=media_type.get("example"),
    )


def _parse_responses(responses_data: dict, spec: dict) -> list[Response]:
    """Parse response definitions"""
    responses = []

    for status_code, response_data in responses_data.items():
        # Resolve if it's a reference
        if "$ref" in response_data:
            response_data = _resolve_ref(response_data["$ref"], spec)

        # Get schema from content
        schema = None
        example = None
        content = response_data.get("content", {})
        if "application/json" in content:
            media_type = content["application/json"]
            schema = _resolve_schema(media_type.get("schema", {}), spec)
            example = media_type.get("example")

        try:
            code = int(status_code)
        except ValueError:
            # Handle 'default' or other non-numeric status codes
            code = 0

        responses.append(
            Response(
                status_code=code,
                description=response_data.get("description", ""),
                schema=schema,
                example=example,
            )
        )

    return responses


def _parse_endpoint(path: str, method: str, operation: dict, spec: dict) -> Endpoint:
    """Parse a single endpoint operation"""
    # Collect parameters from both path level and operation level
    parameters = []
    for param in operation.get("parameters", []):
        parameters.append(_parse_parameter(param, spec))

    return Endpoint(
        path=path,
        method=method.upper(),
        operation_id=operation.get("operationId"),
        summary=operation.get("summary"),
        description=operation.get("description"),
        tags=operation.get("tags", []),
        parameters=parameters,
        request_body=_parse_request_body(operation.get("requestBody"), spec),
        responses=_parse_responses(operation.get("responses", {}), spec),
    )


def normalize_spec(raw_spec: dict) -> NormalizedSpec:
    """
    Normalize a parsed OpenAPI spec into our internal model.

    Args:
        raw_spec: The parsed spec dictionary

    Returns:
        NormalizedSpec with all endpoints extracted

    Raises:
        OpenAPIParseError: If the spec is invalid
    """
    # Validate basic structure
    if not isinstance(raw_spec, dict):
        raise OpenAPIParseError("Spec must be an object")

    # Check OpenAPI version
    openapi_version = raw_spec.get("openapi", "")
    if not openapi_version.startswith("3."):
        swagger_version = raw_spec.get("swagger", "")
        if swagger_version:
            raise OpenAPIParseError(
                f"Swagger/OpenAPI 2.x not supported, found version {swagger_version}"
            )
        if not openapi_version:
            raise OpenAPIParseError("Missing 'openapi' version field")
        raise OpenAPIParseError(f"Unsupported OpenAPI version: {openapi_version}")

    # Get info
    info = raw_spec.get("info", {})
    if not info.get("title"):
        raise OpenAPIParseError("Missing required field: info.title")
    if not info.get("version"):
        raise OpenAPIParseError("Missing required field: info.version")

    # Get base URL from servers
    base_url = None
    servers = raw_spec.get("servers", [])
    if servers and isinstance(servers, list) and servers[0].get("url"):
        base_url = servers[0]["url"]

    # Extract schemas
    schemas = raw_spec.get("components", {}).get("schemas", {})

    # Parse all endpoints
    endpoints = []
    paths = raw_spec.get("paths", {})
    http_methods = ["get", "post", "put", "patch", "delete", "head", "options"]

    # Sort paths for deterministic ordering
    for path in sorted(paths.keys()):
        path_item = paths[path]
        if not isinstance(path_item, dict):
            continue

        # Get path-level parameters
        path_params = path_item.get("parameters", [])

        # Sort methods for deterministic ordering
        for method in sorted(http_methods):
            if method in path_item:
                operation = path_item[method]
                if isinstance(operation, dict):
                    # Merge path-level parameters with operation parameters
                    if path_params:
                        op_params = operation.get("parameters", [])
                        operation = operation.copy()
                        operation["parameters"] = path_params + op_params

                    endpoints.append(_parse_endpoint(path, method, operation, raw_spec))

    return NormalizedSpec(
        title=info["title"],
        version=info["version"],
        description=info.get("description"),
        base_url=base_url,
        endpoints=endpoints,
        schemas=schemas,
    )


def parse_and_normalize(content: str) -> NormalizedSpec:
    """
    Convenience function to parse and normalize in one step.

    Args:
        content: Raw spec content as YAML or JSON string

    Returns:
        NormalizedSpec
    """
    raw = parse_spec(content)
    return normalize_spec(raw)
