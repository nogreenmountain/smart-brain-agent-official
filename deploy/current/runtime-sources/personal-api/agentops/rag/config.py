from __future__ import annotations

import os
import uuid


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
_RAG_V3_PROJECT_ALLOWLIST_RAW = os.getenv("RAG_V3_PROJECT_ALLOWLIST")
RAG_V3_PROJECT_ALLOWLIST_CONFIGURED = _RAG_V3_PROJECT_ALLOWLIST_RAW is not None
RAG_V3_REQUIRE_PROJECT_ALLOWLIST = env_bool(
    "RAG_V3_REQUIRE_PROJECT_ALLOWLIST",
    False,
)


def _parse_project_allowlist(raw: str | None) -> frozenset[uuid.UUID]:
    """Parse a comma-separated project UUID allowlist fail-closed."""
    if raw is None:
        return frozenset()
    values = [part.strip() for part in raw.split(",") if part.strip()]
    parsed: list[uuid.UUID] = []
    for value in values:
        try:
            parsed.append(uuid.UUID(value))
        except (ValueError, AttributeError):
            return frozenset()
    return frozenset(parsed)


RAG_V3_PROJECT_ALLOWLIST = _parse_project_allowlist(_RAG_V3_PROJECT_ALLOWLIST_RAW)
SUPPORTED_RETRIEVAL_VERSIONS = {
    "v1", "v2-vector", "v2-hybrid", "v2-hybrid-rerank", "v3-shadow",
}


def v3_retrieval_enabled(project_id=None) -> bool:
    """Return whether v3 retrieval may read its independent shadow index."""
    # The master switch protects both the configured default and explicit
    # per-request ``v3-*`` selections.  An explicit shadow request is useful
    # during a project allow-list canary while the global default remains v2.
    if not RAG_V3_ENABLED:
        return False
    # A declared allowlist is restrictive even when empty or malformed.  This
    # makes a production typo fail closed instead of silently enabling v3 for
    # every project.  When the variable is absent, isolated candidate tests
    # may exercise v3 without a project-specific route.
    if RAG_V3_REQUIRE_PROJECT_ALLOWLIST or RAG_V3_PROJECT_ALLOWLIST_CONFIGURED or RAG_V3_PROJECT_ALLOWLIST:
        if project_id is None:
            return False
        try:
            normalized = uuid.UUID(str(project_id))
        except (ValueError, AttributeError, TypeError):
            return False
        # Keep the runtime tolerant of tests/embedders that provide strings
        # while the environment parser still exposes UUID values.
        return any(
            (uuid.UUID(str(value)) if not isinstance(value, uuid.UUID) else value)
            == normalized
            for value in RAG_V3_PROJECT_ALLOWLIST
            if _is_valid_uuid_value(value)
        )
    return True


def _is_valid_uuid_value(value) -> bool:
    try:
        uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError):
        return False
    return True


def v3_indexing_enabled() -> bool:
    """Return whether background v3 indexing may be scheduled."""
    return RAG_V3_ENABLED


def effective_retrieval_version(requested: str | None = None, *, project_id=None) -> str:
    """Resolve a requested mode without ever bypassing the v3 master switch."""
    version = requested or RAG_RETRIEVAL_VERSION
    if version.startswith("v3-") and not v3_retrieval_enabled(project_id):
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
