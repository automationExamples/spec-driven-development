"""
Unit tests for OpenAPI parser.
"""

import pytest
from app.openapi_parser import (
    parse_spec,
    normalize_spec,
    parse_and_normalize,
    OpenAPIParseError,
    NormalizedSpec,
)  # noqa: F401


class TestParseSpec:
    """Tests for parse_spec function"""

    def test_parse_valid_yaml(self):
        """Should parse valid YAML content"""
        content = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths: {}
"""
        result = parse_spec(content)
        assert result["openapi"] == "3.0.0"
        assert result["info"]["title"] == "Test API"

    def test_parse_valid_json(self):
        """Should parse valid JSON content"""
        content = '{"openapi": "3.0.0", "info": {"title": "Test API", "version": "1.0.0"}, "paths": {}}'
        result = parse_spec(content)
        assert result["openapi"] == "3.0.0"
        assert result["info"]["title"] == "Test API"

    def test_parse_empty_content_raises_error(self):
        """Should raise error for empty content"""
        with pytest.raises(OpenAPIParseError, match="Empty spec content"):
            parse_spec("")

    def test_parse_whitespace_only_raises_error(self):
        """Should raise error for whitespace-only content"""
        with pytest.raises(OpenAPIParseError, match="Empty spec content"):
            parse_spec("   \n\t  ")

    def test_parse_invalid_json_raises_error(self):
        """Should raise error for invalid JSON"""
        with pytest.raises(OpenAPIParseError, match="Invalid JSON"):
            parse_spec('{"invalid": json}')

    def test_parse_invalid_yaml_raises_error(self):
        """Should raise error for invalid YAML"""
        with pytest.raises(OpenAPIParseError, match="Invalid YAML"):
            parse_spec("key: [unclosed")

    def test_parse_non_object_raises_error(self):
        """Should raise error when spec is not an object"""
        with pytest.raises(OpenAPIParseError, match="must be a YAML/JSON object"):
            parse_spec("- item1\n- item2")


class TestNormalizeSpec:
    """Tests for normalize_spec function"""

    def test_normalize_minimal_spec(self):
        """Should normalize a minimal valid spec"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
        }
        result = normalize_spec(raw)
        assert result.title == "Test API"
        assert result.version == "1.0.0"
        assert result.endpoints == []

    def test_normalize_extracts_base_url(self):
        """Should extract base URL from servers"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "servers": [{"url": "http://localhost:8000"}],
            "paths": {},
        }
        result = normalize_spec(raw)
        assert result.base_url == "http://localhost:8000"

    def test_normalize_missing_openapi_version_raises_error(self):
        """Should raise error when openapi version is missing"""
        raw = {"info": {"title": "Test", "version": "1.0"}, "paths": {}}
        with pytest.raises(OpenAPIParseError, match="Missing 'openapi' version"):
            normalize_spec(raw)

    def test_normalize_swagger_2_raises_error(self):
        """Should raise error for Swagger 2.x specs"""
        raw = {
            "swagger": "2.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
        }
        with pytest.raises(
            OpenAPIParseError, match="Swagger/OpenAPI 2.x not supported"
        ):
            normalize_spec(raw)

    def test_normalize_missing_title_raises_error(self):
        """Should raise error when title is missing"""
        raw = {"openapi": "3.0.0", "info": {"version": "1.0"}, "paths": {}}
        with pytest.raises(
            OpenAPIParseError, match="Missing required field: info.title"
        ):
            normalize_spec(raw)

    def test_normalize_missing_version_raises_error(self):
        """Should raise error when version is missing"""
        raw = {"openapi": "3.0.0", "info": {"title": "Test"}, "paths": {}}
        with pytest.raises(
            OpenAPIParseError, match="Missing required field: info.version"
        ):
            normalize_spec(raw)

    def test_normalize_extracts_endpoints(self):
        """Should extract all endpoints with correct methods"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/items": {
                    "get": {"summary": "List items", "responses": {"200": {}}},
                    "post": {"summary": "Create item", "responses": {"201": {}}},
                },
                "/items/{id}": {
                    "get": {"summary": "Get item", "responses": {"200": {}}}
                },
            },
        }
        result = normalize_spec(raw)
        assert len(result.endpoints) == 3

        # Check endpoints are sorted
        paths_methods = [(e.path, e.method) for e in result.endpoints]
        assert ("/items", "GET") in paths_methods
        assert ("/items", "POST") in paths_methods
        assert ("/items/{id}", "GET") in paths_methods

    def test_normalize_extracts_parameters(self):
        """Should extract path and query parameters"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/items/{id}": {
                    "get": {
                        "parameters": [
                            {
                                "name": "id",
                                "in": "path",
                                "required": True,
                                "schema": {"type": "string"},
                            },
                            {
                                "name": "include",
                                "in": "query",
                                "schema": {"type": "string"},
                            },
                        ],
                        "responses": {"200": {}},
                    }
                }
            },
        }
        result = normalize_spec(raw)
        endpoint = result.endpoints[0]
        assert len(endpoint.parameters) == 2

        id_param = next(p for p in endpoint.parameters if p.name == "id")
        assert id_param.location == "path"
        assert id_param.required is True

        include_param = next(p for p in endpoint.parameters if p.name == "include")
        assert include_param.location == "query"
        assert include_param.required is False

    def test_normalize_extracts_request_body(self):
        """Should extract request body schema"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/items": {
                    "post": {
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {"name": {"type": "string"}},
                                    }
                                }
                            },
                        },
                        "responses": {"201": {}},
                    }
                }
            },
        }
        result = normalize_spec(raw)
        endpoint = result.endpoints[0]
        assert endpoint.request_body is not None
        assert endpoint.request_body.required is True
        assert endpoint.request_body.content_type == "application/json"
        assert endpoint.request_body.schema["type"] == "object"

    def test_normalize_extracts_responses(self):
        """Should extract response schemas"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/items": {
                    "get": {
                        "responses": {
                            "200": {
                                "description": "Success",
                                "content": {
                                    "application/json": {"schema": {"type": "array"}}
                                },
                            },
                            "404": {"description": "Not found"},
                        }
                    }
                }
            },
        }
        result = normalize_spec(raw)
        endpoint = result.endpoints[0]
        assert len(endpoint.responses) == 2

        ok_response = next(r for r in endpoint.responses if r.status_code == 200)
        assert ok_response.description == "Success"
        assert ok_response.schema["type"] == "array"

        not_found = next(r for r in endpoint.responses if r.status_code == 404)
        assert not_found.description == "Not found"
        assert not_found.schema is None

    def test_normalize_resolves_schema_refs(self):
        """Should resolve $ref references in schemas"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/items": {
                    "post": {
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            }
                        },
                        "responses": {"201": {}},
                    }
                }
            },
            "components": {
                "schemas": {
                    "Item": {
                        "type": "object",
                        "required": ["name"],
                        "properties": {"name": {"type": "string"}},
                    }
                }
            },
        }
        result = normalize_spec(raw)
        endpoint = result.endpoints[0]
        assert endpoint.request_body.schema["type"] == "object"
        assert "name" in endpoint.request_body.schema["properties"]

    def test_normalize_extracts_schemas(self):
        """Should extract component schemas"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {},
            "components": {
                "schemas": {"Item": {"type": "object"}, "Error": {"type": "object"}}
            },
        }
        result = normalize_spec(raw)
        assert "Item" in result.schemas
        assert "Error" in result.schemas


class TestParseAndNormalize:
    """Tests for the convenience function"""

    def test_parse_and_normalize_yaml(self):
        """Should parse and normalize YAML in one step"""
        content = """
openapi: "3.0.0"
info:
  title: Test API
  version: "1.0.0"
paths:
  /health:
    get:
      responses:
        "200":
          description: OK
"""
        result = parse_and_normalize(content)
        assert isinstance(result, NormalizedSpec)
        assert result.title == "Test API"
        assert len(result.endpoints) == 1
        assert result.endpoints[0].path == "/health"


class TestEndpointOrdering:
    """Tests for deterministic endpoint ordering"""

    def test_endpoints_sorted_by_path_then_method(self):
        """Endpoints should be sorted by path, then by method"""
        raw = {
            "openapi": "3.0.0",
            "info": {"title": "Test", "version": "1.0"},
            "paths": {
                "/z": {"post": {"responses": {}}, "get": {"responses": {}}},
                "/a": {"delete": {"responses": {}}, "get": {"responses": {}}},
            },
        }
        result = normalize_spec(raw)

        paths_methods = [(e.path, e.method) for e in result.endpoints]
        # Should be sorted: /a first, then /z; within each path, methods sorted alphabetically
        assert paths_methods == [
            ("/a", "DELETE"),
            ("/a", "GET"),
            ("/z", "GET"),
            ("/z", "POST"),
        ]
