# Spec-Driven Task App

This repository contains a small spec-driven full-stack example: a FastAPI backend and a plain HTML + JavaScript frontend for managing tasks in memory.

Project structure
```
backend/
	main.py
	models.py
	routes.py
	storage.py
frontend/
	index.html
tests/
	test_tasks.py
requirements.txt
README.md
```

Quickstart

1. Install dependencies (recommended in a virtualenv):

```bash
pip install -r requirements.txt
```

2. Run the backend:

```bash
python -m backend.main
```

The API will be available at `http://127.0.0.1:8000` and the OpenAPI docs at `http://127.0.0.1:8000/docs`.

# Spec-Driven Task Manager

This repository contains a small full-stack Task Manager implemented using a spec-driven approach.

Task spec (single source of truth):

{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "status": "pending | completed"
}

## Run the backend

Install dependencies into a virtualenv, then run with Uvicorn:

```bash
python -m pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

The backend serves the API and the frontend. Open http://localhost:8000/ to use the web UI.

API endpoints:
- `POST /tasks` — create a task (JSON: title, description)
- `GET /tasks` — list tasks
- `GET /tasks?status=pending|completed` — filter tasks by status
- `PATCH /tasks/{id}/status` — update a task's status (JSON: {status: "completed"})

Test-only endpoint:
- `POST /test/clear` — clears in-memory storage (used by the test suite)

## Frontend

Open http://localhost:8000/ in your browser. The single `index.html` page allows creating tasks, filtering, and toggling status.

## Run tests

```bash
python -m pip install -r requirements.txt
pytest -q
```

## How AI / Code generation tools were used

- The project was implemented following a spec-driven workflow. Pydantic models were derived from the task spec and used for validation and OpenAPI generation.
- Code generation tools were used to scaffold boilerplate (models, routes, storage) and to iterate on API shapes and tests, accelerating implementation while preserving human review and refinement.

