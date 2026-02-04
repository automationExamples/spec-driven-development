# tests/test_tasks_api.py
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.service import TaskService
from app.storage import StorageConfig, TaskStorage


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    """
    Create an isolated TestClient per test by swapping app globals to use
    a temp JSON file for persistence.
    """
    data_path = tmp_path / "tasks.json"

    storage = TaskStorage(StorageConfig(data_path=data_path))
    service = TaskService(storage)

    # Patch the app module globals
    import app.main as main

    main.storage = storage
    main.service = service

    return TestClient(app)


def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_get_task(client: TestClient):
    r = client.post(
        "/tasks",
        json={"title": "Pay rent", "description": "Before Friday", "tags": ["finance", "home"]},
    )
    assert r.status_code == 201
    task = r.json()

    assert "id" in task
    assert task["title"] == "Pay rent"
    assert task["description"] == "Before Friday"
    assert task["tags"] == ["finance", "home"]
    assert task["status"] == "todo"
    assert "created_at" in task
    assert "updated_at" in task

    r2 = client.get(f"/tasks/{task['id']}")
    assert r2.status_code == 200
    assert r2.json()["id"] == task["id"]


def test_create_validation_errors(client: TestClient):
    r = client.post("/tasks", json={"title": ""})
    assert r.status_code == 422

    r2 = client.post("/tasks", json={"description": "x"})
    assert r2.status_code == 422


def test_list_defaults_and_total(client: TestClient):
    client.post("/tasks", json={"title": "Task A"})
    client.post("/tasks", json={"title": "Task B"})
    r = client.get("/tasks")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_patch_task_updates_status(client: TestClient):
    task = client.post("/tasks", json={"title": "Task A"}).json()

    r = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert r.status_code == 200
    updated = r.json()
    assert updated["status"] == "done"
    assert updated["id"] == task["id"]
    assert updated["updated_at"] != task["updated_at"]


def test_patch_validation_errors(client: TestClient):
    task = client.post("/tasks", json={"title": "Task A"}).json()

    r = client.patch(f"/tasks/{task['id']}", json={"status": "completed"})
    assert r.status_code == 422

    r2 = client.patch(f"/tasks/{task['id']}", json={"title": ""})
    assert r2.status_code == 422


def test_search_q_matches_title_description_tags(client: TestClient):
    client.post("/tasks", json={"title": "Buy milk", "description": "2% please", "tags": ["groceries"]})
    client.post("/tasks", json={"title": "Read book", "description": "Way of Kings", "tags": ["fun", "reading"]})

    r = client.get("/tasks", params={"q": "kings"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "Read book"

    r2 = client.get("/tasks", params={"q": "groceries"})
    assert r2.status_code == 200
    assert r2.json()["total"] == 1
    assert r2.json()["items"][0]["title"] == "Buy milk"


def test_filter_by_status(client: TestClient):
    t1 = client.post("/tasks", json={"title": "Task A"}).json()
    t2 = client.post("/tasks", json={"title": "Task B"}).json()

    client.patch(f"/tasks/{t2['id']}", json={"status": "in_progress"})

    r = client.get("/tasks", params={"status": "in_progress"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == t2["id"]

    r2 = client.get("/tasks", params={"status": "todo"})
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["total"] == 1
    assert body2["items"][0]["id"] == t1["id"]


def test_filter_by_tag_exact_match(client: TestClient):
    client.post("/tasks", json={"title": "T1", "tags": ["alpha"]})
    client.post("/tasks", json={"title": "T2", "tags": ["alpha", "beta"]})
    client.post("/tasks", json={"title": "T3", "tags": ["alphabet"]})

    r = client.get("/tasks", params={"tag": "alpha"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    titles = {t["title"] for t in body["items"]}
    assert titles == {"T1", "T2"}


def test_pagination_limit_offset(client: TestClient):
    for i in range(10):
        client.post("/tasks", json={"title": f"Task {i}"})

    r1 = client.get("/tasks", params={"limit": 3, "offset": 0})
    assert r1.status_code == 200
    assert r1.json()["total"] == 10
    assert len(r1.json()["items"]) == 3

    r2 = client.get("/tasks", params={"limit": 3, "offset": 3})
    assert r2.status_code == 200
    assert len(r2.json()["items"]) == 3

    ids1 = [t["id"] for t in r1.json()["items"]]
    ids2 = [t["id"] for t in r2.json()["items"]]
    assert set(ids1).isdisjoint(set(ids2))


def test_list_validation_errors(client: TestClient):
    r = client.get("/tasks", params={"limit": 0})
    assert r.status_code == 422

    r2 = client.get("/tasks", params={"offset": -1})
    assert r2.status_code == 422


def test_delete_and_404s(client: TestClient):
    task = client.post("/tasks", json={"title": "Temp"}).json()

    r = client.delete(f"/tasks/{task['id']}")
    assert r.status_code == 204

    r2 = client.get(f"/tasks/{task['id']}")
    assert r2.status_code == 404

    r3 = client.delete(f"/tasks/{task['id']}")
    assert r3.status_code == 404


def test_get_unknown_task_returns_404(client: TestClient):
    r = client.get("/tasks/not-a-real-id")
    assert r.status_code == 404


def test_patch_unknown_task_returns_404(client: TestClient):
    r = client.patch("/tasks/not-a-real-id", json={"status": "done"})
    assert r.status_code == 404
