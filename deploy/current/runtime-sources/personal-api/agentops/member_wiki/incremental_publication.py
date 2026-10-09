"""Bounded pending compilation and per-key streaming publication.

Uncompiled replacements of known key sources stay pending; this entry does not
silently substitute old revisions or discard a source to close a dependency.
"""
import uuid
from types import SimpleNamespace
from sqlalchemy import text
try:
    from agentops.member_wiki import gateway_materializer as core,privacy
    from agentops.member_wiki.key_fold import KeyFold
except ModuleNotFoundError:
    from agentops_local.member_wiki import gateway_materializer as core,privacy
    from agentops_local.member_wiki.key_fold import KeyFold

BATCH_REQUESTS=32
PAGE_SOURCES=128


class PendingDependencies(ValueError):
    """Current heads exist but their immutable compilation is not ready."""


def _capture(orm,params):
    candidates=orm.execute(text('''SELECT r.request_id::text,h.revision_id::text,
        NOT EXISTS(SELECT 1 FROM public.member_wiki_gateway_contributions c WHERE c.revision_id=h.revision_id) AS missing
        FROM public.ai_gateway_delta_consumer_jobs j JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
        JOIN public.ai_gateway_delta_heads h ON h.request_id=r.request_id
        JOIN public.ai_gateway_admissions a ON a.id=r.request_id
        WHERE a.user_id=CAST(:owner AS uuid) AND a.admitted_at<:cutoff AND j.enqueued_at<:cutoff
          AND j.consumer='member_wiki' AND j.consumed_at IS NULL
          AND (:selected_count=0 OR a.id=ANY(CAST(:selected_requests AS uuid[])))
        GROUP BY r.request_id,h.revision_id ORDER BY missing DESC,min(j.enqueued_at),r.request_id
        LIMIT :batch_limit'''),{**params,'batch_limit':BATCH_REQUESTS,
            'selected_count':len(params.get('_selected_heads',{})),
            'selected_requests':list(params.get('_selected_heads',{}))}).all()
    jobs=orm.execute(text('''SELECT j.revision_id::text,r.request_id::text
        FROM public.ai_gateway_delta_consumer_jobs j JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
        WHERE r.request_id=ANY(CAST(:requests AS uuid[])) AND j.consumer='member_wiki'
          AND j.enqueued_at<:cutoff AND j.consumed_at IS NULL ORDER BY j.enqueued_at,j.revision_id
        LIMIT :job_limit'''),{**params,'requests':[r.request_id for r in candidates],'job_limit':core.MAX_JOBS}).all()
    captured={row.request_id for row in jobs}
    return [r for r in candidates if r.request_id in captured],[r.revision_id for r in jobs]


def _metadata(orm,params,requests,*,lock=False):
    if not requests:return {}
    if len(requests)>core.MAX_REQUESTS:
        raise ValueError('Wiki metadata batch budget exceeded')
    rows=orm.execute(text(f'''SELECT a.id::text AS request_id,h.revision_id::text,
        r.employee_id,a.event_sha256,a.admitted_at,pending.scope_key,
        jsonb_build_object('project_id',a.event_payload->'project_id') AS event_payload,
        ({core.ELIGIBLE}) IS TRUE AS eligible
        FROM {core.SOURCE_FROM} WHERE a.user_id=CAST(:owner AS uuid)
          AND a.id=ANY(CAST(:requests AS uuid[])) ORDER BY a.admitted_at,a.id'''+
        (' FOR SHARE OF h' if lock else '')), {**params,'requests':requests}).all()
    if len(rows)!=len(set(requests)) or any(not r.eligible for r in rows):
        raise ValueError('Wiki source authorization or delta snapshot is pending')
    return {r.request_id:r for r in rows}


