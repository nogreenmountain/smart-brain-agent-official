"""Authenticated project instructions, approval details and personal reporting."""
from datetime import date, datetime
import hashlib
import json
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.auth.middleware import AuthenticatedRoute
from agentops.common.orm import get_orm_session
from agentops.rag.authz import AuthzError, current_user_id, require_admin, require_member
from agentops.project_collaboration import SHANGHAI, day_bounds, render_agents, validate_agents


def private(response: Response):
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(prefix='/project-collaboration', route_class=AuthenticatedRoute,
                   dependencies=[Depends(private)])


def user(request):
    try:
        return current_user_id(request)
    except AuthzError as error:
        raise HTTPException(error.status_code, error.detail) from error


def access(orm, uid, pid, write=False):
    try:
        return (require_admin if write else require_member)(orm, user_id=uid, project_id=pid)
    except AuthzError as error:
        raise HTTPException(error.status_code, error.detail) from error


def reviewer(orm, uid):
    row = orm.execute(text("""
        SELECT au.id FROM auth.users au JOIN public.users pu ON pu.id=au.id
        WHERE au.id=:uid AND lower(au.email)='hanshangbo@local.dev'
          AND COALESCE(pu.is_active,true) AND au.deleted_at IS NULL
          AND (au.banned_until IS NULL OR au.banned_until<=now())
    """), {'uid': str(uid)}).first()
    if row is None:
        raise HTTPException(403, '仅 hanshangbo 可以查看和审批额外 Key 申请')


def agents_row(orm, pid):
    row = orm.execute(text('''
        SELECT content,version,updated_at,updated_by_user_id
        FROM public.project_agents_files WHERE project_id=:pid
    '''), {'pid': str(pid)}).first()
    if row is None:
        return {'exists': False, 'version': 0, 'content': ''}
    return {'exists': True, 'content': row.content, 'version': row.version,
            'updated_at': row.updated_at, 'updated_by_user_id': row.updated_by_user_id,
            'sha256': hashlib.sha256(row.content.encode('utf-8')).hexdigest()}


