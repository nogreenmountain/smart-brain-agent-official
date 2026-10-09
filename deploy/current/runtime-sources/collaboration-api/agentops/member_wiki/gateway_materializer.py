"""UUID Gateway publication transaction; candidates only until worker acceptance.

No commits, inferred legacy ownership or baseline adoption. Existing manual and
legacy rows are preserved; overlapping bound keys fail closed for explicit audit.
"""
import json
import os
import uuid
from datetime import timezone, timedelta
from sqlalchemy import text
try:
    from agentops.member_wiki import compiler, contributions, contribution_store, domain, privacy
    from agentops.ai_usage.daily_delta_sources import project_messages
    from agentops.ai_usage.delta_revisions import acknowledge_jobs
except ModuleNotFoundError:
    from agentops_local.member_wiki import compiler, contributions, contribution_store, domain, privacy
    from agentops_local.ai_usage.daily_delta_sources import project_messages
    from agentops_local.ai_usage.delta_revisions import acknowledge_jobs

MAX_REQUESTS = 256
MAX_MESSAGES = 10000
MAX_BYTES = 8 * 1024 * 1024
MAX_PUBLICATION_BYTES = 8 * 1024 * 1024
MAX_JOBS = 2048
MAX_KEYS = 768
SHANGHAI = timezone(timedelta(hours=8))

SOURCE_FROM = """public.ai_gateway_delta_heads h
    JOIN public.ai_gateway_delta_revisions r ON r.id=h.revision_id AND r.request_id=h.request_id
    JOIN public.ai_gateway_admissions a ON a.id=h.request_id
    JOIN public.ai_gateway_events e ON e.event_id=a.id::text AND e.user_id=a.user_id
        AND e.gateway_instance_id=a.gateway_instance_id AND e.key_id=a.key_id
    JOIN public.ai_gateway_delta_pending_sources pending ON pending.request_id=a.id"""
SOURCE_WHERE = 'a.user_id=CAST(:owner AS uuid) AND a.admitted_at<:cutoff'
ELIGIBLE = """a.delivered_at IS NOT NULL AND a.event_sha256 IS NOT NULL
    AND jsonb_typeof(a.event_payload)='object' AND a.event_payload ? 'project_id'
    AND a.event_payload->'content_complete'='true'::jsonb AND e.status_code>=200 AND e.status_code<400
    AND r.projection->>'status' IN ('exact_prefix','unattributed_context','independent_request')
    AND NOT EXISTS(SELECT 1 FROM public.ai_gateway_delta_pending_sources dirty
        WHERE dirty.scope_key=pending.scope_key AND dirty.processed_at IS NULL)
    AND (a.event_payload->'project_id'='null'::jsonb OR EXISTS(
        SELECT 1 FROM public.project_members member JOIN public.projects project ON project.id=member.project_id
        WHERE member.user_id=a.user_id AND project.id::text=a.event_payload->>'project_id'))"""


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _enabled():
    if os.getenv('SB_GATEWAY_PERSONAL_CONSUMERS_ENABLED', 'false').lower() != 'true':
        raise ValueError('Gateway Wiki consumers are disabled')


def _owner(orm, params, *, lock=False):
    row = orm.execute(text('''SELECT u.full_name FROM public.users u JOIN auth.users a ON a.id=u.id
        WHERE u.id=CAST(:owner AS uuid) AND u.is_active IS TRUE''' + (' FOR SHARE OF u,a' if lock else '')), params).first()
    if row is None:
        raise ValueError('Wiki owner must be an active account')
    return str(row.full_name or params['owner'])


