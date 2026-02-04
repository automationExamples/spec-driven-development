from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from uuid import uuid4

from .models import Task, TaskCreate, TaskStatus, TaskUpdate, utc_now
from .storage import TaskStorage


@dataclass
class ListQuery:
    q: Optional[str] = None
    status: Optional[TaskStatus] = None
    tag: Optional[str] = None
    limit: int = 50
    offset: int = 0


class TaskService:
    def __init__(self, storage: TaskStorage):
        self._storage = storage

    def create(self, payload: TaskCreate) -> Task:
        now = utc_now()
        task = Task(
            id=str(uuid4()),
            title=payload.title.strip(),
            description=payload.description.strip() if payload.description else None,
            tags=[t.strip() for t in payload.tags if t.strip()],
            status=TaskStatus.todo,
            created_at=now,
            updated_at=now,
        )
        return self._storage.upsert(task)

    def get(self, task_id: str) -> Optional[Task]:
        return self._storage.get(task_id)

    def update(self, task_id: str, patch: TaskUpdate) -> Optional[Task]:
        existing = self._storage.get(task_id)
        if not existing:
            return None

        updated = existing.model_copy(deep=True)
        if patch.title is not None:
            updated.title = patch.title.strip()
        if patch.description is not None:
            updated.description = patch.description.strip() if patch.description else None
        if patch.tags is not None:
            updated.tags = [t.strip() for t in patch.tags if t.strip()]
        if patch.status is not None:
            updated.status = patch.status

        updated.updated_at = utc_now()
        return self._storage.upsert(updated)

    def delete(self, task_id: str) -> bool:
        return self._storage.delete(task_id)

    def list(self, query: ListQuery) -> Tuple[int, List[Task]]:
        tasks = list(self._storage.list_all().values())
        tasks.sort(key=lambda t: t.updated_at, reverse=True)

        def matches(t: Task) -> bool:
            if query.status and t.status != query.status:
                return False
            if query.tag and query.tag not in t.tags:
                return False
            if query.q:
                q = query.q.lower()
                hay = (t.title + " " + (t.description or "") + " " + " ".join(t.tags)).lower()
                return q in hay
            return True

        filtered = [t for t in tasks if matches(t)]
        total = len(filtered)

        start = max(query.offset, 0)
        end = start + max(min(query.limit, 200), 1)
        return total, filtered[start:end]