def _affected_keys(orm,params,requests,records):
    keys={core.domain.experience_from_dict(item).experience_key for row in records for item in row['experiences']}
    previous=orm.execute(text('''SELECT p.experience_key FROM public.member_wiki_gateway_publications p
        WHERE p.owner_user_id=CAST(:owner AS uuid) AND (p.dependencies ?| CAST(:requests AS text[]) OR EXISTS (
          SELECT 1 FROM public.member_wiki_experience_sources s WHERE s.experience_id=p.experience_id
            AND s.session_id=ANY(CAST(:requests AS uuid[])))) ORDER BY p.experience_key LIMIT :key_limit'''),
        {**params,'requests':requests,'key_limit':core.MAX_KEYS+1}).scalars().all()
    keys.update(previous)
    if len(keys)>core.MAX_KEYS:
        raise ValueError('Wiki affected key budget exceeded')
    return sorted(keys)


def _key_sources(orm,params,key):
    values={**params,'match':core._json([{'experience_key':key}]),'key':key,
        'after_date':None,'after_request':None,'page_limit':PAGE_SOURCES,'byte_limit':core.MAX_BYTES}
    # Known contributors with a new, not-yet-compiled head must not disappear
    # just because the inner join to the current compiled source is empty.
    pending=orm.execute(text('''SELECT 1 FROM public.ai_gateway_delta_heads h
        JOIN public.ai_gateway_admissions a ON a.id=h.request_id
        WHERE a.user_id=CAST(:owner AS uuid)
          AND EXISTS(SELECT 1 FROM public.member_wiki_gateway_contributions old
            WHERE old.request_id=h.request_id AND old.owner_user_id=a.user_id AND old.experiences @> CAST(:match AS jsonb))
          AND NOT EXISTS(SELECT 1 FROM public.member_wiki_gateway_contributions current WHERE current.revision_id=h.revision_id)
        LIMIT 1'''),values).first()
    if pending:
        raise PendingDependencies('Wiki affected key has an uncompiled replacement; dependency remains pending')
    fold=KeyFold(owner_user_id=params['owner'],experience_key=key,metadata_budget=core.MAX_BYTES)
    sources={};metadata_bytes=0
    while True:
        page=orm.execute(text(f'''WITH picked AS MATERIALIZED (
            SELECT a.id::text AS request_id,h.revision_id::text,a.user_id::text AS owner_user_id,
              a.admitted_at,a.event_sha256,pending.scope_key,c.content_sha256,
              jsonb_build_object('project_id',a.event_payload->'project_id') AS event_payload,
              (SELECT jsonb_agg(item.value ORDER BY item.ordinality)
                FROM jsonb_array_elements(c.experiences) WITH ORDINALITY item(value,ordinality)
                WHERE item.value->>'experience_key'=:key) AS experiences,
              ({core.ELIGIBLE}) IS TRUE AS eligible
            FROM {core.SOURCE_FROM} JOIN public.member_wiki_gateway_contributions c
              ON c.revision_id=h.revision_id AND c.request_id=h.request_id AND c.owner_user_id=a.user_id
            WHERE a.user_id=CAST(:owner AS uuid) AND c.experiences @> CAST(:match AS jsonb)
              AND (CAST(:after_date AS timestamptz) IS NULL OR (a.admitted_at,a.id)>
                (CAST(:after_date AS timestamptz),CAST(:after_request AS uuid)))
            ORDER BY a.admitted_at,a.id LIMIT :page_limit), budget AS MATERIALIZED (
            SELECT COALESCE(sum(octet_length(to_jsonb(picked)::text)),0) AS bytes,
              COALESCE(bool_and(eligible),true) AS eligible FROM picked)
            SELECT picked.*,budget.bytes AS transfer_bytes,budget.eligible AS transfer_eligible
            FROM budget LEFT JOIN picked ON budget.bytes<=:byte_limit AND budget.eligible
            ORDER BY picked.admitted_at,picked.request_id'''),values).all()
        if page[0].transfer_bytes>core.MAX_BYTES:
            raise ValueError('Wiki key contribution page budget exceeded')
        if not page[0].transfer_eligible:
            raise ValueError('Wiki key source authorization or projection is pending')
        if page[0].request_id is None:break
        for row in page:
            metadata=dict(request_id=row.request_id,revision_id=row.revision_id,observed_at=row.admitted_at.isoformat(),
                project_id=row.event_payload.get('project_id'),event_sha256=row.event_sha256,scope_key=row.scope_key)
            metadata_bytes+=len(core._json(metadata).encode('utf-8'))
            if metadata_bytes>core.MAX_BYTES:
                raise ValueError('Wiki full key source metadata budget exceeded')
            fold.add(dict(owner_user_id=row.owner_user_id,request_id=row.request_id,revision_id=row.revision_id,
                observed_at=row.admitted_at.isoformat(),project_id=row.event_payload.get('project_id'),
                content_sha256=row.content_sha256,experiences=row.experiences))
            # Do not retain the page's compiled bodies in the source catalog.
            sources[row.request_id]=SimpleNamespace(request_id=row.request_id,revision_id=row.revision_id,
                admitted_at=row.admitted_at,event_payload=row.event_payload,event_sha256=row.event_sha256,scope_key=row.scope_key)
        values.update(after_date=page[-1].admitted_at,after_request=page[-1].request_id)
        if len(page)<PAGE_SOURCES:break
    return fold.finish(),fold.heads,sources


