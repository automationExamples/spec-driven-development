import sys
import os
import pytest

# Ensure repository root is on sys.path so `backend` package is importable during tests
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def setup_function():
    # Clear shared in-memory state via test API
    client.post("/test/clear")


def test_create_task():
    res = client.post("/tasks", json={"title": "Hello", "description": "World"})
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Hello"
    assert data["description"] == "World"
    assert data["status"] == "pending"


def test_list_tasks():
    client.post("/tasks", json={"title": "T1", "description": "D1"})
    client.post("/tasks", json={"title": "T2", "description": "D2"})
    res = client.get("/tasks")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_filter_by_status():
    r1 = client.post("/tasks", json={"title": "A", "description": "a"}).json()
    r2 = client.post("/tasks", json={"title": "B", "description": "b"}).json()
    # Set one task to completed via API
    client.patch(f"/tasks/{r2['id']}/status", json={"status": "completed"})
    res_pending = client.get("/tasks", params={"status": "pending"})
    res_completed = client.get("/tasks", params={"status": "completed"})
    assert all(t["status"] == "pending" for t in res_pending.json())
    assert all(t["status"] == "completed" for t in res_completed.json())


def test_update_status_endpoint():
    r = client.post("/tasks", json={"title": "X", "description": "x"}).json()
    res = client.patch(f"/tasks/{r['id']}/status", json={"status": "completed"})
    assert res.status_code == 200
    assert res.json()["status"] == "completed"


def test_invalid_input():
    # missing title should return 422
    res = client.post("/tasks", json={"description": "no title"})
    assert res.status_code == 422

