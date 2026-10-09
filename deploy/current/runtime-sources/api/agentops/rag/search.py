"""Search for the RAG knowledge base.

v1 is the original 384-dim pgvector search.
v2 adds BGE-M3 embeddings, PostgreSQL FTS, RRF fusion, and optional reranking.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import List

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from agentops.rag import config
from agentops.rag.hybrid import (
    preprocess_fts_text,
    preprocess_shadow_fts_text,
    reciprocal_rank_fusion,
    rerank_or_keep,
)
from agentops.rag.model_clients import EmbeddingServiceClient, ModelServiceError, RerankerClient

logger = logging.getLogger(__name__)


@dataclass
class SearchHit:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content: str
    source_page: int | None
    source_line: int | None
    chunk_index: int
    score: float
    heading_path: str | None = None
    retrieval_mode: str | None = None
    vector_score: float | None = None
    keyword_score: float | None = None
    vector_rank: int | None = None
    keyword_rank: int | None = None
    rrf_score: float | None = None
    rerank_score: float | None = None
    embedding_model: str | None = None
    embedding_version: str | None = None


def search(
    orm: Session,
    *,
    query: str,
    project_id: uuid.UUID,
    k: int = 5,
    retrieval_version: str | None = None,
) -> List[SearchHit]:
    """Return the top-k chunks restricted to the given project."""
    if not query.strip():
        return []
    version = config.effective_retrieval_version(retrieval_version)
    if version == "v1":
        return _search_v1(orm, query=query, project_id=project_id, k=k)

    try:
        if version == "v3-shadow":
            return _search_v3_shadow(orm, query=query, project_id=project_id, k=k)
        if version == "v2-vector":
            return _search_v2_vector(orm, query=query, project_id=project_id, k=k)
        if version == "v2-hybrid":
            return _search_v2_hybrid(
                orm,
                query=query,
                project_id=project_id,
                k=k,
                use_reranker=False,
            )
        if version == "v2-hybrid-rerank":
            return _search_v2_hybrid(
                orm,
                query=query,
                project_id=project_id,
                k=k,
                use_reranker=True,
            )
    except ModelServiceError:
        logger.exception("RAG v2 model service failed")
        if config.RAG_V2_FALLBACK_TO_V1:
            hits = _search_v1(orm, query=query, project_id=project_id, k=k)
            for hit in hits:
                hit.retrieval_mode = "v1-fallback"
            return hits
        raise

    raise ValueError(f"retrieval version is configured but not implemented: {version}")


def _search_v1(
    orm: Session,
    *,
    query: str,
    project_id: uuid.UUID,
    k: int,
) -> List[SearchHit]:
    # Keep pgvector/ORM imports off the v3 shadow read path.  This also makes
    # the lexical shadow index independently testable in lightweight workers.
    from agentops.rag.db import Document, DocumentChunk

    from agentops.rag.embed import embed_query

    qvec = embed_query(query)
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.content,
            DocumentChunk.source_page,
            DocumentChunk.source_line,
            DocumentChunk.embedding.cosine_distance(qvec).label("distance"),
            Document.filename,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.project_id == project_id)
        .where(Document.status == "ready")
        .where((Document.is_current.is_(None)) | (Document.is_current.is_(True)))
        .where((Document.version_conflict.is_(None)) | (Document.version_conflict.is_(False)))
        .order_by("distance")
        .limit(k)
    )
    rows = orm.execute(stmt).all()
    hits = []
    for idx, r in enumerate(rows, start=1):
        score = float(1.0 - r.distance)
        hits.append(SearchHit(
            chunk_id=r.id,
            document_id=r.document_id,
            document_name=r.filename,
            content=r.content,
            source_page=r.source_page,
            source_line=r.source_line,
            chunk_index=r.chunk_index,
            score=score,
            retrieval_mode="v1",
            vector_score=score,
            vector_rank=idx,
        ))
    return hits


def _search_v2_vector(
    orm: Session,
    *,
    query: str,
    project_id: uuid.UUID,
    k: int,
    limit_override: int | None = None,
) -> List[SearchHit]:
    from agentops.rag.db import Document, DocumentChunkV2

    qvec = EmbeddingServiceClient().embed_query(query)
    limit = limit_override or k
    stmt = (
        select(
            DocumentChunkV2.id,
            DocumentChunkV2.document_id,
            DocumentChunkV2.chunk_index,
            DocumentChunkV2.content,
            DocumentChunkV2.source_page,
            DocumentChunkV2.source_line,
            DocumentChunkV2.heading_path,
            DocumentChunkV2.embedding_model,
            DocumentChunkV2.embedding_version,
            DocumentChunkV2.embedding.cosine_distance(qvec).label("distance"),
            Document.filename,
        )
        .join(Document, Document.id == DocumentChunkV2.document_id)
        .where(DocumentChunkV2.project_id == project_id)
        .where(Document.status == "ready")
        .where((Document.is_current.is_(None)) | (Document.is_current.is_(True)))
        .where((Document.version_conflict.is_(None)) | (Document.version_conflict.is_(False)))
        .where(DocumentChunkV2.embedding_model == config.RAG_V2_EMBEDDING_MODEL)
        .where(DocumentChunkV2.embedding_version == config.RAG_V2_EMBEDDING_VERSION)
        .order_by("distance")
        .limit(limit)
    )
    rows = orm.execute(stmt).all()
    hits = []
    for idx, r in enumerate(rows, start=1):
        score = float(1.0 - r.distance)
        hits.append(SearchHit(
            chunk_id=r.id,
            document_id=r.document_id,
            document_name=r.filename,
            content=r.content,
            source_page=r.source_page,
            source_line=r.source_line,
            chunk_index=r.chunk_index,
            score=score,
            heading_path=r.heading_path,
            retrieval_mode="v2-vector",
            vector_score=score,
            vector_rank=idx,
            embedding_model=r.embedding_model,
            embedding_version=r.embedding_version,
        ))
    return hits


def _search_v2_keyword(
    orm: Session,
    *,
    query: str,
    project_id: uuid.UUID,
    limit: int,
) -> List[SearchHit]:
    fts_query = preprocess_fts_text(query)
    stmt = text(
        """
        SELECT
            c.id,
            c.document_id,
            c.chunk_index,
            c.content,
            c.source_page,
            c.source_line,
            c.heading_path,
            c.embedding_model,
            c.embedding_version,
            d.filename,
            ts_rank(c.content_tsv, plainto_tsquery('simple', :fts_query)) AS keyword_score
        FROM public.document_chunks_v2 c
        JOIN public.documents d ON d.id = c.document_id
        WHERE c.project_id = :project_id
          AND d.status = 'ready'
          AND COALESCE(d.is_current, true) = true
          AND COALESCE(d.version_conflict, false) = false
          AND c.embedding_model = :embedding_model
          AND c.embedding_version = :embedding_version
          AND c.content_tsv @@ plainto_tsquery('simple', :fts_query)
        ORDER BY keyword_score DESC, c.created_at ASC
        LIMIT :limit
        """
    )
    rows = orm.execute(
        stmt,
        {
            "project_id": str(project_id),
            "fts_query": fts_query,
            "embedding_model": config.RAG_V2_EMBEDDING_MODEL,
            "embedding_version": config.RAG_V2_EMBEDDING_VERSION,
            "limit": limit,
        },
    ).mappings().all()
    hits = []
    for idx, r in enumerate(rows, start=1):
        score = float(r["keyword_score"] or 0.0)
        hits.append(SearchHit(
            chunk_id=r["id"],
            document_id=r["document_id"],
            document_name=r["filename"],
            content=r["content"],
            source_page=r["source_page"],
            source_line=r["source_line"],
            chunk_index=r["chunk_index"],
            score=score,
            heading_path=r["heading_path"],
            retrieval_mode="v2-keyword",
            keyword_score=score,
            keyword_rank=idx,
            embedding_model=r["embedding_model"],
            embedding_version=r["embedding_version"],
        ))
    return hits


def _search_v3_shadow(
    orm: Session,
    *,
    query: str,
    project_id: uuid.UUID,
    k: int,
) -> List[SearchHit]:
    """Read the append-only v3 shadow index without changing v2 behavior.

    The first v3 slice intentionally uses the generated FTS column.  It
    enforces project ACL and ready-document filtering in SQL, limits chunks
    per document for diversity, and keeps source/heading metadata needed by
    evidence citations.  Any schema/index/model failure is isolated to this
    path and falls back to the existing v2 hybrid search.
    """
    stmt = text(
        """
        WITH ranked AS (
            SELECT
                c.id,
                c.document_id,
                c.project_id,
                d.filename,
                c.original_text,
                c.content,
                c.source_locator,
                c.page,
                c.slide,
                c.sheet,
                c.cell_range,
                c.heading_path,
                ROW_NUMBER() OVER (
                    PARTITION BY c.document_id
                    ORDER BY ts_rank(c.content_tsv, plainto_tsquery('simple', :fts_query)) DESC,
                             c.chunk_index ASC
                ) AS document_rank,
                c.chunk_index,
                ts_rank(c.content_tsv, plainto_tsquery('simple', :fts_query)) AS keyword_score,
                c.content_hash,
                c.parser_version,
                c.chunker_version
            FROM public.document_chunks_v3_shadow c
            JOIN public.documents d ON d.id = c.document_id
            WHERE c.project_id = :project_id
              AND d.status = 'ready'
              AND COALESCE(d.is_current, true) = true
              AND COALESCE(d.version_conflict, false) = false
              AND c.retrieval_version = 'v3-shadow'
              AND c.content_tsv @@ plainto_tsquery('simple', :fts_query)
        )
        SELECT *
        FROM ranked
        WHERE document_rank <= 2
        ORDER BY keyword_score DESC, document_id, chunk_index
        LIMIT :limit
        """
    )
    try:
        rows = orm.execute(
            stmt,
            {
                "project_id": str(project_id),
                "fts_query": preprocess_shadow_fts_text(query),
                "limit": k,
            },
        ).mappings().all()
    except Exception:
        logger.exception("RAG v3 shadow search failed; falling back to v2")
        hits = _search_v2_hybrid(
            orm,
            query=query,
            project_id=project_id,
            k=k,
            use_reranker=False,
        )
        for hit in hits:
            hit.retrieval_mode = "v2-fallback"
        return hits

    def value(row, key, default=None):
        try:
            return row[key]
        except (KeyError, TypeError, IndexError):
            return getattr(row, key, default)

    hits: List[SearchHit] = []
    for row in rows:
        score = float(value(row, "keyword_score", 0.0) or 0.0)
        hits.append(
            SearchHit(
                chunk_id=value(row, "id"),
                document_id=value(row, "document_id"),
                document_name=value(row, "filename", value(row, "document_id", "")),
                content=value(row, "content", value(row, "original_text", "")),
                source_page=value(row, "page"),
                source_line=None,
                chunk_index=int(value(row, "chunk_index", 0) or 0),
                score=score,
                heading_path=value(row, "heading_path"),
                retrieval_mode="v3-shadow",
                keyword_score=score,
            )
        )
    return hits


def _search_v2_hybrid(
    orm: Session,
    *,
    query: str,
    project_id: uuid.UUID,
    k: int,
    use_reranker: bool,
) -> List[SearchHit]:
    vector_hits = _search_v2_vector(
        orm,
        query=query,
        project_id=project_id,
        k=k,
        limit_override=max(config.RAG_VECTOR_TOP_K, k),
    )
    keyword_hits = _search_v2_keyword(
        orm,
        query=query,
        project_id=project_id,
        limit=max(config.RAG_KEYWORD_TOP_K, k),
    )
    fused = reciprocal_rank_fusion(
        vector_hits,
        keyword_hits,
        limit=max(config.RAG_RRF_TOP_K, k),
    )
    for hit in fused:
        hit.retrieval_mode = "v2-hybrid"

    if not use_reranker:
        return fused[:k]

    rerank_input = fused[: max(config.RAG_RRF_TOP_K, config.RAG_RERANK_TOP_K, k)]
    reranked = rerank_or_keep(query, rerank_input, RerankerClient())
    for hit in reranked:
        hit.retrieval_mode = "v2-hybrid-rerank"
    return reranked[:k]
