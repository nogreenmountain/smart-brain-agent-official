"""Persist the processing protocol independently of deployment feature flags."""
from __future__ import annotations

import os
from sqlalchemy import text

PROTOCOL = 'cc-input-v1'


def enabled():
    return os.getenv('SB_CC_INPUT_REVISIONS_ENABLED', 'false').lower() == 'true'


def installed(orm):
    return orm.execute(text("SELECT to_regclass('public.cc_queued_input_contracts') IS NOT NULL")).scalar_one()


def declare_claim_protocol(orm):
    # Transaction-local: a pooled connection must not lend this declaration to
    # a later old reader. This is compatibility fencing, not authentication.
    orm.execute(text("SELECT set_config('smartbrain.cc_queue_protocol', :protocol, true)"),
        {'protocol':PROTOCOL})


def intake_protocol(orm):
    present = installed(orm)
    if present and not enabled():
        raise RuntimeError('CC intake disabled')
    if present and enabled() and not completion_schema_installed(orm):
        raise RuntimeError('CC completion migration required')
    return PROTOCOL if present and enabled() else None


def mode(orm, receipt_id):
    if not installed(orm):
        return 'legacy'
    row = orm.execute(text('''SELECT q.stream,q.payload,q.status,c.protocol
        FROM public.ingest_queue_receipts q LEFT JOIN public.cc_queued_input_contracts c
        ON c.receipt_id=q.id WHERE q.id=CAST(:id AS uuid)'''), {'id':str(receipt_id)}).first()
    if row is None:
        return 'complete'
    if row.status == 'synced':
        return 'complete' if row.protocol is None or has_completion(orm,receipt_id) else 'deferred'
    if row.protocol is not None:
        return PROTOCOL if row.protocol == PROTOCOL and enabled() and completion_schema_installed(orm) else 'deferred'
    if row.stream == 'ai-chat' and row.payload.get('source') == 'cc_switch':
        return 'deferred'
    return 'legacy'


def register(orm, receipt_id):
    if not completion_schema_installed(orm):
        raise RuntimeError('CC completion migration required')
    orm.execute(text('''INSERT INTO public.cc_queued_input_contracts
        (receipt_id,protocol,owner_user_id,project_id,payload_fingerprint,payload_sha256,claims_sha256)
        SELECT id,'cc-input-v1',CAST(claims->>'sub' AS uuid),CAST(claims->>'project_id' AS uuid),
          payload_fingerprint,encode(sha256(convert_to(payload::text,'UTF8')),'hex'),
          encode(sha256(convert_to(claims::text,'UTF8')),'hex')
        FROM public.ingest_queue_receipts WHERE id=CAST(:id AS uuid)'''), {'id':str(receipt_id)})


def verify_replay(orm, receipt_id, *, payload_json, claims):
    valid = orm.execute(text('''SELECT c.receipt_id,q.status FROM public.cc_queued_input_contracts c
        JOIN public.ingest_queue_receipts q ON q.id=c.receipt_id
        WHERE c.receipt_id=CAST(:id AS uuid) AND c.protocol='cc-input-v1'
          AND c.owner_user_id=CAST(:owner AS uuid) AND c.project_id=CAST(:project AS uuid)
          AND c.payload_sha256=encode(sha256(convert_to(CAST(:payload AS jsonb)::text,'UTF8')),'hex')
          AND q.payload_fingerprint=c.payload_fingerprint AND q.status<>'dead_letter'
        FOR SHARE OF q'''), {'id':str(receipt_id), 'owner':str(claims['sub']),
            'project':str(claims['project_id']), 'payload':payload_json}).first()
    if valid is None:
        raise RuntimeError('CC queued replay requires the original registered contract')
    if valid.status == 'synced' and not has_completion(orm,receipt_id):
        raise RuntimeError('CC queued replay has no verified completion')


def completion_schema_installed(orm):
    return orm.execute(text("SELECT to_regclass('public.cc_queued_input_completions') IS NOT NULL")).scalar_one()


def has_completion(orm, receipt_id):
    if not completion_schema_installed(orm):
        return False
    return orm.execute(text('''SELECT EXISTS(SELECT 1 FROM public.cc_queued_input_completions x
        JOIN public.cc_queued_input_contracts c ON c.receipt_id=x.receipt_id
        JOIN public.cc_input_revisions r ON r.id=x.revision_id
        WHERE x.receipt_id=CAST(:id AS uuid) AND x.protocol=c.protocol
          AND x.owner_user_id=c.owner_user_id AND x.project_id=c.project_id
          AND x.owner_user_id=r.owner_user_id AND x.project_id=r.project_id
          AND x.session_id=r.session_id AND x.result_snapshot_sha256=r.snapshot_sha256
          AND x.content_fingerprint=r.content_fingerprint AND x.input_payload_sha256=c.payload_sha256)'''),
        {'id':str(receipt_id)}).scalar_one()


def record_completion(orm, *, receipt_id, revision_id, fingerprint):
    row = orm.execute(text('''INSERT INTO public.cc_queued_input_completions
        (receipt_id,protocol,owner_user_id,project_id,session_id,revision_id,claim_token,
         input_payload_sha256,content_fingerprint,result_snapshot_sha256)
        SELECT c.receipt_id,c.protocol,c.owner_user_id,c.project_id,r.session_id,r.id,q.claim_token,
          c.payload_sha256,:fingerprint,r.snapshot_sha256
        FROM public.cc_queued_input_contracts c JOIN public.ingest_queue_receipts q ON q.id=c.receipt_id
        JOIN public.cc_input_revisions r ON r.id=CAST(:revision AS uuid)
        WHERE c.receipt_id=CAST(:id AS uuid) RETURNING receipt_id'''),
        {'id':str(receipt_id),'revision':str(revision_id),'fingerprint':fingerprint}).first()
    if row is None:
        raise RuntimeError('CC completion requires its registered input')


def verify_pending(orm, receipt_id):
    valid = orm.execute(text('''SELECT q.id FROM public.ingest_queue_receipts q
        JOIN public.cc_queued_input_contracts c ON c.receipt_id=q.id
        WHERE q.id=CAST(:id AS uuid) AND c.protocol='cc-input-v1' AND q.stream='ai-chat'
          AND q.payload->>'source'='cc_switch'
          AND q.payload->>'project_id'=c.project_id::text
          AND q.claims->>'sub'=c.owner_user_id::text AND q.claims->>'project_id'=c.project_id::text
          AND q.payload_fingerprint=c.payload_fingerprint
          AND c.payload_sha256=encode(sha256(convert_to(q.payload::text,'UTF8')),'hex')
          AND c.claims_sha256=encode(sha256(convert_to(q.claims::text,'UTF8')),'hex')
        '''), {'id':str(receipt_id)}).first()
    if valid is None:
        raise RuntimeError('CC queued durable input changed')


def poll_filter(orm):
    if not installed(orm):
        return ''
    allowed = " OR EXISTS (SELECT 1 FROM public.cc_queued_input_contracts c WHERE c.receipt_id=q.id)" if enabled() else ''
    return " AND ((q.stream<>'ai-chat' OR q.payload->>'source' IS DISTINCT FROM 'cc_switch')" + allowed + ')'


def cleanup_filter(orm):
    if not installed(orm):
        return ''
    return ' AND NOT EXISTS (SELECT 1 FROM public.cc_queued_input_contracts c WHERE c.receipt_id=ingest_queue_receipts.id)'
