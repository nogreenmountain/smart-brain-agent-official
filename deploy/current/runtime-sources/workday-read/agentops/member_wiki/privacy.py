"""Source-bound ownership and live read authorization for detailed member Wikis.

No alias is an authorization credential. Old unbound content stays in its original
tables and is hidden until audited; callers must not infer a UUID from its name.
"""
import uuid
from sqlalchemy import text


SOURCE_SNAPSHOT_SQL = """(SELECT COALESCE(jsonb_agg(to_jsonb(s) ORDER BY s.session_id),'[]'::jsonb)
    FROM public.member_wiki_experience_sources s WHERE s.experience_id=wiki.id)"""

READ_FROM_SQL = """public.member_wiki_experiences wiki
    JOIN public.member_wiki_access_bindings binding ON binding.experience_id=wiki.id
        AND binding.version=wiki.current_version"""

# A broad owner/admin roster is not authority over the request's source project.
# Check every Gateway source, including a mixed-source experience, on every read.
GATEWAY_SOURCE_FILTER_SQL = """NOT EXISTS (
    SELECT 1 FROM public.member_wiki_experience_sources wiki_source
    WHERE wiki_source.experience_id=wiki.id
      AND wiki_source.source IN ('ai_gateway_personal','ai_gateway_project')
      AND NOT EXISTS (
        SELECT 1 FROM public.ai_gateway_admissions source_admission
        JOIN public.ai_gateway_events source_event ON source_event.event_id=source_admission.id::text
          AND source_event.user_id=source_admission.user_id
          AND source_event.gateway_instance_id=source_admission.gateway_instance_id
        WHERE source_admission.id=wiki_source.session_id AND source_admission.user_id=binding.owner_user_id
          AND source_admission.delivered_at IS NOT NULL AND source_admission.event_sha256 IS NOT NULL
          AND jsonb_typeof(source_admission.event_payload)='object'
          AND source_admission.event_payload ? 'project_id'
          AND source_admission.event_payload->'content_complete'='true'::jsonb
          AND source_event.status_code>=200 AND source_event.status_code<400
          AND (source_admission.event_payload->'project_id'='null'::jsonb OR EXISTS (
            SELECT 1 FROM public.projects source_project
            JOIN public.project_members source_owner ON source_owner.project_id=source_project.id
            WHERE source_project.id::text=source_admission.event_payload->>'project_id'
              AND source_owner.user_id=binding.owner_user_id
              AND (viewer.id=binding.owner_user_id OR viewer.is_system_admin IS TRUE OR EXISTS (
                SELECT 1 FROM public.project_members source_admin
                JOIN public.user_orgs source_org ON source_org.user_id=source_admin.user_id
                  AND source_org.org_id=source_project.org_id
                WHERE source_admin.project_id=source_project.id AND source_admin.user_id=viewer.id
                  AND source_admin.role::text IN ('owner','admin') AND source_org.role::text IN ('owner','admin')
              ))
          ))
      )
)"""

LEGACY_SOURCE_FILTER_SQL = """NOT EXISTS (
    SELECT 1 FROM public.member_wiki_experience_sources legacy_source
    WHERE legacy_source.experience_id=wiki.id
      AND legacy_source.source NOT IN ('ai_gateway_personal','ai_gateway_project')
      AND NOT EXISTS (
        SELECT 1 FROM public.member_wiki_legacy_source_scopes frozen
        JOIN public.projects original_project ON original_project.id=frozen.project_id
        JOIN public.project_members original_owner ON original_owner.project_id=original_project.id
          AND original_owner.user_id=frozen.owner_user_id
        WHERE frozen.session_id=legacy_source.session_id AND frozen.source=legacy_source.source
          AND frozen.owner_user_id=binding.owner_user_id
          AND (viewer.id=binding.owner_user_id OR viewer.is_system_admin IS TRUE OR EXISTS (
            SELECT 1 FROM public.project_members original_admin
            JOIN public.user_orgs original_org ON original_org.user_id=original_admin.user_id
              AND original_org.org_id=original_project.org_id
            WHERE original_admin.project_id=original_project.id AND original_admin.user_id=viewer.id
              AND original_admin.role::text IN ('owner','admin') AND original_org.role::text IN ('owner','admin')
          ))
      )
)"""

