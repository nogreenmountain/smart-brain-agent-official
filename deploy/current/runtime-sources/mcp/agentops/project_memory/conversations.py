"""Explicit company-memory submissions, separate from gateway request capture."""
from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..rag.authz import AuthzError, require_writer

from ..project_wiki.domain import contains_prompt_injection, contains_sensitive_content


# Only a short visible request/final-answer summary belongs in this channel.
# Reject recognized envelopes rather than trying to extract hidden reasoning.
INTERNAL_CONTENT = re.compile(
    r'<\s*/?\s*(?:think(?:ing)?|analysis|reasoning|system|developer|tool(?:_call|_result)?)(?:\s|>)'
    r'|(?:role|channel)[\"\']?\s*[:=]\s*[\"\']?(?:analysis|commentary|tool|system|developer)\b'
    r'|<\|(?:im_start|im_end|start|end|channel|message|meta_sep)\|>'
    r'|(?:\[|【)\s*/?\s*(?:analysis|reasoning|thinking|commentary|system|developer|tool(?:_call|_result|\s+output)?|思考过程|推理过程|工具输出|内部上下文)\s*(?:\]|】)'
    r'|^\s*(?:#{1,6}\s*)?(?:analysis|reasoning|thinking|思考过程|推理过程|工具输出|内部上下文|system|developer|tool\s*(?:output|result))\s*(?:[:：]|$)'
    r'|^\s*(?:`{3,}|~{3,})', re.IGNORECASE | re.MULTILINE)


@dataclass(frozen=True)
class ConversationSubmission:
    submission_id: uuid.UUID
    title: str
    messages: list[dict[str, str]]
    task_result: str
    model: str
    model_source: str
    content_sha256: str


def _safe_text(value: object, field: str, limit: int, *, required: bool = True) -> str:
    if not isinstance(value, str):
        raise ValueError(f'{field} must be text')
    value = value.strip()
    if (required and not value) or len(value) > limit:
        raise ValueError(f'{field} has invalid length')
    if any(ord(c) < 32 and c not in '\n\r\t' for c in value):
        raise ValueError(f'{field} contains control characters')
    if contains_sensitive_content(value) or contains_prompt_injection(value):
        raise ValueError(f'{field} contains sensitive or unsafe content; redact before submitting')
    if INTERNAL_CONTENT.search(value):
        raise ValueError(f'{field} contains internal content; submit a concise visible request/final-answer summary')
    return value


def validate_submission(*, submission_id: str, title: str,
                        messages: list[dict[str, str]], task_result: str = '',
                        model: str | None = None) -> ConversationSubmission:
    try:
        sid = uuid.UUID(str(submission_id))
    except (ValueError, TypeError, AttributeError) as error:
        raise ValueError('submission_id must be a UUID') from error
    title = _safe_text(title, 'title', 120)
    task_result = _safe_text(task_result, 'task_result', 300, required=False)
    model = _safe_text(model, 'model', 200, required=False) if model is not None else ''
    model_source = 'client_declared' if model and model != 'unknown' else 'unknown'
    model = model or 'unknown'
    if not isinstance(messages, list) or not 1 <= len(messages) <= 2:
        raise ValueError('messages must contain 1 to 2 concise summary messages')
    cleaned = []
    for item in messages:
        if not isinstance(item, dict) or set(item) != {'role', 'content'}:
            raise ValueError('messages accept only role and content')
        if item['role'] not in ('user', 'assistant'):
            raise ValueError('message role must be user or assistant')
        limit = 300 if item['role'] == 'user' else 600
        cleaned.append({'role': item['role'], 'content': _safe_text(item['content'], 'message content', limit)})
    if len(cleaned) == 2 and [m['role'] for m in cleaned] != ['user', 'assistant']:
        raise ValueError('summary messages must be one user request followed by one assistant final result')
    payload = dict(title=title, messages=cleaned, task_result=task_result, model=model)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    if len(encoded) > 6000:
        raise ValueError('summary submission exceeds 6000 UTF-8 bytes')
    return ConversationSubmission(sid, title, cleaned, task_result, model, model_source,
                                  hashlib.sha256(encoded).hexdigest())


def _publish_wiki(orm, *, record, submission: ConversationSubmission) -> str:
    page_id = str(uuid.uuid4())
    # Fence each selected message; uploaded text is evidence, never instructions.
    import re
    def fenced(value):
        width = max([2] + [len(m.group()) for m in re.finditer(r'`+', value)]) + 1
        fence = '`' * width
        return f'{fence}text\n{value}\n{fence}'
    parts = ['# 项目对话摘要']
    labels = {'user': '用户请求', 'assistant': '最终结果'}
    parts.extend(f"## {labels[m['role']]}\n\n{fenced(m['content'])}" for m in submission.messages)
    if submission.task_result and submission.task_result not in [m['content'] for m in submission.messages]:
        parts.append('## 任务结果\n\n' + fenced(submission.task_result))
    # Attribution/model/provenance stay in canonical fields and source links;
    # the readable page contains only the brief task summary, without repeats.
    content = '\n\n'.join(parts)
    params = dict(id=page_id, pid=str(record['project_id']), uid=str(record['user_id']),
                  key=f"conversation-submission-{record['id']}", title=submission.title,
                  summary=submission.task_result[:1000], content=content, rid=str(record['id']))
    orm.execute(text('''INSERT INTO public.project_wiki_pages
        (id,project_id,page_key,title,page_type,status,summary,markdown_content,usefulness,
         confidence,current_version,created_by_user_id,memory_kind,verification_status)
        VALUES (:id,:pid,:key,:title,'note','active',:summary,:content,0,0,1,:uid,
                'conversation_record','generated')'''), params)
    orm.execute(text('''INSERT INTO public.project_wiki_page_versions
        (page_id,version,markdown_content,summary,source_ids,change_reason,created_by_user_id)
        VALUES (:id,1,:content,:summary,CAST(:sources AS jsonb),'authorized conversation submission',:uid)'''),
        params | {'sources': json.dumps([str(record['id'])])})
    orm.execute(text('''INSERT INTO public.project_wiki_page_sources(page_id,source_type,source_id)
        VALUES (:id,'project_conversation_record',:rid)'''), params)
    return page_id


