"""Read personal immutable request snapshots, without another content/token copy.

This supplies request-level provenance. It does not claim that repeated context
across separate requests has been deduplicated into conversation deltas.
"""
import json
import uuid

try:
    from sqlalchemy import text
except ModuleNotFoundError:
    def text(value): return value


def read_personal_sources(orm, *, end_utc, start_utc=None, employee_id=None,
                          unprocessed=False, limit=None, owner_user_id=None):
    conditions = []
    params = {'end_utc': end_utc}
    observed = 'COALESCE(e.completed_at,e.started_at,a.admitted_at)'
    if owner_user_id is not None:
        conditions.append('a.user_id=CAST(:owner_user_id AS uuid)')
        params['owner_user_id']=str(uuid.UUID(str(owner_user_id)))
    if start_utc is not None:
        conditions.append(observed + ' >= :start_utc'); params['start_utc'] = start_utc
    if employee_id is not None:
        conditions.append('e.employee_id=:employee_id'); params['employee_id'] = employee_id
    if unprocessed:
        conditions.append('NOT EXISTS (SELECT 1 FROM public.member_wiki_processed_gateway_requests p WHERE p.request_id=a.id)')
    tail = ''
    if limit is not None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ValueError('Source limit must be a positive integer')
        tail = 'LIMIT :limit'; params['limit'] = limit
    extra = ''.join(' AND ' + value for value in conditions)
    rows = orm.execute(text(f'''
        SELECT a.id::text AS request_id,a.event_payload,e.employee_id,e.employee_name,
               {observed} AS observed_at
        FROM public.ai_gateway_admissions a
        JOIN public.ai_gateway_events e
          ON e.event_id=a.id::text AND e.gateway_instance_id=a.gateway_instance_id AND e.user_id=a.user_id
        WHERE a.delivered_at IS NOT NULL AND a.event_sha256 IS NOT NULL
          AND a.event_payload->'content_complete'='true'::jsonb
          AND a.event_payload->>'project_id' IS NULL AND e.chat_session_id IS NULL
          AND e.status_code>=200 AND e.status_code<400
          AND jsonb_array_length(a.event_payload->'messages')>0
          AND {observed}<:end_utc {extra}
        ORDER BY {observed},a.admitted_at,a.id {tail}
    '''), params).all()
    result = []
    for row in rows:
        payload = json.loads(row.event_payload) if isinstance(row.event_payload, str) else row.event_payload
        result.append(dict(session_id=str(row.request_id), employee_id=str(row.employee_id),
            employee_name=str(row.employee_name or row.employee_id), title=payload.get('title') or '个人 AI 请求',
            source='ai_gateway_personal', task_id=payload.get('task_id') or 'unassigned',
            task_title=payload.get('task_title') or payload.get('title') or '个人 AI 请求',
            model=payload.get('resolved_model') or payload.get('model') or 'unknown',
            trace_id=payload.get('trace_id'), started_at=row.observed_at, messages=payload['messages']))
    return result