def _sources(orm, params):
    where=SOURCE_WHERE
    if '_requests' in params:
        where+=' AND a.id=ANY(CAST(:_requests AS uuid[]))'
    # Count all heads independently so a missing event/pending join cannot hide
    # a corrupt source and turn a formerly published contribution into a deletion.
    total = orm.execute(text('''SELECT count(*) FROM public.ai_gateway_delta_heads h
        JOIN public.ai_gateway_admissions a ON a.id=h.request_id WHERE ''' + where), params).scalar_one()
    if '_requests' in params and total!=len(set(params['_requests'])):
        raise ValueError('Wiki captured source snapshot is incomplete')
    sizes = orm.execute(text(f'''SELECT count(*) AS requests,
        COALESCE(sum(jsonb_array_length(a.event_payload->'messages')),0) AS messages,
        COALESCE(sum(octet_length(a.event_payload::text)+octet_length(r.projection::text)),0) AS bytes,
        COALESCE(bool_and(({ELIGIBLE}) IS TRUE),true) AS eligible
        FROM {SOURCE_FROM} WHERE {where}'''), params).one()
    if sizes.requests != total or not sizes.eligible:
        raise ValueError('Wiki source authorization or delta projection is pending')
    if total > MAX_REQUESTS or sizes.messages > MAX_MESSAGES or sizes.bytes > MAX_BYTES:
        raise ValueError('Wiki complete owner source budget exceeded')
    # This guard and the body projection share one MVCC statement. The earlier
    # aggregate gives a useful error, but cannot authorize this later transfer.
    rows = orm.execute(text(f'''WITH transfer_budget AS MATERIALIZED (
        SELECT count(*) AS requests,
          COALESCE(sum(jsonb_array_length(a.event_payload->'messages')),0) AS messages,
          COALESCE(sum(octet_length(a.event_payload::text)+octet_length(r.projection::text)),0) AS bytes,
          COALESCE(bool_and(({ELIGIBLE}) IS TRUE),true) AS eligible
        FROM {SOURCE_FROM} WHERE {where})
        SELECT a.id::text AS request_id,h.revision_id::text,
        r.employee_id,r.projection,a.event_payload,a.event_sha256,a.admitted_at,pending.scope_key
        FROM {SOURCE_FROM} CROSS JOIN transfer_budget budget WHERE {where}
          AND budget.requests=:expected_count AND budget.requests<=:max_requests
          AND budget.messages<=:max_messages AND budget.bytes<=:max_bytes AND budget.eligible
        ORDER BY a.admitted_at,a.id'''), {**params,'expected_count':total,
            'max_requests':MAX_REQUESTS,'max_messages':MAX_MESSAGES,'max_bytes':MAX_BYTES}).all()
    if len(rows) != total:
        raise ValueError('Wiki source snapshot changed or exceeds transfer budget; retry')
    return rows


def _pending(orm, params):
    rows = orm.execute(text('''SELECT j.revision_id::text FROM public.ai_gateway_delta_consumer_jobs j
        JOIN public.ai_gateway_delta_revisions r ON r.id=j.revision_id
        JOIN public.ai_gateway_admissions a ON a.id=r.request_id
        WHERE a.user_id=CAST(:owner AS uuid) AND a.admitted_at<:cutoff AND j.enqueued_at<:cutoff
          AND j.consumer='member_wiki' AND j.consumed_at IS NULL
        ORDER BY j.revision_id LIMIT :job_limit'''), {**params, 'job_limit': MAX_JOBS+1}).scalars().all()
    if len(rows) > MAX_JOBS:
        raise ValueError('Wiki captured job budget exceeded')
    return rows


