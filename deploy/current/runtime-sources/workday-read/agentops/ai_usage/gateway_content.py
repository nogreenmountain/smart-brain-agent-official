"""Bound immutable Gateway response bodies before database transfer."""
from . import daily_access

INLINE_MESSAGE_BYTES = 2 * 1024 * 1024
PAGE_MESSAGE_BYTES = 4 * 1024 * 1024
CONTENT_FRAGMENT_CHARACTERS = 16384

# Explicit projection excludes unbounded raw_usage/usage and message metadata.
METADATA_SQL = "jsonb_build_object(" + ",".join(
    "'%s',a.event_payload->'%s'" % (key, key) for key in (
        'title','conversation_id','project_id','content_complete','context_source',
        'request_message_count','model','resolved_model','requested_model')) + ")"
MESSAGE_TEXT_SQL = "COALESCE(a.event_payload->'messages','[]'::jsonb)::text"
MESSAGE_BYTES_SQL = "octet_length(" + MESSAGE_TEXT_SQL + ")"
READABLE_SQL = f"""a.delivered_at IS NOT NULL AND a.event_sha256 IS NOT NULL
            AND jsonb_typeof(a.event_payload)='object' AND a.event_payload ? 'project_id'
            AND EXISTS (SELECT 1 FROM {daily_access.OWNER_FROM_SQL}
                WHERE owner_profile.id=e.user_id AND {daily_access.OWNER_FILTER_SQL}
                AND (a.event_payload->>'project_id' IS NULL OR EXISTS (
                    SELECT 1 FROM public.projects source_project
                    JOIN public.project_members source_owner ON source_owner.project_id=source_project.id
                    WHERE source_project.id::text=a.event_payload->>'project_id'
                      AND source_owner.user_id=e.user_id
                      AND (viewer.id=e.user_id OR viewer.is_system_admin IS TRUE OR EXISTS (
                        SELECT 1 FROM public.project_members source_admin
                        JOIN public.user_orgs source_org ON source_org.user_id=source_admin.user_id
                          AND source_org.org_id=source_project.org_id
                        WHERE source_admin.project_id=source_project.id AND source_admin.user_id=viewer.id
                          AND source_admin.role::text IN ('owner','admin')
                          AND source_org.role::text IN ('owner','admin')
                      ))
                ))
            )"""
