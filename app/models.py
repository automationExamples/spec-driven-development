from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    tags: List[str] = Field(default_factory=list, max_length=20)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    tags: Optional[List[str]] = Field(default=None, max_length=20)
    status: Optional[TaskStatus] = None


class Task(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.todo
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    total: int
    items: List[Task]
