"""Register an explicitly reviewed origin snapshot in the caller's transaction.

This does not discover owners, adopt Wikis, commit, or enable legacy publishing.
The database validates the supplied manifest against recorded ingest provenance.
"""
import json
import re
import uuid
from sqlalchemy import text


def freeze_source(orm, *, origin_snapshot, origin_sha256):
    if not isinstance(origin_snapshot, dict) or not re.fullmatch(r'[0-9a-f]{64}', str(origin_sha256)):
        raise ValueError('Wiki legacy scope requires an audited snapshot and hash')
    values={key:str(uuid.UUID(str(origin_snapshot[key]))) for key in ('session_id','owner_user_id','project_id')}
    values.update(source=origin_snapshot['source'],snapshot=json.dumps(origin_snapshot,ensure_ascii=False),digest=origin_sha256)
    orm.execute(text('''INSERT INTO public.member_wiki_legacy_source_scopes
        (session_id,owner_user_id,project_id,source,origin_snapshot,origin_sha256)
        VALUES (CAST(:session_id AS uuid),CAST(:owner_user_id AS uuid),CAST(:project_id AS uuid),
          :source,CAST(:snapshot AS jsonb),:digest) ON CONFLICT(session_id) DO NOTHING'''),values)
    # ON CONFLICT also handles concurrent identical registration; a different
    # winner must not be silently accepted after the INSERT trigger's snapshot.
    match=orm.execute(text('''SELECT 1 FROM public.member_wiki_legacy_source_scopes
        WHERE session_id=CAST(:session_id AS uuid) AND owner_user_id=CAST(:owner_user_id AS uuid)
          AND project_id=CAST(:project_id AS uuid) AND source=:source
          AND origin_snapshot=CAST(:snapshot AS jsonb) AND origin_sha256=:digest'''),values).first()
    if match is None:
        raise ValueError('Wiki legacy scope is immutable; conflicting registration')
