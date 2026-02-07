from fastapi import APIRouter, HTTPException
from typing import List, Optional

from . import storage
from .models import TaskCreate, Task

router = APIRouter()


@router.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    task = storage.create_task(payload.title, payload.description)
    return task


@router.get("/tasks", response_model=List[Task])
def get_tasks(status: Optional[str] = None):
    if status and status not in ("pending", "completed"):
        raise HTTPException(status_code=400, detail="invalid status")
    return storage.list_tasks(status)


@router.patch("/tasks/{task_id}/status", response_model=Task)
def patch_status(task_id: str, payload: dict):
    status = payload.get("status")
    if status not in ("pending", "completed"):
        raise HTTPException(status_code=400, detail="invalid status")
    task = storage.update_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="not found")
    return task


# Test-only convenience endpoint to reset in-memory state
@router.post("/test/clear", status_code=204)
def test_clear():
    storage.clear_storage()
    return
