"""Daily evidence from persisted immutable projections, never guessed boundaries."""
from sqlalchemy import text
import uuid


def read_sources(orm, *, employee_id=None, work_date, owner_user_id=None):
    conditions=['s.work_date=:work_date'];params={'work_date':work_date}
    if employee_id is not None:
        conditions.append('s.employee_id=:employee_id');params['employee_id']=employee_id
    if owner_user_id is not None:
        conditions.append('s.user_id=CAST(:owner_user_id AS uuid)')
        params['owner_user_id']=str(uuid.UUID(str(owner_user_id)))
    elif employee_id is None:
        raise ValueError('daily source requires owner UUID or explicit legacy scope')
    # One SQL statement provides the head, source and dirty state from one MVCC snapshot.
    rows=orm.execute(text(f'''SELECT s.request_id,s.event_payload,h.revision_id,r.projection,
        EXISTS(SELECT 1 FROM public.ai_gateway_delta_pending_sources pending
               WHERE pending.scope_key=s.scope_key AND pending.processed_at IS NULL) AS scope_dirty
        FROM public.ai_gateway_personal_delta_sources s
        LEFT JOIN public.ai_gateway_delta_heads h ON h.request_id=s.request_id
        LEFT JOIN public.ai_gateway_delta_revisions r ON r.id=h.revision_id AND r.request_id=s.request_id
        WHERE {' AND '.join(conditions)} ORDER BY s.admitted_at,s.request_id'''),params).all()
    records=[]
    for row in rows:
        if row.scope_dirty or row.revision_id is None:
            raise ValueError('personal source projection is pending; daily report must retry')
        records.append(dict(session_id=str(row.request_id),revision_id=str(row.revision_id),
            source='ai_gateway_project' if row.event_payload.get('project_id') else 'ai_gateway_personal',
            title=row.event_payload.get('title') or ('项目 AI 请求' if row.event_payload.get('project_id') else '个人 AI 请求'),
            messages=project_messages(row.event_payload,row.projection)))
    return records


def project_messages(payload, projection):
    status=projection['status']
    if status not in ('exact_prefix','unattributed_context','independent_request'):
        raise ValueError('unresolved personal source requires audit before daily consumption')
    responses=set(projection['response_indices'])
    results=set(projection['reported_tool_result_indices'])
    calls=set(projection['tool_call_indices'])
    unknown=set(projection['unknown_tool_indices'])
    records=[]
    for index in projection['retained_input_indices']+projection['response_indices']:
        message=payload['messages'][index]
        if index not in responses and status!='exact_prefix':
            evidence='context'
        elif index in calls:
            evidence='tool_call'
        elif index in unknown:
            evidence='unknown_tool'
        elif index in results:
            evidence='reported_tool_result'
        elif index in responses:
            evidence='model_response'
        else:
            evidence='context'
        records.append(dict(role=message['role'],content=message['content'],evidence_kind=evidence))
    return records
