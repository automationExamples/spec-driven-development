from pydantic import BaseModel
from typing import Literal


class TaskBase(BaseModel):
    title: str
    description: str


class TaskCreate(TaskBase):
    pass


class Task(TaskBase):
    id: str
    status: Literal["pending", "completed"]
from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import UUID


class Task(BaseModel):
    id: UUID
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
    status: Literal["pending", "completed"] = "pending"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = ""
