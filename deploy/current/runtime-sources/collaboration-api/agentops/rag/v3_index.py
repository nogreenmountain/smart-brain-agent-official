"""Idempotent writer for the append-only RAG v3 shadow index.

The first production slice deliberately derives from the already approved v2
chunks.  It adds document context, source locators and neighbor links without
re-parsing or rewriting the v2 fact table.  A later parser-specific worker can
replace this source while keeping the same shadow contract.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import uuid
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from agentops.rag import config
from agentops.rag.model_clients import EmbeddingServiceClient

PARSER_VERSION = "v3-from-v2-2026-08-28"
CHUNKER_VERSION = "contextual-v1"
RETRIEVAL_VERSION = "v3-shadow"


@dataclass(frozen=True)
class ShadowRow:
    document_id: uuid.UUID
    project_id: uuid.UUID
    source_type: str
    source_locator: str | None
    page: int | None
    chunk_index: int
    heading_path: str | None
    parser_version: str
    chunker_version: str
    retrieval_version: str
    original_text: str
    contextual_prefix: str
    content_hash: str
    embedding: list[float] | None = None
    embedding_model: str | None = None
    embedding_version: str | None = None
    previous_chunk_id: uuid.UUID | None = None
    next_chunk_id: uuid.UUID | None = None


def _value(row: Mapping[str, object] | object, key: str, default=None):
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)


def _uuid(value: object | None) -> uuid.UUID:
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


def make_shadow_rows(rows: Iterable[Mapping[str, object] | object]) -> list[ShadowRow]:
    """Convert ordered v2 rows into deterministic shadow rows.

    Input rows must be ordered by ``document_id, chunk_index``.  Neighbor
    references are based on the source chunk UUID, so retries produce the same
    links and do not require a second pass over the shadow table.
    """
    result: list[ShadowRow] = []
    previous_by_document: dict[uuid.UUID, uuid.UUID] = {}
    pending_next: dict[uuid.UUID, int] = {}
    for raw in rows:
        text = str(_value(raw, "content", "") or "")
        if not text.strip():
            continue
        document_id = _uuid(_value(raw, "document_id"))
        project_id = _uuid(_value(raw, "project_id"))
        chunk_id = _uuid(_value(raw, "id"))
        filename = str(_value(raw, "filename", "") or "").strip()
        heading_path = str(_value(raw, "heading_path", "") or "").strip() or None
        source_type = str(_value(raw, "format", "unknown") or "unknown").lower()
        page = _value(raw, "source_page")
        page = int(page) if page is not None else None
        chunk_index = int(_value(raw, "chunk_index", 0) or 0)
        locator = f"page:{page}" if page is not None else f"chunk:{chunk_index}"
        prefix = "\n".join(part for part in (filename, heading_path) if part)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        row = ShadowRow(
            document_id=document_id,
            project_id=project_id,
            source_type=source_type,
            source_locator=locator,
            page=page,
            chunk_index=chunk_index,
            heading_path=heading_path,
            parser_version=PARSER_VERSION,
            chunker_version=CHUNKER_VERSION,
            retrieval_version=RETRIEVAL_VERSION,
            original_text=text,
            contextual_prefix=prefix,
            content_hash=content_hash,
            previous_chunk_id=previous_by_document.get(document_id),
        )
        if document_id in previous_by_document:
            prior_index = pending_next[document_id]
            result[prior_index] = ShadowRow(**{**result[prior_index].__dict__, "next_chunk_id": chunk_id})
        result.append(row)
        pending_next[document_id] = len(result) - 1
        previous_by_document[document_id] = chunk_id
    return result


SELECT_SOURCE_ROWS = """
WITH preferred AS (
    SELECT c.id, c.document_id, c.project_id, c.chunk_index, c.content,
           c.source_page, c.heading_path, d.filename, d.format
    FROM public.document_chunks_v2 c
    JOIN public.documents d ON d.id = c.document_id
    WHERE d.status = 'ready'
      AND COALESCE(d.is_current, true) = true
      AND COALESCE(d.version_conflict, false) = false
      AND (%(project_id)s::uuid IS NULL OR c.project_id = %(project_id)s::uuid)
), legacy AS (
    SELECT c.id, c.document_id, c.project_id, c.chunk_index, c.content,
           c.source_page, NULL::text AS heading_path, d.filename, d.format
    FROM public.document_chunks c
    JOIN public.documents d ON d.id = c.document_id
    WHERE d.status = 'ready'
      AND COALESCE(d.is_current, true) = true
      AND COALESCE(d.version_conflict, false) = false
      AND (%(project_id)s::uuid IS NULL OR c.project_id = %(project_id)s::uuid)
      AND NOT EXISTS (
          SELECT 1
          FROM public.document_chunks_v2 v2
          WHERE v2.document_id = c.document_id
            AND v2.chunk_index = c.chunk_index
      )
)
SELECT id, document_id, project_id, chunk_index, content,
       source_page, heading_path, filename, format