def _previous(orm, params):
    where='p.owner_user_id=CAST(:owner AS uuid)'
    if '_keys' in params:
        where+=' AND p.experience_key=ANY(CAST(:_keys AS text[]))'
    sizes = orm.execute(text(f'''SELECT count(*) AS keys,COALESCE(sum(octet_length(to_jsonb(p)::text)),0) AS bytes
        FROM public.member_wiki_gateway_publications p WHERE {where}'''),params).one()
    if sizes.keys > MAX_KEYS or sizes.bytes > MAX_PUBLICATION_BYTES:
        raise ValueError('Wiki publication snapshot budget exceeded')
    rows = orm.execute(text(f'''WITH transfer_budget AS MATERIALIZED (
        SELECT count(*) AS keys,COALESCE(sum(octet_length(to_jsonb(p)::text)),0) AS bytes
        FROM public.member_wiki_gateway_publications p WHERE {where})
        SELECT p.*,p.experience_snapshot=to_jsonb(w) AND
        p.source_snapshot=(SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.session_id),'[]'::jsonb)
          FROM public.member_wiki_experience_sources s WHERE s.experience_id=w.id) AS unchanged
        FROM public.member_wiki_gateway_publications p
        JOIN public.member_wiki_experiences w ON w.id=p.experience_id
        CROSS JOIN transfer_budget budget WHERE {where}
          AND budget.keys=:expected_count AND budget.keys<=:key_limit AND budget.bytes<=:byte_limit
        ORDER BY p.experience_key FOR UPDATE OF p,w'''), {**params, 'key_limit': MAX_KEYS,
            'byte_limit':MAX_PUBLICATION_BYTES,'expected_count':sizes.keys}).all()
    if len(rows) != sizes.keys:
        raise ValueError('Wiki publication snapshot changed or exceeds transfer budget; retry')
    if any(not row.unchanged for row in rows):
        raise ValueError('Wiki external edit requires baseline audit')
    return {row.experience_key: row for row in rows}


def _compile(orm, params, rows, name, generate_text):
    revision_ids = [row.revision_id for row in rows]
    # A bounded LEFT JOIN returns only size metadata when bodies exceed the
    # limit. No earlier count can authorize a later concurrent body transfer.
    stored = orm.execute(text('''/* wiki_contribution_transfer */
        WITH transfer_budget AS MATERIALIZED (
          SELECT COALESCE(sum(octet_length(to_jsonb(c)::text)),0) AS bytes
          FROM public.member_wiki_gateway_contributions c WHERE revision_id=ANY(CAST(:ids AS uuid[])))
        SELECT c.*,budget.bytes AS transfer_bytes FROM transfer_budget budget
        LEFT JOIN public.member_wiki_gateway_contributions c
          ON c.revision_id=ANY(CAST(:ids AS uuid[])) AND budget.bytes<=:byte_limit
        ORDER BY c.revision_id'''),{'ids':revision_ids,'byte_limit':MAX_BYTES}).all()
    size = stored[0].transfer_bytes
    if size > MAX_BYTES:
        raise ValueError('Wiki contribution budget exceeded')
    saved = {str(row.revision_id): row for row in stored if row.revision_id is not None}
    result = []
    for row in rows:
        if row.revision_id in saved:
            prior = saved[row.revision_id]
            if str(prior.owner_user_id) != params['owner'] or str(prior.request_id) != row.request_id:
                raise ValueError('Wiki contribution owner mismatch')
            items = prior.experiences
        else:
            conversation = compiler.MemberWikiConversation(session_id=row.request_id,employee_id=row.employee_id,
                employee_name=name,title=str(row.event_payload.get('title') or 'AI request'),source='ai_gateway_personal',
                task_id='unassigned',task_title='',model=str(row.event_payload.get('model') or 'unknown'),
                trace_id=None,started_at=row.admitted_at,
                messages=tuple(compiler.MemberWikiMessage(**m) for m in project_messages(row.event_payload,row.projection)))
            def bounded_generate(prompt):
                try:
                    raw = (generate_text or compiler.generate_experiences)(prompt)
                    if not isinstance(raw,str) or len(raw.encode('utf-8')) > 128*1024:
                        raise ValueError('model output exceeds budget')
                    return raw
                except Exception:
                    raise RuntimeError('Wiki model generation failed; pending retained') from None
            items = [domain.experience_to_dict(item) for item in compiler.compile_experiences(
                conversation,generate_text=bounded_generate)]
            size += len(_json(items).encode('utf-8'))
            if size > MAX_BYTES:
                raise ValueError('Wiki compiled contribution budget exceeded')
            contribution_store.save_contribution(orm,revision_id=row.revision_id,request_id=row.request_id,
                owner_user_id=params['owner'],employee_id=row.employee_id,model=compiler.model_name(),experiences=items)
        result.append(dict(request_id=row.request_id,revision_id=row.revision_id,owner_user_id=params['owner'],
            employee_id=row.employee_id,observed_at=row.admitted_at.isoformat(),experiences=items))
    persisted_size = orm.execute(text('''SELECT COALESCE(sum(octet_length(to_jsonb(c)::text)),0)
        FROM public.member_wiki_gateway_contributions c WHERE revision_id=ANY(CAST(:ids AS uuid[]))'''),
        {'ids':revision_ids}).scalar_one()
    if persisted_size > MAX_BYTES:
        raise ValueError('Wiki complete compiled contribution budget exceeded')
    return result


