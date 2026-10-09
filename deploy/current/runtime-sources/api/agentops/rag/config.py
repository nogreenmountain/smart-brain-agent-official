from __future__ import annotations

import os


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


RAG_RETRIEVAL_VERSION = os.getenv("RAG_RETRIEVAL_VERSION", "v2-hybrid")

# v3 is deliberately an opt-in shadow path.  Sub-features are exposed here so
# deployments can prepare configuration without accidentally reading a v3
# index or starting a background rebuild.
RAG_V3_ENABLED = env_bool("RAG_V3_ENABLED", False)
RAG_V3_CONTEXTUAL_CHUNKS_ENABLED = env_bool("RAG_V3_CONTEXTUAL_CHUNKS_ENABLED", False)
RAG_V3_SPARSE_ENABLED = env_bool("RAG_V3_SPARSE_ENABLED", False)
RAG_V3_QUERY_PLANNER_ENABLED = env_bool("RAG_V3_QUERY_PLANNER_ENABLED", False)
RAG_V3_SELECTIVE_RERANK_ENABLED = env_bool("RAG_V3_SELECTIVE_RERANK_ENABLED", False)
RAG_V3_GRAPH_ENABLED = env_bool("RAG_V3_GRAPH_ENABLED", False)
SUPPORTED_RETRIEVAL_VERSIONS = {
    "v1", "v2-vector", "v2-hybrid", "v2-hybrid-rerank", "v3-shadow",
}


def v3_retrieval_enabled() -> bool:
    """Return whether v3 retrieval may read its independent shadow index."""
    # The master switch protects both the configured default and explicit
    # per-request ``v3-*`` selections.  An explicit shadow request is useful
    # during a project allow-list canary while the global default remains v2.
    return RAG_V3_ENABLED


def v3_indexing_enabled() -> bool:
    """Return whether background v3 indexing may be scheduled."""
    return RAG_V3_ENABLED


def effective_retrieval_version(requested: str | None = None) -> str:
    """Resolve a requested mode without ever bypassing the v3 master switch."""
    version = requested or RAG_RETRIEVAL_VERSION
    if version.startswith("v3-") and not RAG_V3_ENABLED:
        return "v2-hybrid"
    if version not in SUPPORTED_RETRIEVAL_VERSIONS:
        raise ValueError(f"unsupported RAG retrieval version: {version}")
    return version

RAG_V2_EMBEDDING_MODEL = os.getenv("RAG_V2_EMBEDDING_MODEL", "BAAI/bge-m3")
RAG_V2_EMBEDDING_VERSION = os.getenv("RAG_V2_EMBEDDING_VERSION", "2026-07-21-bge-m3")
RAG_V2_EMBEDDING_DIM = int(os.getenv("RAG_V2_EMBEDDING_DIM", "1024"))

RAG_EMBEDDING_SERVICE_URL = os.getenv(
    "RAG_EMBEDDING_SERVICE_URL",
    "http://rag-embedding-service:8080",
).rstrip("/")
RAG_RERANKER_SERVICE_URL = os.getenv(
    "RAG_RERANKER_SERVICE_URL",
    "http://rag-reranker-service:8080",
).rstrip("/")

RAG_VECTOR_TOP_K = int(os.getenv("RAG_VECTOR_TOP_K", "20"))
RAG_KEYWORD_TOP_K = int(os.getenv("RAG_KEYWORD_TOP_K", "20"))
RAG_RRF_TOP_K = int(os.getenv("RAG_RRF_TOP_K", "30"))
RAG_RRF_K = int(os.getenv("RAG_RRF_K", "60"))
RAG_RERANK_TOP_K = int(os.getenv("RAG_RERANK_TOP_K", "8"))

RAG_V2_EMBED_ON_UPLOAD = env_bool("RAG_V2_EMBED_ON_UPLOAD", False)
RAG_V2_INGEST_STRICT = env_bool("RAG_V2_INGEST_STRICT", False)
RAG_V2_FALLBACK_TO_V1 = env_bool("RAG_V2_FALLBACK_TO_V1", True)
