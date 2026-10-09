"""HTTP control plane for the opt-in asynchronous material parser."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.auth.middleware import AuthenticatedRoute
from agentops.common.orm import get_orm_session
from agentops.project_memory.async_parser import cancel_parse_job, enqueue_parse_job, retry_parse_job
from agentops.rag.authz import AuthzError, current_user_id, require_admin, require_member


router = APIRouter(route_class=AuthenticatedRoute)


class EnqueueParseRequest(BaseModel):
    project_id: uuid.UUID
    intake_file_id: uuid.UUID
    timeout_seconds: int = Field(default=900, ge=1, le=86_400)
    max_attempts: int = Field(default=3, ge=1, le=10)


class ParseJobResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    intake_file_id: uuid.UUID
    status: str
    attempt_count: int
    max_attempts: int
    timeout_seconds: int
    lease_expires_at: str | None = None
    next_attempt_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    error_message: str | None = None
    result_metadata: dict = Field(default_factory=dict)


def _auth(request: Request) -> uuid.UUID:
    try:
        return current_user_id(request)
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


def _response(row) -> ParseJobResponse:
    return ParseJobResponse(
        id=uuid.UUID(str(row.id)), project_id=uuid.UUID(str(row.project_id)),
        intake_file_id=uuid.UUID(str(row.intake_file_id)), status=str(row.status),
        attempt_count=int(row.attempt_count or 0), max_attempts=int(row.max_attempts or 3),
        timeout_seconds=int(row.timeout_seconds or 900),
        lease_expires_at=str(row.lease_expires_at) if row.lease_expires_at else None,
        next_attempt_at=str(row.next_attempt_at) if getattr(row, "next_attempt_at", None) else None,
        started_at=str(row.started_at) if getattr(row, "started_at", None) else None,
        completed_at=str(row.completed_at) if getattr(row, "completed_at", None) else None,
        error_message=str(row.error_message) if row.error_message else None,
        result_metadata=dict(row.result_metadata or {}),
    )


@router.post("/knowledge/material-parse-jobs", response_model=ParseJobResponse)
def enqueue_material_parse_job(
    request: Request,
    body: EnqueueParseRequest,
    orm: Session = Depends(get_orm_session),
) -> ParseJobResponse:
    user_id = _auth(request)
    try:
        require_member(orm, user_id=user_id, project_id=body.project_id)
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    intake = orm.execute(
        text("""
            SELECT i.project_id
              FROM public.project_material_intake_files f
              JOIN public.project_material_intakes i ON i.id = f.intake_id
             WHERE f.id = :intake_file_id
        """),
        {"intake_file_id": str(body.intake_file_id)},
    ).first()
    if intake is None or uuid.UUID(str(intake.project_id)) != body.project_id:
        # Keep cross-project file identifiers opaque to callers.
        raise HTTPException(status_code=404, detail="intake file does not belong to project")
    row = orm.execute(
        text("""
            SELECT id, project_id, intake_file_id, status, attempt_count,
                   max_attempts, timeout_seconds, lease_expires_at,
                   next_attempt_at::text AS next_attempt_at, started_at, completed_at,
                   error_message, result_metadata
              FROM public.project_material_parse_jobs
             WHERE project_id = :project_id AND intake_file_id = :intake_file_id
        """),
        {"project_id": str(body.project_id), "intake_file_id": str(body.intake_file_id)},
    ).first()
    if row is None:
        job_id = enqueue_parse_job(
            orm,
            project_id=body.project_id,
            intake_file_id=body.intake_file_id,
            created_by_user_id=user_id,
            timeout_seconds=body.timeout_seconds,
            max_attempts=body.max_attempts,
        )
        row = orm.execute(
            text("""
                SELECT id, project_id, intake_file_id, status, attempt_count,
                       max_attempts, timeout_seconds, lease_expires_at,
                       next_attempt_at::text AS next_attempt_at, started_at, completed_at,
                       error_message, result_metadata
                  FROM public.project_material_parse_jobs WHERE id = :id
            """),
            {"id": str(job_id)},
        ).first()
        # ``get_orm_session`` closes without an implicit commit.  The upload
        # confirmation path commits its encompassing transaction, but this
        # standalone control-plane endpoint must persist the enqueue itself.
        orm.commit()
    if row is None:
        raise HTTPException(status_code=503, detail="parse job was not persisted")
    return _response(row)


@router.get("/knowledge/material-parse-jobs/{job_id}", response_model=ParseJobResponse)
def get_material_parse_job(
    request: Request,
    job_id: uuid.UUID,
    orm: Session = Depends(get_orm_session),
) -> ParseJobResponse:
    user_id = _auth(request)
    row = orm.execute(
        text("""
            SELECT id, project_id, intake_file_id, status, attempt_count,
                   max_attempts, timeout_seconds, lease_expires_at,
                   next_attempt_at::text AS next_attempt_at, started_at, completed_at,
                   error_message, result_metadata
              FROM public.project_material_parse_jobs WHERE id = :id
        """),
        {"id": str(job_id)},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="parse job not found")
    try:
        require_member(orm, user_id=user_id, project_id=uuid.UUID(str(row.project_id)))
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return _response(row)


@router.delete("/knowledge/material-parse-jobs/{job_id}", status_code=204)
def cancel_material_parse_job(
    request: Request,
    job_id: uuid.UUID,
    orm: Session = Depends(get_orm_session),
) -> None:
    user_id = _auth(request)
    row = orm.execute(
        text("SELECT project_id FROM public.project_material_parse_jobs WHERE id = :id"),
        {"id": str(job_id)},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="parse job not found")
    project_id = uuid.UUID(str(row.project_id))
    try:
        require_member(orm, user_id=user_id, project_id=project_id)
        require_admin(orm, user_id=user_id, project_id=project_id)
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    if not cancel_parse_job(orm, job_id=job_id, project_id=project_id):
        raise HTTPException(status_code=409, detail="parse job is already terminal")


@router.post("/knowledge/material-parse-jobs/{job_id}/retry", response_model=ParseJobResponse)
def retry_material_parse_job(
    request: Request,
    job_id: uuid.UUID,
    orm: Session = Depends(get_orm_session),
) -> ParseJobResponse:
    """Requeue a failed parse job without creating a duplicate row."""
    user_id = _auth(request)
    row = orm.execute(
        text("""
            SELECT id, project_id, intake_file_id, status, attempt_count,
                   max_attempts, timeout_seconds, lease_expires_at,
                   next_attempt_at::text AS next_attempt_at, started_at, completed_at,
                   error_message, result_metadata
              FROM public.project_material_parse_jobs WHERE id = :id
        """),
        {"id": str(job_id)},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="parse job not found")
    project_id = uuid.UUID(str(row.project_id))
    try:
        require_admin(orm, user_id=user_id, project_id=project_id)
    except AuthzError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    if not retry_parse_job(orm, job_id=job_id, project_id=project_id):
        raise HTTPException(status_code=409, detail="parse job is not retryable")
    refreshed = orm.execute(
        text("""
            SELECT id, project_id, intake_file_id, status, attempt_count,
                   max_attempts, timeout_seconds, lease_expires_at,
                   next_attempt_at::text AS next_attempt_at, started_at, completed_at,
                   error_message, result_metadata
              FROM public.project_material_parse_jobs WHERE id = :id
        """),
        {"id": str(job_id)},
    ).first()
    if refreshed is None:
        raise HTTPException(status_code=503, detail="parse job disappeared after retry")
    return _response(refreshed)
