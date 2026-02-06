# Run Guide

## Prerequisites
- Python 3.11+ (recommended)
- pip

## Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

## Run the Backend API
```powershell
python -m uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000/` and the frontend will load from the same address.

## Run Tests
```powershell
python -m pytest
```

## Notes
- SQLite data is stored in `data.sqlite3` at the repo root.
- Tests use a temporary SQLite file via the `APP_DB_PATH` environment variable.