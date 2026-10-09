"""Project AGENTS.md, project-context, and project usage endpoints."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.auth.middleware import AuthenticatedRoute
from agentops.common.orm import get_orm_session
from agentops.rag.authz import AuthzError, current_user_id, is_system_admin, require_admin, require_member


AGENTS_FILENAME = "AGENTS.md"
AGENTS_TEMPLATE_VERSION = 1
# Keep the upload limit compatible with the first production AGENTS schema;
# larger templates can be introduced later with an explicit migration.
AGENTS_MAX_BYTES = 64 * 1024
CONTEXT_TTL = timedelta(hours=8)
DOWNLOAD_NOTICE = "请下载到对应项目文件夹，若没有项目文件夹，请新建并添加。"

router = APIRouter(route_class=AuthenticatedRoute)


class ContextResponse(BaseModel):
    project_id: uuid.UUID
    agents_version: int
    agents_sha256: str
    token: str
    expires_at: datetime


class AgentsResponse(BaseModel):
    project_id: uuid.UUID
    filename: str
    content: str
    version: int
    sha256: str
    updated_by: uuid.UUID | None = None
    updated_at: datetime | None = None


class WikiUploadStatsMember(BaseModel):
    user_id: uuid.UUID
    display_name: str
    count: int
    ratio: float


class WikiUploadStatsResponse(BaseModel):
    project_id: uuid.UUID
    total: int
    members: list[WikiUploadStatsMember]


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def validate_agents_filename(filename: str | None) -> bool:
    return filename == AGENTS_FILENAME


def build_default_agents(*, project_id: uuid.UUID, project_name: str) -> str:
    # Project names are content only; callers must never execute them as code.
    safe_name = project_name.replace("\r", " ").replace("\n", " ").strip()
    return (
        f"# {safe_name} 项目协作规则\n\n"
        f"<!-- smartbrain-project-id: {project_id} -->\n"
        f"<!-- smartbrain-agents-version: {AGENTS_TEMPLATE_VERSION} -->\n"
        "<!-- smartbrain-agents-sha256: generated-on-save -->\n\n"
        "让 AI 理解项目规则，与智慧大脑高效协作。\n\n"
        f"每条对话完成后，请使用 company memory 插件，将以下对话直接记录到「{safe_name}」项目的知识库“对话记录”中，并明确标注：\n\n"
        "- 上传成员名称\n"
        "- 上传时间\n"
        "- 使用模型\n"
        "- SmartBrain request_id\n"
        "- 本次任务完成内容\n"
    )


def _user_id(request: Request) -> uuid.UUID:
    try:
        return current_user_id(request)
    except AuthzError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def _project(orm: Session, project_id: uuid.UUID):
    row = orm.execute(
        text("SELECT id::text AS id, name FROM public.projects WHERE id=:pid"),
        {"pid": str(project_id)},
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="project not found")
    return row


def _agents_row(orm: Session, project_id: uuid.UUID):
    return orm.execute(
        text("""
            SELECT project_id::text AS project_id, filename, content, version,
                   sha256, updated_by::text AS updated_by, updated_at
            FROM public.project_agents_files
            WHERE project_id=:pid
        """),
        {"pid": str(project_id)},
    ).first()


def _agents_response(row) -> AgentsResponse:
    return AgentsResponse(
        project_id=uuid.UUID(str(row.project_id)),
        filename=str(row.filename),
        content=str(row.content),
        version=int(row.version),
        sha256=str(row.sha256),
        updated_by=uuid.UUID(str(row.updated_by)) if row.updated_by else None,
        updated_at=row.updated_at,
    )


def initialize_agents(orm: Session, *, project_id: uuid.UUID, project_name: str, user_id: uuid.UUID | None = None):
    content = build_default_agents(project_id=project_id, project_name=project_name)
    digest = sha256_text(content)
    orm.execute(text("""
        INSERT INTO public.project_agents_files
            (project_id, filename, content, version, sha256, updated_by)
        VALUES (:pid, :filename, :content, :version, :sha256, :updated_by)
        ON CONFLICT (project_id) DO NOTHING
    """), {
        "pid": str(project_id), "filename": AGENTS_FILENAME, "content": content,
        "version": AGENTS_TEMPLATE_VERSION, "sha256": digest,
        "updated_by": str(user_id) if user_id else None,
    })
    row = _agents_row(orm, project_id)
    if row is None:
        raise HTTPException(status_code=500, detail="AGENTS.md initialization failed")
    return row


def _require_member_or_http(orm: Session, *, user_id: uuid.UUID, project_id: uuid.UUID):
    try:
        return require_member(orm, user_id=user_id, project_id=project_id)
    except AuthzError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


def _require_admin_or_http(orm: Session, *, user_id: uuid.UUID, project_id: uuid.UUID):
    try:
        return require_admin(orm, user_id=user_id, project_id=project_id)
    except AuthzError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/projects/{project_id}/agents", response_model=AgentsResponse)
def get_agents(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    user_id = _user_id(request)
    _require_member_or_http(orm, user_id=user_id, project_id=project_id)
    project = _project(orm, project_id)
    row = _agents_row(orm, project_id) or initialize_agents(
        orm, project_id=project_id, project_name=str(project.name)
    )
    orm.commit()
    return _agents_response(row)


@router.post("/projects/{project_id}/agents/initialize", response_model=AgentsResponse)
def initialize_agents_endpoint(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    user_id = _user_id(request)
    _require_admin_or_http(orm, user_id=user_id, project_id=project_id)
    project = _project(orm, project_id)
    row = initialize_agents(orm, project_id=project_id, project_name=str(project.name), user_id=user_id)
    orm.commit()
    return _agents_response(row)


@router.post("/projects/{project_id}/agents/upload", response_model=AgentsResponse)
async def upload_agents(
    project_id: uuid.UUID,
    request: Request,
    body: bytes = Body(..., media_type="text/markdown"),
    filename: str | None = Header(None, alias="X-File-Name"),
    orm: Session = Depends(get_orm_session),
):
    user_id = _user_id(request)
    _require_admin_or_http(orm, user_id=user_id, project_id=project_id)
    if not validate_agents_filename(filename):
        raise HTTPException(status_code=400, detail="文件名必须严格为 AGENTS.md")
    raw = body[:AGENTS_MAX_BYTES + 1]
    if len(raw) > AGENTS_MAX_BYTES:
        raise HTTPException(status_code=413, detail="AGENTS.md 文件过大")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="AGENTS.md 必须使用 UTF-8 编码") from exc
    current = orm.execute(
        text("SELECT version FROM public.project_agents_files WHERE project_id=:pid FOR UPDATE"),
        {"pid": str(project_id)},
    ).first()
    version = int(current.version) + 1 if current else 1
    orm.execute(text("""
        INSERT INTO public.project_agents_file_versions
            (project_id, filename, content, version, sha256, updated_by)
        VALUES (:pid, :filename, :content, :version, :sha256, :updated_by)
    """), {
        "pid": str(project_id), "filename": AGENTS_FILENAME, "content": content,
        "version": version, "sha256": sha256_text(content), "updated_by": str(user_id),
    })
    orm.execute(text("""
        INSERT INTO public.project_agents_files
            (project_id, filename, content, version, sha256, updated_by)
        VALUES (:pid, :filename, :content, :version, :sha256, :updated_by)
        ON CONFLICT (project_id) DO UPDATE SET
            filename=EXCLUDED.filename, content=EXCLUDED.content,
            version=EXCLUDED.version, sha256=EXCLUDED.sha256,
            updated_by=EXCLUDED.updated_by, updated_at=now()
    """), {
        "pid": str(project_id), "filename": AGENTS_FILENAME, "content": content,
        "version": version, "sha256": sha256_text(content), "updated_by": str(user_id),
    })
    orm.commit()
    return _agents_response(_agents_row(orm, project_id))


@router.get("/projects/{project_id}/agents/download")
def download_agents(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    user_id = _user_id(request)
    _require_member_or_http(orm, user_id=user_id, project_id=project_id)
    row = _agents_row(orm, project_id)
    if row is None:
        project = _project(orm, project_id)
        row = initialize_agents(orm, project_id=project_id, project_name=str(project.name))
        orm.commit()
    return Response(
        content=str(row.content).encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="AGENTS.md"',
            "X-SmartBrain-Download-Notice": DOWNLOAD_NOTICE,
        },
    )


def issue_project_context(
    orm: Session,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    key_id: uuid.UUID | None = None,
) -> ContextResponse:
    _require_member_or_http(orm, user_id=user_id, project_id=project_id)
    if key_id is not None:
        key = orm.execute(
            text("SELECT id FROM public.ai_gateway_keys WHERE id=:kid AND user_id=:uid AND is_active"),
            {"kid": str(key_id), "uid": str(user_id)},
        ).first()
        if key is None:
            raise HTTPException(status_code=404, detail="active API Key not found")
    row = _agents_row(orm, project_id)
    if row is None:
        project = _project(orm, project_id)
        row = initialize_agents(orm, project_id=project_id, project_name=str(project.name), user_id=user_id)
    raw = "sbc_" + secrets.token_urlsafe(36)
    expires = datetime.now(timezone.utc) + CONTEXT_TTL
    orm.execute(text("""
        INSERT INTO public.project_context_tokens
            (user_id, key_id, project_id, agents_version, agents_sha256, token_hash, expires_at)
        VALUES (:uid, :kid, :pid, :version, :sha256, :hash, :expires)
    """), {
        "uid": str(user_id), "kid": str(key_id) if key_id else None,
        "pid": str(project_id), "version": int(row.version), "sha256": str(row.sha256),
        "hash": sha256_text(raw), "expires": expires,
    })
    return ContextResponse(
        project_id=project_id, agents_version=int(row.version), agents_sha256=str(row.sha256),
        token=raw, expires_at=expires,
    )


@router.post("/projects/{project_id}/context", response_model=ContextResponse)
def create_project_context(
    project_id: uuid.UUID,
    request: Request,
    key_id: uuid.UUID | None = Query(None),
    orm: Session = Depends(get_orm_session),
):
    result = issue_project_context(orm, user_id=_user_id(request), project_id=project_id, key_id=key_id)
    orm.commit()
    return result


def resolve_gateway_project_context(
    orm: Session,
    *,
    user_id: uuid.UUID,
    key_id: uuid.UUID,
    token: str | None,
) -> uuid.UUID | None:
    """Validate a context header without trusting a client project id."""
    require_context = os.getenv("SB_GATEWAY_REQUIRE_PROJECT_CONTEXT", "false").lower() in {"1", "true", "yes", "on"}
    if not token:
        if require_context:
            raise HTTPException(status_code=428, detail="project_context_required")
        return None
    row = orm.execute(text("""
        SELECT project_id::text AS project_id, agents_version, agents_sha256
        FROM public.project_context_tokens
        WHERE user_id=:uid AND (key_id IS NULL OR key_id=:kid)
          AND token_hash=:hash AND revoked_at IS NULL AND expires_at > now()
    """), {"uid": str(user_id), "kid": str(key_id), "hash": sha256_text(token)}).first()
    if row is None:
        if require_context:
            raise HTTPException(status_code=428, detail="invalid_project_context")
        return None
    current = _agents_row(orm, uuid.UUID(str(row.project_id)))
    if current is None or int(current.version) != int(row.agents_version) or not hmac.compare_digest(str(current.sha256), str(row.agents_sha256)):
        if require_context:
            raise HTTPException(status_code=428, detail="stale_project_context")
        return None
    return uuid.UUID(str(row.project_id))


@router.get("/projects/{project_id}/wiki-upload-stats", response_model=WikiUploadStatsResponse)
def wiki_upload_stats(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    user_id = _user_id(request)
    _require_member_or_http(orm, user_id=user_id, project_id=project_id)
    rows = orm.execute(text("""
        SELECT r.user_id::text AS user_id,
               COALESCE(NULLIF(u.full_name, ''), split_part(au.email, '@', 1)) AS display_name,
               count(*)::int AS count
        FROM public.project_conversation_records r
        JOIN auth.users au ON au.id=r.user_id
        LEFT JOIN public.users u ON u.id=r.user_id
        WHERE r.project_id=:pid AND r.wiki_status='published'
        GROUP BY r.user_id, u.full_name, au.email
        ORDER BY count(*) DESC, display_name
    """), {"pid": str(project_id)}).all()
    total = sum(int(row.count) for row in rows)
    members = [WikiUploadStatsMember(
        user_id=uuid.UUID(str(row.user_id)), display_name=str(row.display_name),
        count=int(row.count), ratio=(int(row.count) / total if total else 0),
    ) for row in rows]
    return WikiUploadStatsResponse(project_id=project_id, total=total, members=members)
