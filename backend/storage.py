"""In-memory, thread-safe storage for tasks.

This module stores tasks as dictionaries with string UUID ids. It provides
thread-safe functions matching the API expectations used in the tests and
routes: `create_task`, `list_tasks`, `update_status`, and `clear_storage`.
"""
from typing import Dict, List, Optional
import threading
import uuid

_lock = threading.Lock()
_tasks: Dict[str, Dict] = {}


def clear_storage() -> None:
    with _lock:
        _tasks.clear()


def create_task(title: str, description: str) -> Dict:
    with _lock:
        task_id = str(uuid.uuid4())
        task = {"id": task_id, "title": title, "description": description, "status": "pending"}
        _tasks[task_id] = task
        return task.copy()


def list_tasks(status: Optional[str] = None) -> List[Dict]:
    with _lock:
        items = list(_tasks.values())
        if status:
            items = [t.copy() for t in items if t["status"] == status]
        else:
            items = [t.copy() for t in items]
        return items


def update_status(task_id: str, status: str) -> Optional[Dict]:
    if status not in ("pending", "completed"):
        raise ValueError("invalid status")
    with _lock:
        if task_id not in _tasks:
            return None
        _tasks[task_id]["status"] = status
        return _tasks[task_id].copy()
