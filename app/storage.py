from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Dict, Optional

from .models import Task


@dataclass(frozen=True)
class StorageConfig:
    data_path: Path = Path("data/tasks.json")


class TaskStorage:
    def __init__(self, config: StorageConfig):
        self._cfg = config
        self._lock = RLock()
        self._tasks: Dict[str, Task] = {}
        self._cfg.data_path.parent.mkdir(parents=True, exist_ok=True)
        self._load_if_exists()

    def _load_if_exists(self) -> None:
        if not self._cfg.data_path.exists():
            return
        try:
            raw = self._cfg.data_path.read_text(encoding="utf-8").strip()
            if not raw:
                return
            data = json.loads(raw)
            tasks: Dict[str, Task] = {}
            for item in data.get("tasks", []):
                t = Task.model_validate(item)
                tasks[t.id] = t
            self._tasks = tasks
        except Exception:
            # If corrupted, start empty (no crash)
            self._tasks = {}

    def _flush(self) -> None:
        # Use JSON-safe encoding (datetimes -> ISO strings) via Pydantic "json" mode.
        payload = {"tasks": [t.model_dump(mode="json") for t in self._tasks.values()]}
        tmp = self._cfg.data_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self._cfg.data_path)


    def list_all(self) -> Dict[str, Task]:
        with self._lock:
            return dict(self._tasks)

    def get(self, task_id: str) -> Optional[Task]:
        with self._lock:
            return self._tasks.get(task_id)

    def upsert(self, task: Task) -> Task:
        with self._lock:
            self._tasks[task.id] = task
            self._flush()
            return task

    def delete(self, task_id: str) -> bool:
        with self._lock:
            existed = task_id in self._tasks
            if existed:
                self._tasks.pop(task_id, None)
                self._flush()
            return existed
