from fastapi import APIRouter, HTTPException

from app.db import (
    delete_application,
    fetch_all_applications,
    get_application_by_id,
    insert_application_between,
    insert_application_end,
    insert_application_start,
    move_application,
)
from app.models import Application
from app.schemas import ApplicationOut, InsertRequest, MoveRequest

router = APIRouter(tags=["applications"])


@router.get("/applications", response_model=list[ApplicationOut])
def list_applications() -> list[ApplicationOut]:
    rows = fetch_all_applications()
    applications = [Application.from_row(row) for row in rows]
    return [ApplicationOut(**application.__dict__) for application in applications]


@router.post("/applications/insert", response_model=ApplicationOut)
def insert_application(payload: InsertRequest) -> ApplicationOut:
    if payload.placement == "start":
        application_id = insert_application_start(payload.name, payload.summary)
    elif payload.placement == "end":
        application_id = insert_application_end(payload.name, payload.summary)
    else:
        if payload.before_id is None or payload.after_id is None:
            raise HTTPException(status_code=400, detail="before_id and after_id required")
        if payload.before_id == payload.after_id:
            raise HTTPException(status_code=400, detail="before_id and after_id must differ")
        try:
            application_id = insert_application_between(
                payload.name, payload.summary, payload.before_id, payload.after_id
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    row = get_application_by_id(application_id)
    if row is None:
        raise HTTPException(status_code=500, detail="failed to load inserted application")
    return ApplicationOut(**Application.from_row(row).__dict__)


@router.post("/applications/{application_id}/move")
def move_application_endpoint(application_id: int, payload: MoveRequest) -> dict:
    try:
        move_application(application_id, payload.new_position)
    except ValueError as exc:
        detail = str(exc)
        if detail == "application not found":
            raise HTTPException(status_code=404, detail=detail) from exc
        raise HTTPException(status_code=400, detail=detail) from exc
    return {"status": "ok"}


@router.delete("/applications/{application_id}")
def delete_application_endpoint(application_id: int) -> dict:
    try:
        delete_application(application_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": "ok"}
