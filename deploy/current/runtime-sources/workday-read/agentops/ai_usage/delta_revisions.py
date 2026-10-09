"""Append-only derived versions and independent consumer receipts.

All helpers participate in the caller's transaction. The coordinator must hold
the complete conversation scope lock before deriving and moving a head.
"""
import json
import uuid
import importlib.util
from pathlib import Path
from sqlalchemy import text


def _planner():
    try:
        from agentops.ai_usage import message_deltas
        return message_deltas
    except ModuleNotFoundError:
        spec=importlib.util.spec_from_file_location('delta_revision_planner',Path(__file__).with_name('message_deltas.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module


def persist_projections(orm, sources, projections):
    identities = {}
    for source in sources:
        request_id = source['request_id']
        projection = projections[request_id]
        params = dict(request_id=request_id, employee_id=source.get('employee_id',source['member_id']), work_date=source['work_date'],
            revision_sha256=projection['revision_sha256'], source_sha256=projection['source_sha256'],
            projection=json.dumps(projection,ensure_ascii=False,sort_keys=True,separators=(',',':')))
        revision_id = orm.execute(text('''INSERT INTO public.ai_gateway_delta_revisions
            (request_id,employee_id,work_date,revision_sha256,source_sha256,projection)
            VALUES (:request_id,:employee_id,:work_date,:revision_sha256,:source_sha256,CAST(:projection AS jsonb))
            ON CONFLICT(request_id,revision_sha256) DO NOTHING RETURNING id'''),params).scalar_one_or_none()
        if revision_id is None:
            revision_id = orm.execute(text('''SELECT id FROM public.ai_gateway_delta_revisions
                WHERE request_id=:request_id AND revision_sha256=:revision_sha256'''),params).scalar_one_or_none()
        if revision_id is None:
            raise RuntimeError('delta revision insert/read failed')
        values = {'request_id':request_id,'revision_id':str(revision_id)}
        orm.execute(text('''INSERT INTO public.ai_gateway_delta_heads(request_id,revision_id,updated_at)
            VALUES (:request_id,:revision_id,now()) ON CONFLICT(request_id) DO UPDATE
            SET revision_id=EXCLUDED.revision_id,updated_at=EXCLUDED.updated_at
            WHERE ai_gateway_delta_heads.revision_id IS DISTINCT FROM EXCLUDED.revision_id'''),values)
        for consumer in ('daily_worklog','member_wiki'):
            orm.execute(text('''INSERT INTO public.ai_gateway_delta_consumer_jobs(revision_id,consumer)
                VALUES (:revision_id,:consumer) ON CONFLICT(revision_id,consumer) DO NOTHING'''),
                {**values,'consumer':consumer})
        identities[request_id] = str(revision_id)
    return identities


def refresh_request_scope(orm, *, request_id):
    """Recompute a whole scope under the same lock used by producer publication.

    No commit or rollback here; callers own the transaction. None means lock
    contention. Budget failure leaves all pending work and old heads unchanged.
    """
    scope = orm.execute(text('''SELECT scope_key FROM public.ai_gateway_delta_pending_sources
        WHERE request_id=:request_id'''),{'request_id':str(request_id)}).scalar_one_or_none()
    if scope is None:
        raise ValueError('personal delta source is not registered')
    if not orm.execute(text('SELECT pg_try_advisory_xact_lock(hashtextextended(:scope,0))'),
                       {'scope':scope}).scalar_one():
        return None
    planner=_planner()
    sizes=orm.execute(text('''SELECT count(*) AS requests,
        COALESCE(sum(jsonb_array_length(s.event_payload->'messages')),0) AS messages,
        COALESCE(sum(octet_length(s.event_payload::text)),0) AS bytes
        FROM public.ai_gateway_personal_delta_sources s
        JOIN public.ai_gateway_delta_pending_sources p USING(request_id) WHERE p.scope_key=:scope'''),
        {'scope':scope}).one()
    if sizes.requests > planner.MAX_REQUESTS or sizes.messages > planner.MAX_MESSAGES or sizes.bytes > planner.MAX_SERIALIZED_BYTES:
        raise ValueError('complete conversation scope exceeds delta budget')
    rows=orm.execute(text('''SELECT s.* FROM public.ai_gateway_personal_delta_sources s
        JOIN public.ai_gateway_delta_pending_sources p USING(request_id)
        WHERE p.scope_key=:scope ORDER BY s.admitted_at,s.request_id'''),{'scope':scope}).all()
    if not rows:
        raise ValueError('registered delta scope has no eligible source')
    sources=[dict(request_id=str(row.request_id),
        member_id=str(row.user_id) if row.event_payload.get('project_id') else row.employee_id,
        **({'employee_id':row.employee_id} if row.event_payload.get('project_id') else {}),
        gateway_instance_id=row.gateway_instance_id,project_id=row.event_payload.get('project_id'),admitted_at=row.admitted_at.isoformat(),
        work_date=row.work_date.isoformat(),status_code=row.status_code,payload=row.event_payload) for row in rows]
    projections=planner.derive_deltas(sources)
    revisions=persist_projections(orm,sources,projections)
    orm.execute(text('''UPDATE public.ai_gateway_delta_pending_sources SET processed_at=now()
        WHERE scope_key=:scope AND processed_at IS NULL
          AND request_id=ANY(CAST(:requests AS uuid[]))'''),{'scope':scope,'requests':list(revisions)})
    return revisions


def _consumer(value):
    if value not in ('daily_worklog','member_wiki'):
        raise ValueError('invalid delta consumer')
    return value


def pending_jobs(orm, *, consumer, employee_id=None, work_date, owner_user_id=None):
    """Capture version IDs; superseded jobs remain visible for audited handling."""
    conditions=['r.work_date=:work_date'];params={'consumer':_consumer(consumer),'work_date':work_date}
    if employee_id is not None:
        conditions.append('r.employee_id=:employee_id');params['employee_id']=employee_id
    if owner_user_id is not None:
        conditions.append('''EXISTS (SELECT 1 FROM public.ai_gateway_admissions a
            WHERE a.id=r.request_id AND a.user_id=CAST(:owner_user_id AS uuid))''')
        params['owner_user_id']=str(uuid.UUID(str(owner_user_id)))
    elif employee_id is None:
        raise ValueError('delta pending jobs require owner UUID or explicit legacy scope')
    return orm.execute(text(f'''SELECT j.revision_id,r.request_id,r.work_date,r.projection,
        (h.revision_id=j.revision_id) AS is_current
        FROM public.ai_gateway_delta_consumer_jobs j
        JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
        JOIN public.ai_gateway_delta_heads h ON h.request_id=r.request_id
        WHERE j.consumer=:consumer AND j.consumed_at IS NULL
          AND {' AND '.join(conditions)}
        ORDER BY r.request_id,j.revision_id'''),
        params).all()


def acknowledge_jobs(orm, *, consumer, revisions):
    consumer=_consumer(consumer)
    if not revisions:
        return
    orm.execute(text('''UPDATE public.ai_gateway_delta_consumer_jobs SET consumed_at=now()
        WHERE consumer=:consumer AND consumed_at IS NULL AND revision_id=ANY(CAST(:revisions AS uuid[]))'''),
        {'consumer':consumer,'revisions':revisions})


def _record_attempt(orm, scope, error):
    orm.execute(text('''UPDATE public.ai_gateway_delta_pending_sources SET last_attempt_at=now(),
        attempt_count=attempt_count+1,last_error_code=:error WHERE scope_key=:scope AND processed_at IS NULL'''),
        {'scope':scope,'error':error})


def refresh_pending_scopes(orm, *, limit=32):
    """One transaction per scope, with persisted retry order and no source erasure."""
    if type(limit) is not int or not 1<=limit<=256:
        raise ValueError('invalid delta dispatcher limit')
    rows=orm.execute(text('''SELECT scope_key,(array_agg(request_id ORDER BY enqueued_at,request_id))[1] AS request_id
        FROM public.ai_gateway_delta_pending_sources WHERE processed_at IS NULL GROUP BY scope_key
        ORDER BY min(last_attempt_at) NULLS FIRST,min(enqueued_at),scope_key LIMIT :limit'''),{'limit':limit}).all()
    counts={'processed_scopes':0,'failed_scopes':0,'busy_scopes':0}
    for row in rows:
        try:
            _record_attempt(orm,row.scope_key,None)
            result=refresh_request_scope(orm,request_id=str(row.request_id))
            if result is None:
                orm.rollback();_record_attempt(orm,row.scope_key,'scope_busy');orm.commit()
                counts['busy_scopes']+=1
            else:
                orm.commit();counts['processed_scopes']+=1
        except Exception as error:
            orm.rollback()
            _record_attempt(orm,row.scope_key,'scope_validation_failed' if isinstance(error,ValueError) else 'refresh_failed')
            orm.commit();counts['failed_scopes']+=1
    return counts


def pending_work_dates(orm, *, through, limit=31):
    if type(limit) is not int or not 1<=limit<=366:
        raise ValueError('invalid pending date limit')
    rows=orm.execute(text('''SELECT DISTINCT r.work_date FROM public.ai_gateway_delta_consumer_jobs j
        JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
        WHERE j.consumer='daily_worklog' AND j.consumed_at IS NULL AND r.work_date<=:through
        ORDER BY r.work_date LIMIT :limit'''),{'through':through,'limit':limit}).all()
    return [row.work_date for row in rows]
