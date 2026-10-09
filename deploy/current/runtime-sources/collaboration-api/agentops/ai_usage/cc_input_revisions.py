"""Immutable authenticated CC input occurrences and exact Wiki acknowledgements.

No historical backfill, implicit commit, alias ownership or current-row content
substitution. The feature remains disabled until API and consumers deploy as a
single reviewed package. Daily jobs are recorded but not dispatched here.
"""
import json
import os
from sqlalchemy import text


def claim_wiki_input(orm, revision_id):
    from sqlalchemy.engine import Engine
    from sqlalchemy.orm import Session
    import uuid
    engine=orm.get_bind()
    if not isinstance(engine, Engine):
        raise ValueError('CC claim requires an Engine for an independent transaction')
    # A separate connection commits only the claim, never the caller's run,
    # publication or input writes. The job lock serializes contenders.
    with Session(engine) as claims, claims.begin():
        _validate_wiki_input(claims,revision_id)
        params={'id':str(revision_id)}
        active=claims.execute(text('''SELECT a.id FROM public.cc_wiki_claims c
          JOIN public.cc_wiki_attempts a ON a.id=c.attempt_id
          WHERE c.revision_id=CAST(:id AS uuid) AND a.lease_until>clock_timestamp()'''),params).first()
        if active is not None:
            return None
        attempt=str(uuid.uuid4());params['attempt']=attempt
        claims.execute(text('''INSERT INTO public.cc_wiki_attempts(id,revision_id)
          VALUES(CAST(:attempt AS uuid),CAST(:id AS uuid))'''),params)
        claims.execute(text('''INSERT INTO public.cc_wiki_claims(revision_id,attempt_id)
          VALUES(CAST(:id AS uuid),CAST(:attempt AS uuid))
          ON CONFLICT(revision_id) DO UPDATE SET attempt_id=EXCLUDED.attempt_id'''),params)
    return attempt


def enabled():
    return os.getenv('SB_CC_INPUT_REVISIONS_ENABLED','false').lower()=='true'


def _raw_snapshot(orm, session_id):
    row=orm.execute(text('''WITH input AS MATERIALIZED (
      SELECT jsonb_build_object('session',to_jsonb(s),'messages',COALESCE((
        SELECT jsonb_agg(to_jsonb(m) ORDER BY m.sequence_index) FROM public.ai_chat_messages m WHERE m.session_id=s.id),'[]'::jsonb)) AS payload
      FROM public.ai_chat_sessions s WHERE s.id=CAST(:id AS uuid))
      SELECT CASE WHEN octet_length(payload::text)<=8388608 THEN payload END AS snapshot,
        encode(sha256(convert_to(payload::text,'UTF8')),'hex') AS digest FROM input'''),{'id':str(session_id)}).first()
    if row is None or row.snapshot is None:
        raise ValueError('CC input is missing or exceeds snapshot budget')
    return row.snapshot,row.digest


def capture(orm, *, session_id, owner_user_id, project_id, fingerprint):
    """Called after raw session/messages storage, before usage refresh/commit."""
    orm.execute(text('SELECT id FROM public.ai_chat_sessions WHERE id=CAST(:id AS uuid) FOR UPDATE'),{'id':str(session_id)}).one()
    payload,digest=_raw_snapshot(orm,session_id);session=payload['session']
    if (session['source']!='cc_switch' or session['user_id']!=str(owner_user_id)
        or session['project_id']!=str(project_id) or session['content_fingerprint']!=fingerprint):
        raise ValueError('CC input authenticated identity or fingerprint differs')
    previous=orm.execute(text('''SELECT r.id,r.sequence,r.snapshot_sha256 FROM public.cc_input_heads h
      JOIN public.cc_input_revisions r ON r.id=h.revision_id WHERE h.session_id=CAST(:id AS uuid)
      FOR UPDATE OF h'''),{'id':str(session_id)}).first()
    if previous is not None and previous.snapshot_sha256==digest:
        return str(previous.id)
    seen=orm.execute(text('''SELECT EXISTS(SELECT 1 FROM public.cc_input_revisions
      WHERE session_id=CAST(:id AS uuid) AND content_fingerprint=:fingerprint)'''),
      dict(id=str(session_id),fingerprint=fingerprint)).scalar_one()
    complete=(session['status']=='ok' and session['error_count']==0 and session['ended_at'] is not None
      and any(m['role']=='assistant' and m['content'].strip() for m in payload['messages']))
    # Keep PostgreSQL's original JSONB numeric representation; do not serialize
    # the decoded payload back through Python when storing its reviewed hash.
    revision=orm.execute(text('''WITH input AS (
      SELECT jsonb_build_object('session',to_jsonb(s),'messages',COALESCE((
        SELECT jsonb_agg(to_jsonb(m) ORDER BY m.sequence_index) FROM public.ai_chat_messages m WHERE m.session_id=s.id),'[]'::jsonb)) AS payload
      FROM public.ai_chat_sessions s WHERE s.id=CAST(:id AS uuid))
      INSERT INTO public.cc_input_revisions(session_id,sequence,owner_user_id,project_id,source,
        content_fingerprint,snapshot,snapshot_sha256,content_complete,previously_seen_payload)
      SELECT CAST(:id AS uuid),:sequence,CAST(:owner AS uuid),CAST(:project AS uuid),'cc_switch',
        :fingerprint,payload,:digest,:complete,:seen FROM input RETURNING id'''),dict(id=str(session_id),
        sequence=(previous.sequence+1 if previous else 1),owner=str(owner_user_id),project=str(project_id),
        fingerprint=fingerprint,digest=digest,complete=complete,seen=seen)).scalar_one()
    orm.execute(text('''UPDATE public.cc_input_consumer_jobs j SET status='superseded',updated_at=now()
      FROM public.cc_input_revisions r WHERE r.id=j.revision_id AND r.session_id=CAST(:id AS uuid) AND j.status='pending' '''),{'id':str(session_id)})
    orm.execute(text('''INSERT INTO public.cc_input_heads(session_id,revision_id) VALUES(CAST(:id AS uuid),:revision)
      ON CONFLICT(session_id) DO UPDATE SET revision_id=EXCLUDED.revision_id'''),dict(id=str(session_id),revision=revision))
    orm.execute(text('''INSERT INTO public.cc_input_consumer_jobs(revision_id,consumer)
      VALUES(:revision,'wiki'),(:revision,'daily')'''),{'revision':revision})
    from .cc_daily_inputs import record_days
    record_days(orm,revision_id=revision,previous_id=previous.id if previous else None)
    # Unlike the historical best-effort read audit, this ingress provenance is
    # part of the raw/revision/usage transaction and must propagate failures.
    orm.execute(text('''INSERT INTO public.audit_logs(user_id,action,resource_type,resource_id,metadata)
      VALUES(CAST(:owner AS uuid),'ai_chat_ingest','project',:project,CAST(:meta AS jsonb))'''),dict(
        owner=str(owner_user_id),project=str(project_id),meta=json.dumps(dict(source='cc_switch',result_status='ok',
        session_id=str(session_id),input_revision_id=str(revision),input_snapshot_sha256=digest))))
    return str(revision)


