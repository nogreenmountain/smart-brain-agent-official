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
from agentops.rag.v3_retrieval import should_rerank

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
    slide: int | None = None
    sheet: str | None = None
    cell_range: str | None = None
    source_locator: str | None = None


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
    version = config.effective_retrieval_version(retrieval_version, project_id=project_id)
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
    """Read the append-only v3 shadow index with dense + lexical fusion.

    ACL and current-document filters are applied before scoring.  Embeddings
    are optional per row during backfill; rows without a vector remain
    searchable through the lexical channel until the index job catches up.
    Any schema/index/model failure is isolated to this path and falls back to
    the existing v2 hybrid search.
    """
    try:
        query_embedding = EmbeddingServiceClient(timeout_seconds=5).embed_query(query)
        query_embedding_literal = "[" + ",".join(
            format(float(value), ".10g") for value in query_embedding
        ) + "]"
    except ModelServiceError:
        logger.warning("RAG v3 embedding unavailable; using lexical shadow channel")
        query_embedding_literal = None
    stmt = text(
        """
        WITH scored AS (
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
                ts_rank(c.content_tsv, plainto_tsquery('simple', :fts_query)) AS keyword_score,
                CASE WHEN position(lower(d.filename) in lower(:raw_query)) > 0
                       OR position(lower(:raw_query) in lower(d.filename)) > 0
                     THEN 1.0 ELSE 0.0 END AS filename_match_score,
                CASE WHEN c.embedding IS NULL THEN NULL
                     ELSE 1 - (c.embedding <=> CAST(:query_embedding AS vector(1024)))
                END AS dense_score,
                c.embedding_model,
                c.embedding_version,
                c.chunk_index,
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
              AND (c.content_tsv @@ plainto_tsquery('simple', :fts_query)
                   OR c.embedding IS NOT NULL)
        ), ranked AS (
            SELECT scored.*,
                (0.55 * COALESCE(dense_score, 0.0) +
                 0.35 * COALESCE(keyword_score, 0.0) +
                 0.10 * filename_match_score) AS fused_score,
                ROW_NUMBER() OVER (
                    PARTITION BY scored.document_id
                    ORDER BY (0.55 * COALESCE(dense_score, 0.0) +
                              0.35 * COALESCE(keyword_score, 0.0) +
                              0.10 * filename_match_score) DESC,
                             scored.chunk_index ASC
                ) AS document_rank
            FROM scored
        )
        SELECT *
        FROM ranked
        WHERE document_rank <= 2
        ORDER BY fused_score DESC, document_id, chunk_index
        LIMIT :limit
        """
    )
    try:
        rows = orm.execute(
            stmt,
            {
                "project_id": str(project_id),
                "fts_query": preprocess_shadow_fts_text(query),
                "raw_query": query,
                "query_embedding": query_embedding_literal,
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
        score = float(value(row, "fused_score", 0.0) or 0.0)
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
                slide=value(row, "slide"),
                sheet=value(row, "sheet"),
                cell_range=value(row, "cell_range"),
                source_locator=value(row, "source_locator"),
                retrieval_mode="v3-shadow",
                vector_score=(float(value(row, "dense_score"))
                              if value(row, "dense_score") is not None else None),
                keyword_score=(float(value(row, "keyword_score"))
                               if value(row, "keyword_score") is not None else None),
                embedding_model=value(row, "embedding_model"),
                embedding_version=value(row, "embedding_version"),
            )
        )
    if not hits:
        logger.warning("RAG v3 shadow returned no candidates; falling back to v2")
        fallback_hits = _search_v2_hybrid(
            orm,
            query=query,
            project_id=project_id,
            k=k,
            use_reranker=False,
        )
        for hit in fallback_hits:
            hit.retrieval_mode = "v2-fallback"
        return fallback_hits[:k]
    if (
        config.RAG_V3_SELECTIVE_RERANK_ENABLED
        and should_rerank(
            query,
            candidate_count=len(hits),
            cross_document=len({hit.document_id for hit in hits}) > 1,
        )
        and hits
    ):
        try:
            reranked = rerank_or_keep(query, hits, RerankerClient())
            for hit in reranked:
                hit.retrieval_mode = "v3-shadow-rerank"
            return reranked[:k]
        except ModelServiceError:
            logger.warning("RAG v3 reranker unavailable; keeping dense/lexical order")
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
