from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from .models import Task, TaskCreate, TaskListResponse, TaskStatus, TaskUpdate
from .service import ListQuery, TaskService
from .storage import StorageConfig, TaskStorage

app = FastAPI(title="TaskBox API", version="1.0.0")

storage = TaskStorage(StorageConfig())
service = TaskService(storage)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(payload: TaskCreate):
    return service.create(payload)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    task = service.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.patch("/tasks/{task_id}", response_model=Task)
def patch_task(task_id: str, patch: TaskUpdate):
    task = service.update(task_id, patch)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    deleted = service.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(status_code=204, content=None)


@app.get("/tasks", response_model=TaskListResponse)
def list_tasks(
    q: str | None = Query(default=None, max_length=200),
    status: TaskStatus | None = None,
    tag: str | None = Query(default=None, max_length=50),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    total, items = service.list(ListQuery(q=q, status=status, tag=tag, limit=limit, offset=offset))
    return TaskListResponse(total=total, items=items)