def save_project_conversation(orm, *, user_id: uuid.UUID, project_id: uuid.UUID,
                              submission: ConversationSubmission) -> dict:
    """Save in the caller's transaction; no external calls or inferred model usage.

    Authenticated user_id must come from MCP identity, never from tool arguments.
    A savepoint lets a failed Wiki publication retain the canonical selected text.
    """
    user_id, project_id = uuid.UUID(str(user_id)), uuid.UUID(str(project_id))
    identity = orm.execute(text('''SELECT u.id,
            COALESCE(NULLIF(u.nickname,''),NULLIF(u.full_name,''),split_part(a.email,'@',1),u.id::text) AS name
        FROM public.users u JOIN auth.users a ON a.id=u.id
        WHERE u.id=:uid AND COALESCE(u.is_active,true) AND a.deleted_at IS NULL
          AND NOT COALESCE(a.is_anonymous,false)
          AND (a.banned_until IS NULL OR a.banned_until<=now()) FOR SHARE OF u,a'''),
        {'uid': str(user_id)}).first()
    if identity is None:
        raise AuthzError(403, 'member_unavailable')
    # Lock membership before checking writer access, so removal/demotion cannot
    # interleave with a write. The user lock also covers system-admin changes.
    orm.execute(text('''SELECT role FROM public.project_members
        WHERE project_id=:pid AND user_id=:uid FOR SHARE'''),
        {'pid': str(project_id), 'uid': str(user_id)}).first()
    require_writer(orm, user_id=user_id, project_id=project_id)
    project = orm.execute(text('SELECT id FROM public.projects WHERE id=:pid FOR KEY SHARE'),
                          {'pid': str(project_id)}).first()
    if project is None:
        raise AuthzError(404, 'project_not_found')
    params = dict(pid=str(project_id), uid=str(user_id), employee=str(user_id), name=str(identity.name),
        sid=str(submission.submission_id), hash=submission.content_sha256,
        # Internal reference required by the legacy schema, not a model request ID.
        ref=f'mcp:{user_id}:{submission.submission_id}', title=submission.title,
        result=submission.task_result, model=submission.model, model_source=submission.model_source,
        messages=json.dumps(submission.messages, ensure_ascii=False))
    inserted = orm.execute(text('''INSERT INTO public.project_conversation_records
        (project_id,user_id,employee_id,employee_name,request_id,record_source,submission_id,
         content_sha256,title,task_result,model,model_source,messages,token_status)
        VALUES (:pid,:uid,:employee,:name,:ref,'company_memory',:sid,:hash,:title,:result,
                :model,:model_source,CAST(:messages AS jsonb),'unknown')
        ON CONFLICT (project_id,request_id) DO NOTHING RETURNING id'''), params).first()
    record = orm.execute(text('''SELECT * FROM public.project_conversation_records
        WHERE project_id=:pid AND user_id=:uid AND request_id=:ref FOR UPDATE'''), params).mappings().one()
    if record['record_source'] != 'company_memory' or record['content_sha256'] != submission.content_sha256:
        raise ValueError('submission_id conflict: previously saved content differs')
    page_id = str(record['wiki_page_id']) if record['wiki_page_id'] else None
    status, error = record['wiki_status'], record['wiki_error']
    if status == 'published':
        page = orm.execute(text('''SELECT id FROM public.project_wiki_pages
            WHERE id=:id AND project_id=:pid AND status='active' FOR SHARE'''),
            {'id': page_id, 'pid': str(project_id)}).first() if page_id else None
        if page is None:
            status, error = 'failed', 'wiki_page_unavailable'
    if status != 'published':
        try:
            with orm.begin_nested():
                page_id = _publish_wiki(orm, record=record, submission=submission)
            status, error = 'published', None
        except SQLAlchemyError:
            page_id, status, error = None, 'failed', 'wiki_publish_failed'
        orm.execute(text('''UPDATE public.project_conversation_records
            SET wiki_status=:status,wiki_page_id=:page,wiki_error=:error,
                attempt_count=attempt_count+1,updated_at=now() WHERE id=:rid'''),
            {'status': status, 'page': page_id, 'error': error, 'rid': str(record['id'])})
        orm.execute(text('''INSERT INTO public.project_conversation_record_attempts
            (record_id,status,error_message) VALUES (:rid,:status,:error)'''),
            {'rid': str(record['id']), 'status': status, 'error': error})
    return dict(status='saved', record_id=str(record['id']), project_id=str(project_id),
        submission_id=str(submission.submission_id), duplicate=inserted is None,
        uploaded_by={'user_id': str(record['user_id']), 'name': record['employee_name']},
        uploaded_at=record['created_at'].isoformat(), record_source='company_memory',
        model=record['model'], model_source=record['model_source'], token_status='unknown',
        total_tokens=None, wiki_status=status, wiki_page_id=page_id, wiki_error=error)
