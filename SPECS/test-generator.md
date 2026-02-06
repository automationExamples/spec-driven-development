# Feature Spec: Test Generator

## Goal
Generate pytest test files from normalized OpenAPI specs.

## Scope
- In: Mock LLM (deterministic), Real LLM (optional), pytest output
- Out: Other test frameworks, complex test scenarios

## Requirements
- LLMClient interface with generate_tests() method
- MockLLMClient returns deterministic output (no API calls)
- RealLLMClient wraps OpenAI/Anthropic (optional, via env var)
- Generate tests: happy path, negative cases, schema validation

## Acceptance Criteria
- [ ] MockLLMClient generates same output for same input
- [ ] Generated Python code is syntactically valid (ast.parse)
- [ ] Happy path test for each endpoint
- [ ] 404 test for GET endpoints with path params
- [ ] 400/422 test for POST endpoints with required fields
- [ ] Tests use httpx client
- [ ] conftest.py generated with fixtures