def _publication_gate(orm,params,keys):
    values={**params,'keys':keys,'caller_user_id':params['owner'],'owner_user_ids':[params['owner']]}
    valid=orm.execute(text(f'''SELECT NOT EXISTS (
        SELECT 1 FROM public.member_wiki_gateway_publications p
        JOIN public.member_wiki_experiences published ON published.id=p.experience_id
        WHERE p.owner_user_id=CAST(:owner AS uuid) AND p.experience_key=ANY(CAST(:keys AS text[]))
          AND published.status='active' AND NOT EXISTS (
            SELECT 1 FROM {privacy.READ_FROM_SQL} WHERE wiki.id=p.experience_id AND {privacy.READ_FILTER_SQL}))'''),values).scalar_one()
    if not valid:
        raise ValueError('Wiki final source authorization or dependency changed; retry')



def _captured_gate(orm,params,requests,expected):
    core._enabled()
    core._owner(orm,params,lock=True)
    latest=_metadata(orm,params,requests,lock=True)
    if {key:row.revision_id for key,row in latest.items()}!=expected:
        raise ValueError('Wiki captured head changed during generation; retry')
    # Retain source project membership locks until the caller commits staged
    # candidates. Missing/revoked membership is rejected by the recheck.
    orm.execute(text('''SELECT member.project_id FROM public.ai_gateway_admissions a
        JOIN public.projects project ON project.id::text=a.event_payload->>'project_id'
        JOIN public.project_members member ON member.project_id=project.id AND member.user_id=a.user_id
        WHERE a.user_id=CAST(:owner AS uuid) AND a.id=ANY(CAST(:requests AS uuid[]))
        FOR SHARE OF member,project'''),{**params,'requests':requests})
    latest=_metadata(orm,params,requests,lock=True)
    if {key:row.revision_id for key,row in latest.items()}!=expected:
        raise ValueError('Wiki captured head changed during authorization; retry')