READ_FILTER_SQL = f"""binding.owner_user_id = ANY(CAST(:owner_user_ids AS uuid[]))
    AND public.member_wiki_gateway_publication_is_current(wiki.id,wiki.current_version)
    AND binding.experience_snapshot=to_jsonb(wiki)
    AND binding.source_snapshot={SOURCE_SNAPSHOT_SQL}
    AND EXISTS (
        SELECT 1 FROM public.users viewer JOIN auth.users va ON va.id=viewer.id
        JOIN public.users owner_profile ON owner_profile.id=binding.owner_user_id
        JOIN auth.users oa ON oa.id=owner_profile.id
        WHERE viewer.id=CAST(:caller_user_id AS uuid)
          AND viewer.is_active IS TRUE AND owner_profile.is_active IS TRUE
          AND {GATEWAY_SOURCE_FILTER_SQL}
          AND {LEGACY_SOURCE_FILTER_SQL}
          AND (viewer.id=binding.owner_user_id OR (
            owner_profile.ai_detail_visible_to_admin IS TRUE AND (
              (viewer.is_system_admin IS TRUE AND EXISTS (
                SELECT 1 FROM public.project_members target WHERE target.user_id=binding.owner_user_id))
              OR EXISTS (
                SELECT 1 FROM public.user_orgs caller_org
                JOIN public.projects project ON project.org_id=caller_org.org_id
                JOIN public.project_members caller ON caller.project_id=project.id
                    AND caller.user_id=caller_org.user_id
                JOIN public.project_members target ON target.project_id=project.id
                WHERE caller_org.user_id=viewer.id AND target.user_id=binding.owner_user_id
                  AND caller_org.role::text IN ('owner','admin')
                  AND caller.role::text IN ('owner','admin')
              )
            )
          ))
    )"""


def read_parameters(*, caller_user_id, owner_user_ids):
    """Only server-resolved UUIDs; absent/invalid context returns no readable rows."""
    if caller_user_id is None or not owner_user_ids:
        return None
    try:
        return dict(caller_user_id=str(uuid.UUID(str(caller_user_id))),
                    owner_user_ids=list(dict.fromkeys(str(uuid.UUID(str(value))) for value in owner_user_ids)))
    except (ValueError, TypeError, AttributeError):
        return None


def bind_experience(orm, *, experience_id, owner_user_id):
    """Snapshot and validate sources in caller's publication transaction; no commit.

    This explicit helper is not yet called by the legacy publisher. Unknown or
    mixed-owner baselines need audit; database validation refuses guessed owners.
    """
    params = dict(experience_id=str(uuid.UUID(str(experience_id))),
                  owner_user_id=str(uuid.UUID(str(owner_user_id))))
    row = orm.execute(text(f"""INSERT INTO public.member_wiki_access_bindings
        (experience_id,version,owner_user_id,experience_snapshot,source_snapshot)
        SELECT wiki.id,wiki.current_version,CAST(:owner_user_id AS uuid),to_jsonb(wiki),{SOURCE_SNAPSHOT_SQL}
        FROM public.member_wiki_experiences wiki WHERE wiki.id=CAST(:experience_id AS uuid)
        ON CONFLICT(experience_id,version) DO NOTHING RETURNING version"""), params).first()
    if row is None:
        matches = orm.execute(text(f"""SELECT 1 FROM {READ_FROM_SQL}
            WHERE wiki.id=CAST(:experience_id AS uuid) AND binding.owner_user_id=CAST(:owner_user_id AS uuid)
              AND binding.experience_snapshot=to_jsonb(wiki)
              AND binding.source_snapshot={SOURCE_SNAPSHOT_SQL}"""), params).first()
        if matches is None:
            raise ValueError('immutable Wiki access binding differs; explicit new version required')
