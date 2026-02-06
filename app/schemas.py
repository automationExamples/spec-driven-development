from pydantic import BaseModel, Field


class ApplicationOut(BaseModel):
    id: int
    name: str
    summary: str
    position: int


class ApplicationCreate(BaseModel):
    name: str = Field(min_length=1)
    summary: str = Field(min_length=1)


class InsertRequest(ApplicationCreate):
    placement: str = Field(pattern="^(start|end|between)$")
    before_id: int | None = None
    after_id: int | None = None


class MoveRequest(BaseModel):
    new_position: int = Field(ge=1)