def publish(orm, *, owner_user_id, cutoff, generate_text=None, embed_text=None, selected_heads=None):
    if cutoff.tzinfo is None:
        raise ValueError('Wiki cutoff requires a timezone')
    params=dict(owner=str(uuid.UUID(str(owner_user_id))),cutoff=cutoff)
    if selected_heads is not None:
        if not isinstance(selected_heads,dict) or not 1<=len(selected_heads)<=BATCH_REQUESTS:
            raise ValueError('Wiki selected head batch is invalid')
        params['_selected_heads']={str(uuid.UUID(str(request))):str(uuid.UUID(str(revision)))
            for request,revision in selected_heads.items()}
    with orm.begin_nested():
        core._enabled()
        if not orm.execute(text('SELECT pg_try_advisory_xact_lock(hashtextextended(:lock,0))'),
            {'lock':core._json(['gateway-wiki-owner-v1',params['owner']])}).scalar_one():
            return {'status':'busy'}
        name=core._owner(orm,params)
        captured,jobs=_capture(orm,params)
        if not jobs:return {'status':'noop'}
        requests=[row.request_id for row in captured]
        expected={row.request_id:row.revision_id for row in captured}
        if selected_heads is not None and any(params['_selected_heads'].get(request)!=revision for request,revision in expected.items()):
            raise ValueError('Wiki reserved head changed before publication; retry')
        metadata=_metadata(orm,params,requests)
        if {key:row.revision_id for key,row in metadata.items()}!=expected:
            raise ValueError('Wiki captured head snapshot changed; retry')
        missing=[row.request_id for row in captured if row.missing]
        raw={row.request_id:row for row in core._sources(orm,{**params,'_requests':missing})} if missing else {}
        if any(row.revision_id!=expected[key] for key,row in raw.items()):
            raise ValueError('Wiki raw source head snapshot changed; retry')
        rows=[raw.get(request,metadata[request]) for request in requests]
        records=core._compile(orm,params,rows,name,generate_text)
        core._enabled()
        core._owner(orm,params)
        keys=_affected_keys(orm,params,requests,records)
        try:
            # All affected publication rows share a savepoint. A later key
            # waiting on another batch must also undo earlier key writes.
            with orm.begin_nested():
                previous=core._previous(orm,{**params,'_keys':keys})
                changed=0
                for key in keys:
                    value,heads,sources=_key_sources(orm,params,key)
                    old=previous.get(key)
                    if old and old.projection_sha256==value['revision_sha256']:
                        continue
                    if value['status']=='stale' and old is None:
                        raise ValueError('Wiki affected key has no contribution or prior publication')
                    core._write_experience(orm,params,key,value,old,heads,sources,name,embed_text)
                    changed+=1
                total=orm.execute(text('''SELECT COALESCE(sum(octet_length(to_jsonb(p)::text)),0)
                    FROM public.member_wiki_gateway_publications p WHERE p.owner_user_id=CAST(:owner AS uuid)
                      AND p.experience_key=ANY(CAST(:keys AS text[]))'''),{**params,'keys':keys}).scalar_one()
                if total>core.MAX_PUBLICATION_BYTES:
                    raise ValueError('Wiki generated affected publication snapshot budget exceeded')
        except PendingDependencies:
            # Keep only immutable compiled candidates, never partial Wiki
            # publication or ACK. The caller still owns the outer commit.
            _captured_gate(orm,params,requests,expected)
            return {'status':'staged','experience_count':0,'acknowledged_count':0,
                'captured_request_count':len(requests),'raw_request_count':len(raw),
                'compiled_request_count':len(missing)}
        core._enabled()
        core._owner(orm,params,lock=True)
        latest=_metadata(orm,params,requests,lock=True)
        if {key:row.revision_id for key,row in latest.items()}!=expected:
            raise ValueError('Wiki captured head changed during generation; retry')
        _publication_gate(orm,params,keys)
        # Hold current source memberships through commit. Query only the
        # affected publications; no historical request bodies leave the DB.
        orm.execute(text('''SELECT member.project_id FROM public.member_wiki_gateway_publications p
            JOIN public.member_wiki_experience_sources s ON s.experience_id=p.experience_id
            JOIN public.ai_gateway_admissions a ON a.id=s.session_id
            JOIN public.projects project ON project.id::text=a.event_payload->>'project_id'
            JOIN public.project_members member ON member.project_id=project.id AND member.user_id=a.user_id
            WHERE p.owner_user_id=CAST(:owner AS uuid) AND p.experience_key=ANY(CAST(:keys AS text[]))
            FOR SHARE OF member,project'''),{**params,'keys':keys})
        _publication_gate(orm,params,keys)
        core.acknowledge_jobs(orm,consumer='member_wiki',revisions=jobs)
        return {'status':'published','experience_count':changed,'acknowledged_count':len(jobs),
            'captured_request_count':len(requests),'raw_request_count':len(raw)}