def pending_wiki_inputs(orm, *, cutoff, limit):
    rows=orm.execute(text('''WITH selected AS MATERIALIZED (
      SELECT r.id,r.snapshot,r.owner_user_id FROM public.cc_input_heads h
      JOIN public.cc_input_revisions r ON r.id=h.revision_id
      JOIN public.cc_input_consumer_jobs j ON j.revision_id=r.id AND j.consumer='wiki' AND j.status='pending'
      JOIN public.ai_chat_sessions s ON s.id=r.session_id AND s.user_id=r.owner_user_id AND s.project_id=r.project_id
      JOIN public.users u ON u.id=r.owner_user_id AND u.is_active IS TRUE
      JOIN public.project_members pm ON pm.project_id=r.project_id AND pm.user_id=r.owner_user_id
      WHERE r.content_complete IS TRUE AND r.previously_seen_payload IS FALSE
        AND (r.snapshot->'session'->>'started_at')::timestamptz<:cutoff
      ORDER BY (r.snapshot->'session'->>'started_at')::timestamptz,r.id LIMIT :limit)
      SELECT id,owner_user_id,CASE WHEN sum(octet_length(snapshot::text)) OVER ()<=8388608
        THEN snapshot END AS snapshot FROM selected'''),dict(cutoff=cutoff,limit=min(max(int(limit),1),32))).all()
    if any(row.snapshot is None for row in rows):
        raise ValueError('CC pending input snapshot budget exceeded')
    return rows


def _validate_wiki_input(orm, revision_id):
    if not enabled():
        raise ValueError('CC input changed: revision consumer disabled')
    revision=orm.execute(text('SELECT * FROM public.cc_input_revisions WHERE id=CAST(:id AS uuid)'),{'id':str(revision_id)}).mappings().one()
    params=dict(id=revision['session_id'],revision=revision['id'],owner=revision['owner_user_id'],project=revision['project_id'])
    orm.execute(text('SELECT id FROM public.ai_chat_sessions WHERE id=:id FOR SHARE'),params).one()
    head=orm.execute(text('SELECT revision_id FROM public.cc_input_heads WHERE session_id=:id FOR SHARE'),params).scalar_one()
    _,digest=_raw_snapshot(orm,revision['session_id'])
    membership=orm.execute(text('''SELECT pm.user_id FROM public.project_members pm JOIN public.users u ON u.id=pm.user_id
      WHERE pm.user_id=:owner AND pm.project_id=:project AND u.is_active IS TRUE FOR SHARE OF pm,u'''),params).first()
    job=orm.execute(text("SELECT status FROM public.cc_input_consumer_jobs WHERE revision_id=:revision AND consumer='wiki' FOR UPDATE"),params).scalar_one()
    if (head!=revision['id'] or digest!=revision['snapshot_sha256'] or not revision['content_complete']
        or revision['previously_seen_payload']
        or membership is None or job!='pending'):
        raise ValueError('CC input changed during generation or is no longer authorized/pending')


def fence_wiki_input(orm, revision_id, attempt_id=None):
    _validate_wiki_input(orm,revision_id)
    current=orm.execute(text('''SELECT c.attempt_id FROM public.cc_wiki_claims c
      JOIN public.cc_wiki_attempts a ON a.id=c.attempt_id
      WHERE c.revision_id=CAST(:id AS uuid) AND c.attempt_id=CAST(:attempt AS uuid)
        AND a.lease_until>clock_timestamp() FOR UPDATE OF c'''),
      dict(id=str(revision_id),attempt=attempt_id)).first()
    if current is None:
        raise ValueError('CC input changed: model claim expired or superseded')


def acknowledge_wiki_input(orm, *, revision_id, publications, attempt_id=None):
    fence_wiki_input(orm,revision_id,attempt_id)
    orm.execute(text('''INSERT INTO public.member_wiki_cc_input_receipts(revision_id,publications)
      VALUES(CAST(:id AS uuid),CAST(:publications AS jsonb))'''),dict(id=str(revision_id),publications=json.dumps(publications)))
    orm.execute(text("UPDATE public.cc_input_consumer_jobs SET status='consumed',updated_at=now() WHERE revision_id=CAST(:id AS uuid) AND consumer='wiki'"),{'id':str(revision_id)})
