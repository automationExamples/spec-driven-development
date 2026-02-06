# Architecture Overview

## System Structure
- `app/main.py`: FastAPI app bootstrap, startup init, and static file mounting.
- `app/db.py`: SQLite connection management and ranking operations (insert, move, delete).
- `app/schemas.py`: Pydantic request/response models.
- `app/models.py`: Lightweight domain model for applications.
- `app/routers/applications.py`: API endpoints for queue operations.
- `static/`: Frontend UI (HTML/CSS/JS) served by FastAPI.
- `tests/`: Pytest coverage for ranking workflows.

## Data Model
Single SQLite table `applications`:
- `id` (auto-increment)
- `name`
- `summary`
- `position` (1-based rank)

`position` is treated as the canonical ranking, with reindexing on insert/move/delete.

## Key Design Decisions
- Integer ranking with reindexing:
  - Keeps ordering deterministic and easy to reason about.
  - Avoids fractional rank drift and simplifies constraints.
- SQLite for persistence:
  - Zero-config local storage fits assessment constraints.
  - Simple to reset or inspect via a single file.
- Frontend as static assets served by FastAPI:
  - Minimal setup and no build step.
  - Keeps deployment and local run straightforward.
- Backend validates bounds, frontend clamps:
  - UI clamps move requests to `[1, max]` for convenience.
  - Backend still enforces range to avoid invalid data.

## Sample Commands

### List Applications
```powershell
curl http://127.0.0.1:8000/applications
```

### Insert at End
```powershell
curl -X POST http://127.0.0.1:8000/applications/insert ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Jane Doe\",\"summary\":\"Small business line of credit\",\"placement\":\"end\"}"
```

### Insert at Start
```powershell
curl -X POST http://127.0.0.1:8000/applications/insert ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Urgent Review\",\"summary\":\"Escalated request\",\"placement\":\"start\"}"
```

### Insert Between Two Items
```powershell
curl -X POST http://127.0.0.1:8000/applications/insert ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Priority Insert\",\"summary\":\"Manual triage\",\"placement\":\"between\",\"before_id\":1,\"after_id\":2}"
```

### Move (Change Rank)
```powershell
curl -X POST http://127.0.0.1:8000/applications/3/move ^
  -H "Content-Type: application/json" ^
  -d "{\"new_position\":1}"
```

### Delete
```powershell
curl -X DELETE http://127.0.0.1:8000/applications/3
```

## Testing Focus
- Ordering after inserts (start/end/between).
- Reindexing after moves and deletes.
- Error handling for invalid moves and unknown IDs is enforced by the API.