def publish_owner(orm, *, owner_user_id, cutoff, generate_text=None, embed_text=None, selected_heads=None):
    """Publish a bounded pending batch; the caller owns the outer commit."""
    try:
        from agentops.member_wiki.incremental_publication import publish
    except ModuleNotFoundError:
        from agentops_local.member_wiki.incremental_publication import publish
    return publish(orm,owner_user_id=owner_user_id,cutoff=cutoff,
        generate_text=generate_text,embed_text=embed_text,selected_heads=selected_heads)


def _write_experience(orm, params, key, value, previous, heads, sources, name, embed_text):
    identifier = str(previous.experience_id) if previous else str(uuid.uuid4())
    conflict = orm.execute(text('''SELECT 1 FROM public.member_wiki_access_bindings b
        JOIN public.member_wiki_experiences w ON w.id=b.experience_id
        WHERE b.owner_user_id=CAST(:owner AS uuid) AND w.experience_key=:key AND w.id<>CAST(:id AS uuid)
        LIMIT 1'''),{**params,'key':key,'id':identifier}).first()
    if conflict:
        raise ValueError('Wiki matching legacy baseline requires explicit audit')
    storage = 'gateway-owner:' + params['owner']
    version = int(previous.version)+1 if previous else 1
    selected = [sources[request] for request in value['source_session_ids']]
    if value['status']=='active':
        dates = [row.admitted_at.astimezone(SHANGHAI).date() for row in selected]
        first,last = min(dates),max(dates)
        experience = domain.experience_from_dict(value['experience'])
        # Domain summaries bound their references. Published source coordinates
        # and counts must retain the entire current contribution set separately.
        markdown = domain.render_experience_markdown(experience,employee_id=storage,employee_name=name,
            first_observed=first,last_observed=last,observation_count=value['observation_count'],
            source_session_ids=tuple(value['source_session_ids']),source_trace_ids=())
        if embed_text is None:
            raise ValueError('Wiki publisher requires an explicit embedding provider')
        try:
            embedding = embed_text(markdown)
            if embedding is not None:
                if len(embedding)!=1024:
                    raise ValueError('invalid embedding size')
                embedding = _json([float(item) for item in embedding])
        except Exception:
            raise RuntimeError('Wiki embedding failed; pending retained') from None
        fields = dict(employee_name=name,title=experience.title,task_type=experience.task_type,
            outcome=experience.outcome,summary=experience.summary,structured_content=_json(domain.experience_to_dict(experience)),
            markdown_content=markdown,tags=list(experience.tags),tools=list(experience.tools),confidence=experience.confidence,
            first_observed=first,last_observed=last,observation_count=value['observation_count'],
            source_session_ids=_json(value['source_session_ids']),source_trace_ids='[]',
            current_version=version,embedding=embedding,
            embedding_model=os.getenv('RAG_V2_EMBEDDING_MODEL','BAAI/bge-m3') if embedding is not None else None,
            embedding_version=os.getenv('RAG_V2_EMBEDDING_VERSION','2026-07-21-bge-m3') if embedding is not None else None,
            status='active')
    else:
        if previous is None:
            raise ValueError('Wiki empty projection has no prior publication')
        # Preserve last body in the original row/history while making it stale,
        # clearing searchable vectors and current sources, with an honest count.
        fields = dict(current_version=version,status='stale',observation_count=0,
            source_session_ids='[]',source_trace_ids='[]',embedding=None,embedding_model=None,embedding_version=None)
    casts = {'structured_content':'jsonb','source_session_ids':'jsonb','source_trace_ids':'jsonb',
             'tags':'text[]','tools':'text[]','embedding':'vector(1024)'}
    # All column names and casts originate in the fixed dictionaries above.
    def expression(column):
        return f'CAST(:{column} AS {casts[column]})' if column in casts else ':'+column
    if previous:
        orm.execute(text('UPDATE public.member_wiki_experiences SET '+
            ','.join(column+'='+expression(column) for column in fields)+',updated_at=now() WHERE id=CAST(:id AS uuid)'),
            {**fields,'id':identifier})
    else:
        fields.update(id=identifier,employee_id=storage,experience_key=key)
        orm.execute(text('INSERT INTO public.member_wiki_experiences ('+','.join(fields)+') VALUES ('+
            ','.join(expression(column) for column in fields)+')'),fields)
    orm.execute(text('''INSERT INTO public.member_wiki_experience_versions
        (experience_id,version,structured_content,markdown_content,source_session_ids)
        SELECT id,current_version,structured_content,markdown_content,source_session_ids
        FROM public.member_wiki_experiences WHERE id=CAST(:id AS uuid)'''),{'id':identifier})
    orm.execute(text('DELETE FROM public.member_wiki_experience_sources WHERE experience_id=CAST(:id AS uuid)'),{'id':identifier})
    for source in selected:
        # Existing source validator uses this provenance family label for both
        # scopes. Immutable admission.project_id determines the real ACL.
        orm.execute(text('''INSERT INTO public.member_wiki_experience_sources
            (experience_id,session_id,observed_at,source) VALUES(CAST(:id AS uuid),CAST(:request AS uuid),:observed,'ai_gateway_personal')'''),
            {'id':identifier,'request':source.request_id,'observed':source.admitted_at})
    if value['status']=='active':
        privacy.bind_experience(orm,experience_id=identifier,owner_user_id=params['owner'])
    orm.execute(text('''INSERT INTO public.member_wiki_gateway_publications
        (owner_user_id,experience_key,experience_id,version,projection_sha256,dependencies,experience_snapshot,source_snapshot)
        SELECT CAST(:owner AS uuid),w.experience_key,w.id,w.current_version,:sha,CAST(:dependencies AS jsonb),to_jsonb(w),
          (SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.session_id),'[]'::jsonb)
           FROM public.member_wiki_experience_sources s WHERE s.experience_id=w.id)
        FROM public.member_wiki_experiences w WHERE w.id=CAST(:id AS uuid)
        ON CONFLICT(owner_user_id,experience_key) DO UPDATE SET version=EXCLUDED.version,
          projection_sha256=EXCLUDED.projection_sha256,dependencies=EXCLUDED.dependencies,
          experience_snapshot=EXCLUDED.experience_snapshot,source_snapshot=EXCLUDED.source_snapshot'''),
        {**params,'id':identifier,'sha':value['revision_sha256'],'dependencies':_json(heads)})
    orm.execute(text('''INSERT INTO public.member_wiki_gateway_publication_versions
        (experience_id,version,owner_user_id,publication_snapshot)
        SELECT p.experience_id,p.version,p.owner_user_id,to_jsonb(p)
        FROM public.member_wiki_gateway_publications p WHERE p.experience_id=CAST(:id AS uuid)'''),{'id':identifier})
