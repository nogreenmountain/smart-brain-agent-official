"""Bound immutable Gateway response bodies before database transfer.

This module is intentionally self-contained. Daily-report authorization is a
separate feature and must not be an import-time dependency of the personal
gateway API (the production image does not ship that optional module).
"""

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
READABLE_SQL = """a.delivered_at IS NOT NULL AND a.event_sha256 IS NOT NULL
            AND jsonb_typeof(a.event_payload)='object'"""
