# Feature Spec: REST API Endpoints

## Goal
Provide FastAPI endpoints to upload specs, generate tests, run tests.

## Scope
- In: CRUD for specs, sync generation, sync test runs
- Out: Async background jobs, webhooks

## Requirements
- POST /specs to upload OpenAPI spec
- GET /specs to list all specs
- GET /specs/{id} to get spec details
- POST /generate to generate tests for a spec
- GET /generations/{id} to get generation details
- POST /runs to execute tests
- GET /runs/{id} to get results

## Acceptance Criteria
- [ ] POST /specs validates and stores spec, returns spec_id
- [ ] GET /specs returns list of all specs
- [ ] GET /specs/{id} returns spec details with endpoints
- [ ] POST /generate creates pytest files, returns generation_id
- [ ] GET /generations/{id} returns generation status and files
- [ ] POST /runs executes tests, returns run_id and summary
- [ ] GET /runs/{id} returns status, passed, failed, failures list
- [ ] GET /health returns {"status": "ok"}
