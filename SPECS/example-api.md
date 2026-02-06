# Feature Spec: Example Target API

## Goal
Provide a simple FastAPI application to test generated tests against.

## Scope
- In: Basic CRUD for items resource
- Out: Authentication, complex relationships

## Requirements
- GET /health returns status
- POST /items creates item with name and price
- GET /items/{id} returns item or 404
- GET /items returns list of all items

## Acceptance Criteria
- [ ] Health endpoint returns {"status": "ok"}
- [ ] POST /items with valid body returns 201 + created item with id
- [ ] POST /items with missing required fields returns 422
- [ ] GET /items returns list of all items
- [ ] GET /items/{id} with valid id returns 200 + item
- [ ] GET /items/{id} with invalid id returns 404
- [ ] OpenAPI spec matches implementation