@router.get('/projects/{project_id}/agents')
def get_agents(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    access(orm, user(request), project_id)
    return agents_row(orm, project_id)


@router.post('/projects/{project_id}/agents/initialize')
def initialize_agents(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    uid = user(request)
    access(orm, uid, project_id, True)
    project = orm.execute(text('SELECT name FROM public.projects WHERE id=:pid'), {'pid': str(project_id)}).first()
    if project is None:
        raise HTTPException(404, '项目不存在')
    orm.execute(text('''
        INSERT INTO public.project_agents_files(project_id,content,updated_by_user_id)
        VALUES(:pid,:content,:uid) ON CONFLICT(project_id) DO NOTHING
    '''), {'pid': str(project_id), 'uid': str(uid), 'content': render_agents(project.name, str(project_id))})
    orm.commit()
    return agents_row(orm, project_id)


class AgentsUpload(BaseModel):
    filename: str = Field(max_length=200)
    content: str = Field(max_length=65536)
    expected_version: int = Field(ge=0)


@router.put('/projects/{project_id}/agents')
def upload_agents(project_id: uuid.UUID, body: AgentsUpload, request: Request,
                  orm: Session = Depends(get_orm_session)):
    uid = user(request)
    access(orm, uid, project_id, True)
    try:
        content = validate_agents(body.filename, body.content.encode('utf-8'))
    except (ValueError, UnicodeError) as error:
        raise HTTPException(422, str(error)) from error
    # Lock the project, including the initial empty-file case.
    project = orm.execute(text('SELECT id FROM public.projects WHERE id=:pid FOR UPDATE'), {'pid': str(project_id)}).first()
    if project is None:
        raise HTTPException(404, '项目不存在')
    current = agents_row(orm, project_id)
    if current['version'] != body.expected_version:
        raise HTTPException(409, 'AGENTS.md 已由其他人更新，请刷新后重新核对')
    orm.execute(text('''
        INSERT INTO public.project_agents_files(project_id,content,updated_by_user_id)
        VALUES(:pid,:content,:uid)
        ON CONFLICT(project_id) DO UPDATE SET content=EXCLUDED.content,
          version=project_agents_files.version+1,updated_by_user_id=EXCLUDED.updated_by_user_id,updated_at=now()
    '''), {'pid': str(project_id), 'content': content, 'uid': str(uid)})
    orm.commit()
    return agents_row(orm, project_id)


@router.get('/projects/{project_id}/agents/download')
def download_agents(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    access(orm, user(request), project_id)
    row = agents_row(orm, project_id)
    if not row['exists']:
        raise HTTPException(404, '请先由项目负责人初始化 AGENTS.md')
    return Response(row['content'].encode('utf-8'), media_type='text/markdown; charset=utf-8',
                    headers={'Content-Disposition': 'attachment; filename="AGENTS.md"', 'Cache-Control': 'no-store'})


class KeyRequest(BaseModel):
    requested_limit: int = Field(ge=2, le=100)
    reason: str = Field(min_length=1, max_length=2000)

    @field_validator('reason')
    @classmethod
    def clean_reason(cls, value):
        if not value.strip():
            raise ValueError('请填写申请原因')
        return value.strip()


class Review(BaseModel):
    decision: Literal['approve', 'reject']
    comment: str = Field(default='', max_length=2000)


def key_status(orm, uid):
    row = orm.execute(text('''
        SELECT COALESCE((SELECT max_active_keys FROM public.ai_gateway_key_allowances WHERE user_id=:uid),1) AS allowed,
          (SELECT count(*) FROM public.ai_gateway_keys WHERE user_id=:uid AND is_active) AS active
    '''), {'uid': str(uid)}).first()
    return {'allowed': int(row.allowed), 'active': int(row.active)}


@router.get('/key-requests/mine')
def my_key_requests(request: Request, orm: Session = Depends(get_orm_session)):
    uid = user(request)
    rows = orm.execute(text('''
        SELECT id,requested_limit,reason,status,review_comment,created_at,reviewed_at
        FROM public.ai_gateway_key_requests WHERE user_id=:uid ORDER BY created_at DESC LIMIT 30
    '''), {'uid': str(uid)}).all()
    return {**key_status(orm, uid), 'requests': [dict(row._mapping) for row in rows]}


@router.post('/key-requests')
def submit_key_request(body: KeyRequest, request: Request, orm: Session = Depends(get_orm_session)):
    uid = user(request)
    if orm.execute(text('SELECT id FROM public.users WHERE id=:uid FOR UPDATE'), {'uid': str(uid)}).first() is None:
        raise HTTPException(404, '账号不存在')
    status = key_status(orm, uid)
    if body.requested_limit <= max(status['allowed'], status['active']):
        raise HTTPException(422, '申请总名额必须大于当前名额和已有活动 Key 数量')
    if orm.execute(text("SELECT id FROM public.ai_gateway_key_requests WHERE user_id=:uid AND status='pending'"), {'uid': str(uid)}).first():
        raise HTTPException(409, '已有待审批申请，请等待处理')
    target = orm.execute(text("""
        SELECT au.id FROM auth.users au JOIN public.users pu ON pu.id=au.id
        WHERE lower(au.email)='hanshangbo@local.dev' AND COALESCE(pu.is_active,true)
          AND au.deleted_at IS NULL AND (au.banned_until IS NULL OR au.banned_until<=now())
    """)).first()
    if target is None:
        raise HTTPException(503, '指定审批账号暂不可用，请稍后再试')
    row = orm.execute(text('''
        INSERT INTO public.ai_gateway_key_requests(user_id,reviewer_id,requested_limit,reason)
        VALUES(:uid,:reviewer,:limit,:reason) RETURNING id,status
    '''), {'uid': str(uid), 'reviewer': str(target.id), 'limit': body.requested_limit, 'reason': body.reason}).first()
    orm.commit()
    return dict(row._mapping)


@router.get('/key-requests/pending')
def pending_key_requests(request: Request, orm: Session = Depends(get_orm_session)):
    uid = user(request)
    reviewer(orm, uid)
    rows = orm.execute(text('''
        SELECT r.id,r.user_id,r.requested_limit,r.reason,r.created_at,
          split_part(au.email,'@',1) AS username,
          COALESCE(NULLIF(pu.nickname,''),split_part(au.email,'@',1)) AS display_name,
          COALESCE(a.max_active_keys,1) AS current_limit,
          (SELECT count(*) FROM public.ai_gateway_keys k WHERE k.user_id=r.user_id AND k.is_active) AS active_keys
        FROM public.ai_gateway_key_requests r JOIN auth.users au ON au.id=r.user_id
        JOIN public.users pu ON pu.id=r.user_id LEFT JOIN public.ai_gateway_key_allowances a ON a.user_id=r.user_id
        WHERE r.status='pending' AND r.reviewer_id=:uid ORDER BY r.created_at,r.id
    '''), {'uid': str(uid)}).all()
    return [dict(row._mapping) for row in rows]


@router.post('/key-requests/{request_id}/review')
def review_key_request(request_id: uuid.UUID, body: Review, request: Request, orm: Session = Depends(get_orm_session)):
    uid = user(request)
    reviewer(orm, uid)
    # Lock requester before request to match key creation/submission lock order.
    candidate = orm.execute(text('SELECT user_id FROM public.ai_gateway_key_requests WHERE id=:id AND reviewer_id=:uid'),
                            {'id': str(request_id), 'uid': str(uid)}).first()
    if candidate is None:
        raise HTTPException(404, '申请不存在')
    orm.execute(text('SELECT id FROM public.users WHERE id=:uid FOR UPDATE'), {'uid': str(candidate.user_id)}).first()
    row = orm.execute(text('SELECT user_id,status,requested_limit FROM public.ai_gateway_key_requests WHERE id=:id FOR UPDATE'),
                      {'id': str(request_id)}).first()
    if row.status != 'pending':
        raise HTTPException(409, '申请已经处理，请刷新列表')
    if body.decision == 'approve':
        orm.execute(text('''
            INSERT INTO public.ai_gateway_key_allowances(user_id,max_active_keys) VALUES(:uid,:limit)
            ON CONFLICT(user_id) DO UPDATE SET max_active_keys=GREATEST(ai_gateway_key_allowances.max_active_keys,EXCLUDED.max_active_keys),updated_at=now()
        '''), {'uid': str(row.user_id), 'limit': row.requested_limit})
    final = 'approved' if body.decision == 'approve' else 'rejected'
    orm.execute(text('''
        UPDATE public.ai_gateway_key_requests SET status=:status,review_comment=:comment,
          reviewed_at=now(),reviewed_by_user_id=:uid WHERE id=:id
    '''), {'id': str(request_id), 'uid': str(uid), 'status': final, 'comment': body.comment})
    orm.commit()
    return {'id': str(request_id), 'status': final}


@router.get('/activity')
def personal_activity(request: Request, day: date | None = None, orm: Session = Depends(get_orm_session)):
    uid = user(request)
    day = day or datetime.now(SHANGHAI).date()
    start, end = day_bounds(day)
    params = {'uid': str(uid), 'start': start, 'end': end}
    counts = orm.execute(text('''
        SELECT
          (SELECT count(*) FROM public.ai_gateway_events e
           WHERE e.user_id=:uid AND COALESCE(e.started_at,e.created_at)>=:start AND COALESCE(e.started_at,e.created_at)<:end) AS gateway_requests,
          (SELECT count(*) FROM public.ai_chat_messages m JOIN public.ai_chat_sessions s ON s.id=m.session_id
           WHERE s.user_id=:uid AND m.role='user' AND s.source<>'ai_gateway'
             AND s.gateway_event_id IS NULL
             AND COALESCE(m.message_created_at,m.created_at)>=:start AND COALESCE(m.message_created_at,m.created_at)<:end) AS other_messages
    '''), params).first()
    rows = orm.execute(text('''
        SELECT p.id AS project_id,p.name AS project_name,count(*) AS upload_count,
          count(DISTINCT v.page_id) AS page_count
        FROM public.project_wiki_page_versions v JOIN public.project_wiki_pages ppage ON ppage.id=v.page_id
        JOIN public.projects p ON p.id=ppage.project_id
        WHERE v.created_by_user_id=:uid AND v.change_reason='mcp_direct_publish'
          AND v.created_at>=:start AND v.created_at<:end
        GROUP BY p.id,p.name ORDER BY upload_count DESC,p.name,p.id
    '''), params).all()
    projects = [dict(row._mapping) for row in rows]
    return {'date': day.isoformat(), 'timezone': 'Asia/Shanghai',
            'conversation_count': int(counts.gateway_requests + counts.other_messages),
            'gateway_requests': int(counts.gateway_requests), 'other_messages': int(counts.other_messages),
            'wiki_upload_count': sum(int(row['upload_count']) for row in projects), 'projects': projects,
            'definition': '对话按网关请求及其他渠道用户消息计数，排除网关会话副本。Wiki 按 Company Memory 成功发布次数统计（含更新），不含待审、失败或自动编译。未接入的对话无法统计。'}


@router.get('/projects/{project_id}/wiki-contributions')
def wiki_contributions(project_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    access(orm, user(request), project_id)
    rows = orm.execute(text('''
        WITH uploads AS (
          SELECT v.created_by_user_id AS user_id,count(*) AS upload_count
          FROM public.project_wiki_page_versions v JOIN public.project_wiki_pages p ON p.id=v.page_id
          WHERE p.project_id=:pid AND v.change_reason='mcp_direct_publish' GROUP BY v.created_by_user_id
        ), members AS (
          SELECT user_id FROM public.project_members WHERE project_id=:pid
          UNION SELECT user_id FROM uploads
        )
        SELECT m.user_id,COALESCE(NULLIF(pu.nickname,''),split_part(au.email,'@',1),'未归属成员') AS display_name,
          COALESCE(u.upload_count,0) AS upload_count
        FROM members m LEFT JOIN uploads u ON u.user_id IS NOT DISTINCT FROM m.user_id
        LEFT JOIN public.users pu ON pu.id=m.user_id LEFT JOIN auth.users au ON au.id=m.user_id
        ORDER BY upload_count DESC,display_name,m.user_id
    '''), {'pid': str(project_id)}).all()
    members = [dict(row._mapping) for row in rows]
    return {'project_id': str(project_id), 'total': sum(int(row['upload_count']) for row in members), 'members': members}


def review_draft(orm, uid, draft_id):
    row = orm.execute(text('''
        SELECT id,project_id,intake_id,submission_id,markdown_content FROM public.project_memory_drafts WHERE id=:id
    '''), {'id': str(draft_id)}).first()
    if row is None:
        raise HTTPException(404, '审批内容不存在')
    access(orm, uid, row.project_id, True)
    return row


@router.get('/reviews/{draft_id}')
def review_detail(draft_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    row = review_draft(orm, user(request), draft_id)
    files = orm.execute(text('''
        SELECT id,filename,relative_path,size_bytes,format,included FROM public.project_material_intake_files
        WHERE intake_id=:id ORDER BY created_at,id
    '''), {'id': str(row.intake_id) if row.intake_id else None}).all()
    submission = None
    if row.submission_id:
        item = orm.execute(text('SELECT submission_type,payload,filename FROM public.project_memory_submissions WHERE id=:id'),
                           {'id': str(row.submission_id)}).first()
        if item:
            submission = dict(item._mapping)
    return {'draft_id': str(draft_id), 'markdown_content': row.markdown_content,
            'intake_id': row.intake_id, 'files': [dict(item._mapping) for item in files], 'submission': submission}


@router.get('/reviews/{draft_id}/files/{file_id}')
def review_file(draft_id: uuid.UUID, file_id: uuid.UUID, request: Request, orm: Session = Depends(get_orm_session)):
    draft = review_draft(orm, user(request), draft_id)
    row = orm.execute(text('''
        SELECT filename,extracted_text,storage_key,raw_content,size_bytes
        FROM public.project_material_intake_files WHERE id=:id AND intake_id=:intake
    '''), {'id': str(file_id), 'intake': str(draft.intake_id) if draft.intake_id else None}).first()
    if row is None:
        raise HTTPException(404, '文件不属于此审批')
    preview = row.extracted_text or ''
    note = ''
    if not preview and row.size_bytes <= 20 * 1024 * 1024:
        import subprocess, sys, tempfile
        from pathlib import Path
        from agentops.project_memory.storage import resolve_storage_key
        # Reuse bounded document parsers in a child process so preview cannot stall the API.
        try:
            with tempfile.TemporaryDirectory() as directory:
                if row.storage_key:
                    source = resolve_storage_key(row.storage_key)
                else:
                    source = Path(directory) / ('preview' + Path(row.filename).suffix)
                    source.write_bytes(bytes(row.raw_content or b''))
                code = 'from pathlib import Path; from agentops.project_memory.parsers import extract_text; import sys; print(extract_text(Path(sys.argv[1])).text[:131073])'
                result = subprocess.run([sys.executable, '-c', code, str(source)], capture_output=True, timeout=15)
                if result.returncode == 0:
                    preview = result.stdout.decode('utf-8', errors='replace')
        except (OSError, ValueError, subprocess.TimeoutExpired):
            note = '在线预览暂不可用，请下载原文件查看完整内容。'
    if not preview:
        note = note or '此文件暂无法生成文本预览，请下载原文件查看具体内容。'
    return {'filename': row.filename, 'content': preview[:131072], 'truncated': len(preview)>131072, 'note': note}
