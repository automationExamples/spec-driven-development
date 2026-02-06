import importlib
import os

import pytest
from fastapi.testclient import TestClient


def create_client(tmp_path: pytest.TempPathFactory) -> TestClient:
    db_path = tmp_path / "test.sqlite3"
    os.environ["APP_DB_PATH"] = str(db_path)

    import app.db
    import app.main

    importlib.reload(app.db)
    importlib.reload(app.main)

    return TestClient(app.main.app)


def insert(client: TestClient, name: str, summary: str, placement: str, before_id=None, after_id=None):
    payload = {"name": name, "summary": summary, "placement": placement}
    if before_id is not None:
        payload["before_id"] = before_id
    if after_id is not None:
        payload["after_id"] = after_id
    response = client.post("/applications/insert", json=payload)
    assert response.status_code == 200
    return response.json()


def list_applications(client: TestClient):
    response = client.get("/applications")
    assert response.status_code == 200
    return response.json()


def test_insert_and_list_ordering(tmp_path):
    client = create_client(tmp_path)
    with client:
        a = insert(client, "Alpha", "First", "end")
        b = insert(client, "Bravo", "Second", "end")
        c = insert(client, "Charlie", "Top", "start")

        applications = list_applications(client)
        assert [item["name"] for item in applications] == ["Charlie", "Alpha", "Bravo"]
        assert [item["position"] for item in applications] == [1, 2, 3]

        d = insert(client, "Delta", "Between", "between", before_id=a["id"], after_id=b["id"])
        applications = list_applications(client)
        assert [item["name"] for item in applications] == ["Charlie", "Alpha", "Delta", "Bravo"]
        assert [item["position"] for item in applications] == [1, 2, 3, 4]
        assert d["position"] == 3


def test_move_and_delete(tmp_path):
    client = create_client(tmp_path)
    with client:
        a = insert(client, "Alpha", "First", "end")
        b = insert(client, "Bravo", "Second", "end")
        c = insert(client, "Charlie", "Third", "end")

        move_response = client.post(f"/applications/{b['id']}/move", json={"new_position": 1})
        assert move_response.status_code == 200

        applications = list_applications(client)
        assert [item["name"] for item in applications] == ["Bravo", "Alpha", "Charlie"]
        assert [item["position"] for item in applications] == [1, 2, 3]

        delete_response = client.delete(f"/applications/{a['id']}")
        assert delete_response.status_code == 200

        applications = list_applications(client)
        assert [item["name"] for item in applications] == ["Bravo", "Charlie"]
        assert [item["position"] for item in applications] == [1, 2]


def test_invalid_between_and_move(tmp_path):
    client = create_client(tmp_path)
    with client:
        a = insert(client, "Alpha", "First", "end")
        b = insert(client, "Bravo", "Second", "end")

        bad_between = client.post(
            "/applications/insert",
            json={
                "name": "Bad",
                "summary": "Invalid between",
                "placement": "between",
                "before_id": b["id"],
                "after_id": a["id"],
            },
        )
        assert bad_between.status_code == 400

        missing_between = client.post(
            "/applications/insert",
            json={
                "name": "Missing",
                "summary": "Missing ids",
                "placement": "between",
                "before_id": a["id"],
            },
        )
        assert missing_between.status_code == 400

        out_of_range_move = client.post(
            f"/applications/{a['id']}/move",
            json={"new_position": 99},
        )
        assert out_of_range_move.status_code == 400

        missing_move = client.post(
            "/applications/999/move",
            json={"new_position": 1},
        )
        assert missing_move.status_code == 404

        missing_delete = client.delete("/applications/999")
        assert missing_delete.status_code == 404

        invalid_payload = client.post(
            "/applications/insert",
            json={"name": "", "summary": "", "placement": "start"},
        )
        assert invalid_payload.status_code == 422
