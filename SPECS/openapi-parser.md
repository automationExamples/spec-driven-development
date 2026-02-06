# Feature Spec: OpenAPI Parser

## Goal
Parse and normalize OpenAPI 3.x specs into internal model.

## Scope
- In: YAML/JSON parsing, endpoint extraction, schema extraction
- Out: OpenAPI 2.x (Swagger), code generation from schemas

## Requirements
- Parse YAML and JSON format specs
- Extract all endpoints with path, method, parameters
- Extract request body schemas
- Extract response codes and schemas
- Handle $ref references in schemas

## Acceptance Criteria
- [ ] parse_spec() handles valid YAML
- [ ] parse_spec() handles valid JSON
- [ ] parse_spec() raises error on invalid content
- [ ] normalize_spec() returns NormalizedSpec with all endpoints
- [ ] Parameters (path, query) extracted correctly
- [ ] Request body schema extracted when present
- [ ] Response schemas extracted for each status code
- [ ] $ref references resolved correctly