FROM (
    SELECT * FROM preferred
    UNION ALL
    SELECT * FROM legacy
) source_rows
ORDER BY document_id, chunk_index
LIMIT %(limit)s OFFSET %(offset)s
"""

INSERT_SHADOW_ROW = """
INSERT INTO public.document_chunks_v3_shadow (
    document_id, project_id, source_type, source_locator, page, heading_path, chunk_index,
    previous_chunk_id, next_chunk_id, parser_version, chunker_version,
    retrieval_version, original_text, contextual_prefix, content_hash,
    embedding_model, embedding_version, embedding
) VALUES (
    %(document_id)s, %(project_id)s, %(source_type)s, %(source_locator)s,
    %(page)s, %(heading_path)s, %(chunk_index)s, %(previous_chunk_id)s, %(next_chunk_id)s,
    %(parser_version)s, %(chunker_version)s, %(retrieval_version)s,
    %(original_text)s, %(contextual_prefix)s, %(content_hash)s,
    %(embedding_model)s, %(embedding_version)s,
    CAST(%(embedding)s AS vector(1024))
)
ON CONFLICT (document_id, retrieval_version, chunker_version, parser_version, chunk_index)
DO UPDATE SET
    project_id = EXCLUDED.project_id,
    source_locator = EXCLUDED.source_locator,
    page = EXCLUDED.page,
    heading_path = EXCLUDED.heading_path,
    chunk_index = EXCLUDED.chunk_index,
    previous_chunk_id = EXCLUDED.previous_chunk_id,
    next_chunk_id = EXCLUDED.next_chunk_id,
    original_text = EXCLUDED.original_text,
    contextual_prefix = EXCLUDED.contextual_prefix,
    content_hash = EXCLUDED.content_hash,
    embedding_model = EXCLUDED.embedding_model,
    embedding_version = EXCLUDED.embedding_version,
    embedding = EXCLUDED.embedding,
    updated_at = now()
"""


def _vector_literal(vector: list[float] | None) -> str | None:
    if vector is None:
        return None
    return "[" + ",".join(format(float(value), ".10g") for value in vector) + "]"


def index_shadow(
    connection,
    *,
    project_id: str | None = None,
    limit: int = 1000,
    offset: int = 0,
    apply: bool = False,
) -> dict[str, int | bool]:
    """Preview or write a bounded v3 shadow batch using a DB-API connection."""
    if limit < 1 or limit > 100_000:
        raise ValueError("limit must be between 1 and 100000")
    if offset < 0:
        raise ValueError("offset must be non-negative")
    with connection.cursor() as cursor:
        cursor.execute(
            SELECT_SOURCE_ROWS,
            {"project_id": project_id, "limit": limit, "offset": offset},
        )
        source_rows = cursor.fetchall()
        if source_rows and not isinstance(source_rows[0], Mapping):
            columns = []
            for description in cursor.description or []:
                name = getattr(description, "name", None)
                columns.append(name or description[0])
            source_rows = [dict(zip(columns, row)) for row in source_rows]
    shadow_rows = make_shadow_rows(source_rows)
    if not apply:
        return {"source_rows": len(source_rows), "shadow_rows": len(shadow_rows), "applied": False}

    embeddings = EmbeddingServiceClient().embed_documents(
        [f"{row.contextual_prefix}\n\n{row.original_text}" if row.contextual_prefix else row.original_text
         for row in shadow_rows]
    )
    if len(embeddings) != len(shadow_rows):
        raise RuntimeError("embedding service returned the wrong number of v3 vectors")
    embedding_model = config.RAG_V2_EMBEDDING_MODEL
    embedding_version = config.RAG_V2_EMBEDDING_VERSION
    with connection.cursor() as cursor:
        for row, embedding in zip(shadow_rows, embeddings, strict=True):
            values = dict(row.__dict__)
            values.update(
                embedding=_vector_literal(embedding),
                embedding_model=embedding_model,
                embedding_version=embedding_version,
            )
            cursor.execute(INSERT_SHADOW_ROW, values)
    connection.commit()
    return {
        "source_rows": len(source_rows),
        "shadow_rows": len(shadow_rows),
        "embedding_rows": len(embeddings),
        "applied": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--apply", action="store_true", help="write the v3 shadow table")
    args = parser.parse_args(argv)
    if os.getenv("RAG_V3_ENABLED", "false").lower() not in {"1", "true", "yes", "on"}:
        print("RAG_V3_ENABLED=false; no v3 rows will be written.")
        return 0
    if not args.apply:
        print("preview mode; pass --apply only after the shadow schema and backup gate pass")
    import psycopg

    database_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL or SUPABASE_DATABASE_URL is required")
    with psycopg.connect(database_url) as connection:
        print(index_shadow(
            connection,
            project_id=args.project_id,
            limit=args.limit,
            offset=args.offset,
            apply=args.apply,
        ))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
