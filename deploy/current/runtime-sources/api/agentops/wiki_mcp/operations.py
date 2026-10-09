from __future__ import annotations

import os
import uuid
from contextlib import AbstractContextManager
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import text

try:  # production image exposes ``agentops``; source tests use ``agentops_local``
    from agentops.project_wiki.query import (
        get_decision_records as query_decision_records,
        get_examples as query_examples,
        get_page as query_get_page,
        get_recent_updates as query_recent_updates,
        get_related_nodes as query_related_nodes,
        search_wiki as query_search_wiki,
    )
    from agentops.project_wiki.service import create_memory_proposal
    from agentops.member_wiki.access import (
        MemberWikiAccessError,
        load_member_access_context,
        resolve_member_scope,
    )
    from agentops.member_wiki.query import (
        get_member_experience as query_get_member_experience,
        search_member_experiences,
    )
    from agentops.meeting_summaries.query import (
        get_meeting_summary as query_get_meeting_summary,
        search_meeting_summaries as query_search_meeting_summaries,
    )
    from agentops.rag.authz import require_member
    from agentops.wiki_mcp.materials import format_capabilities, material_item
except ModuleNotFoundError:  # pragma: no cover - source-tree fallback
    from agentops_local.project_wiki.query import (
        get_decision_records as query_decision_records,
        get_examples as query_examples,
        get_page as query_get_page,
        get_recent_updates as query_recent_updates,
        get_related_nodes as query_related_nodes,
        search_wiki as query_search_wiki,
    )
    from agentops_local.project_wiki.service import create_memory_proposal
    from agentops_local.member_wiki.access import (
        MemberWikiAccessError,
        load_member_access_context,
        resolve_member_scope,
    )
    from agentops_local.member_wiki.query import (
        get_member_experience as query_get_member_experience,
        search_member_experiences,
    )
    from agentops_local.meeting_summaries.query import (
        get_meeting_summary as query_get_meeting_summary,
        search_meeting_summaries as query_search_meeting_summaries,
    )
    from agentops_local.rag.authz import require_member
    from agentops_local.wiki_mcp.materials import format_capabilities, material_item


SessionFactory = Callable[[], AbstractContextManager]


def _json_value(value: Any) -> Any:
    if is_dataclass(value):
        return _json_value(asdict(value))
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    if hasattr(value, "__dict__"):
        return _json_value(vars(value))
    return value


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    cleaned = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError as error:
        raise ValueError("time filters must use ISO 8601 format") from error


def _member_hit_summary(item: Any) -> dict[str, Any]:
    return {
        "experience_id": str(item.id),
        "member_id": item.employee_id,
        "member_name": item.employee_name,
        "experience_key": item.experience_key,
        "title": item.title,
        "task_type": item.task_type,
        "outcome": item.outcome,
        "summary": item.summary,
        "tags": list(item.tags),
        "tools": list(item.tools),
        "confidence": item.confidence,
        "first_observed": str(item.first_observed),
        "last_observed": str(item.last_observed),
        "observation_count": item.observation_count,
        "current_version": item.current_version,
        "updated_at": str(item.updated_at),
        "lexical_score": item.lexical_score,
        "vector_score": item.vector_score,
    }


def _meeting_hit_summary(item: Any, *, include_markdown: bool = False) -> dict[str, Any]:
    result = {
        "meeting_summary_id": str(item.id),
        "project_id": str(item.project_id),
        "project_name": item.project_name,
        "title": item.title,
        "meeting_date": str(item.meeting_date),
        "participant_user_ids": [str(value) for value in item.participant_user_ids],
        "participants": list(item.participants),
        "tags": list(item.tags),
        "decisions": list(item.decisions),
        "action_items": list(item.action_items),
        "source_filename": item.source_filename,
        "source_format": item.source_format,
        "source_size_bytes": item.source_size_bytes,
        "created_by_name": item.created_by_name,
        "created_at": str(item.created_at),
        "updated_at": str(item.updated_at),
        "lexical_score": item.lexical_score,
        "vector_score": item.vector_score,
    }
    if include_markdown:
        result["summary_markdown"] = item.summary_markdown
    else:
        result["summary_excerpt"] = item.summary_markdown[:800]
    return result


class WikiOperations:
    def __init__(self, *, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory

    @staticmethod
    def _project_rows(orm, user_id: uuid.UUID):
        return orm.execute(
            text("""
                SELECT p.id::text, p.name, pm.role::text AS role
                FROM public.project_members pm
                JOIN public.projects p ON p.id = pm.project_id
                WHERE pm.user_id = :user_id
                ORDER BY p.name, p.id
            """),
            {"user_id": str(user_id)},
        ).all()

    def _resolve_project(
        self,
        orm,
        *,
        user_id: uuid.UUID,
        project_id: str | uuid.UUID | None,
        node_id: str | uuid.UUID | None = None,
    ) -> uuid.UUID:
        selected = project_id or os.getenv("WIKI_MCP_DEFAULT_PROJECT_ID", "").strip() or None
        if selected is None and node_id is not None:
            row = orm.execute(
                text("""
                    SELECT project_id::text
                    FROM public.project_wiki_pages
                    WHERE id = :node_id AND status = 'active'
                """),
                {"node_id": str(node_id)},
            ).first()
            selected = row.project_id if row else None
        if selected is None:
            projects = self._project_rows(orm, user_id)
            if len(projects) == 1:
                selected = projects[0].id
            elif not projects:
                raise ValueError("This account has no accessible projects")
            else:
                names = ", ".join(f"{row.name} ({row.id})" for row in projects[:8])
                raise ValueError(f"project_id is required; accessible projects: {names}")
        try:
            resolved = uuid.UUID(str(selected))
        except ValueError as error:
            raise ValueError("project_id must be a UUID") from error
        require_member(orm, user_id=user_id, project_id=resolved)
        return resolved

    def list_projects(self, *, user_id: uuid.UUID) -> dict[str, Any]:
        with self.session_factory() as orm:
            rows = self._project_rows(orm, user_id)
        return {
            "items": [
                {"project_id": str(row.id), "name": str(row.name), "role": str(row.role)}
                for row in rows
            ]
        }

    @staticmethod
    def _user_identity(orm, user_id: uuid.UUID) -> dict[str, str]:
        row = orm.execute(
            text("""
                SELECT au.id::text AS user_id, au.email,
                       COALESCE(
                           NULLIF(BTRIM(pu.nickname), ''),
                           NULLIF(BTRIM(pu.full_name), ''),
                           au.email,
                           au.id::text
                       ) AS name
                FROM auth.users au
                LEFT JOIN public.users pu ON pu.id = au.id
                WHERE au.id = :user_id
            """),
            {"user_id": str(user_id)},
        ).first()
        if row is None:
            return {"user_id": str(user_id), "name": str(user_id), "email": ""}
        return {
            "user_id": str(row.user_id),
            "name": str(row.name),
            "email": str(row.email or ""),
        }

    @staticmethod
    def _member_ids(context, member: str | None) -> tuple[list[str], dict[str, Any] | None]:
        if member:
            try:
                resolved = resolve_member_scope(
                    is_admin=context.is_admin,
                    current=context.current,
                    accessible_members=context.accessible_members,
                    requested_member=member,
                )
            except MemberWikiAccessError as error:
                raise PermissionError(error.detail) from error
            return [resolved.employee_id], _json_value(resolved)
        if context.is_admin:
            return [item.employee_id for item in context.accessible_members], None
        return [context.current.employee_id], _json_value(context.current)

    def list_member_wikis(self, *, user_id: uuid.UUID) -> dict[str, Any]:
        with self.session_factory() as orm:
            context = load_member_access_context(orm, user_id=user_id)
            member_ids = [item.employee_id for item in context.accessible_members]
            rows = []
            if member_ids:
                rows = orm.execute(
                    text("""
                        SELECT employee_id, count(*) AS experience_count,
                               max(last_observed) AS last_observed,
                               max(updated_at) AS updated_at
                        FROM public.member_wiki_experiences
                        WHERE status = 'active'
                          AND employee_id = ANY(CAST(:employee_ids AS text[]))
                        GROUP BY employee_id
                    """),
                    {"employee_ids": member_ids},
                ).all()
        counts = {str(row.employee_id): row for row in rows}
        return {
            "mode": "admin" if context.is_admin else "self",
            "items": [
                {
                    "member_id": member.employee_id,
                    "member_name": member.name,
                    "email": member.email,
                    "experience_count": int(counts[member.employee_id].experience_count)
                    if member.employee_id in counts else 0,
                    "last_observed": str(counts[member.employee_id].last_observed)
                    if member.employee_id in counts and counts[member.employee_id].last_observed else None,
                    "updated_at": str(counts[member.employee_id].updated_at)
                    if member.employee_id in counts and counts[member.employee_id].updated_at else None,
                }
                for member in context.accessible_members
            ],
        }

    @staticmethod
    def _query_embedding(query: str) -> list[float] | None:
        if not query.strip():
            return None
        try:
            from agentops.rag.model_clients import EmbeddingServiceClient

            return EmbeddingServiceClient().embed_query(query)
        except Exception:
            return None

    def search_member(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        member: str | None = None,
        tags: list[str] | None = None,
        outcome: str | None = None,
        task_type: str | None = None,
        updated_after: str | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        if outcome and outcome not in {"success", "partial", "failure"}:
            raise ValueError("outcome must be success, partial, or failure")
        with self.session_factory() as orm:
            context = load_member_access_context(orm, user_id=user_id)
            employee_ids, resolved_member = self._member_ids(context, member)
            items = search_member_experiences(
                orm,
                employee_ids=employee_ids,
                query=query,
                tags=tags,
                outcome=outcome,
                task_type=task_type,
                updated_after=_parse_datetime(updated_after),
                limit=limit,
                query_embedding=self._query_embedding(query),
            )
        return {
            "member": resolved_member,
            "searched_member_count": len(employee_ids),
            "items": [_member_hit_summary(item) for item in items],
        }

    def get_member_experience(
        self,
        *,
        user_id: uuid.UUID,
        experience_id: str,
    ) -> dict[str, Any]:
        try:
            parsed_id = uuid.UUID(experience_id)
        except ValueError as error:
            raise ValueError("experience_id must be a UUID") from error
        with self.session_factory() as orm:
            context = load_member_access_context(orm, user_id=user_id)
            employee_ids, _ = self._member_ids(context, None)
            item = query_get_member_experience(
                orm,
                experience_id=parsed_id,
                employee_ids=employee_ids,
            )
        if item is None:
            raise ValueError("member Wiki experience not found or not accessible")
        result = _member_hit_summary(item)
        result["markdown_content"] = item.markdown_content
        return result

    def recent_member_experience(
        self,
        *,
        user_id: uuid.UUID,
        member: str | None = None,
        since: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        with self.session_factory() as orm:
            context = load_member_access_context(orm, user_id=user_id)
            employee_ids, resolved_member = self._member_ids(context, member)
            items = search_member_experiences(
                orm,
                employee_ids=employee_ids,
                updated_after=_parse_datetime(since),
                limit=limit,
                query_embedding=None,
            )
        return {
            "member": resolved_member,
            "searched_member_count": len(employee_ids),
            "items": [_member_hit_summary(item) for item in items],
        }

    def list_meeting_summaries(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str | None = None,
        since: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        parsed_since = _parse_datetime(since)
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            items = query_search_meeting_summaries(
                orm,
                project_ids=[resolved],
                meeting_date_from=parsed_since.date() if parsed_since else None,
                limit=limit,
            )
        return {
            "project_id": str(resolved),
            "items": [_meeting_hit_summary(item) for item in items],
        }

    def search_meeting_summaries(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        project_id: str | None = None,
        tags: list[str] | None = None,
        since: str | None = None,
        limit: int = 8,
    ) -> dict[str, Any]:
        parsed_since = _parse_datetime(since)
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            items = query_search_meeting_summaries(
                orm,
                project_ids=[resolved],
                query=query,
                tags=tags,
                meeting_date_from=parsed_since.date() if parsed_since else None,
                limit=limit,
                query_embedding=self._query_embedding(query),
            )
        return {
            "project_id": str(resolved),
            "items": [_meeting_hit_summary(item) for item in items],
        }

    def get_meeting_summary(
        self,
        *,
        user_id: uuid.UUID,
        meeting_summary_id: str,
    ) -> dict[str, Any]:
        try:
            parsed_id = uuid.UUID(meeting_summary_id)
        except ValueError as error:
            raise ValueError("meeting_summary_id must be a UUID") from error
        with self.session_factory() as orm:
            row = orm.execute(
                text("SELECT project_id::text FROM public.meeting_summaries WHERE id = :id"),
                {"id": str(parsed_id)},
            ).first()
            if row is None:
                raise ValueError("meeting summary not found or not accessible")
            resolved = self._resolve_project(
                orm,
                user_id=user_id,
                project_id=str(row.project_id),
            )
            item = query_get_meeting_summary(
                orm,
                summary_id=parsed_id,
                project_ids=[resolved],
            )
        if item is None:
            raise ValueError("meeting summary not found or not accessible")
        return _meeting_hit_summary(item, include_markdown=True)

    def search(
        self,
        *,
        user_id: uuid.UUID,
        query: str,
        project_id: str | None = None,
        memory_kinds: list[str] | None = None,
        tags: list[str] | None = None,
        updated_after: str | None = None,
        verified_only: bool = False,
        limit: int = 8,
    ) -> dict[str, Any]:
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            items = query_search_wiki(
                orm,
                query=query,
                project_id=resolved,
                memory_kinds=memory_kinds,
                tags=tags,
                updated_after=_parse_datetime(updated_after),
                verified_only=verified_only,
                limit=limit,
            )
            if any(
                getattr(item, "project_id", None) != resolved
                for item in items
            ):
                raise RuntimeError(
                    "Wiki search returned a page outside the resolved project"
                )
        return {"project_id": str(resolved), "items": _json_value(items)}

    @staticmethod
    def _limit(value: int, *, maximum: int = 100) -> int:
        return max(1, min(int(value), maximum))

    @staticmethod
    def _uuid(value: str, *, field: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(value))
        except ValueError as error:
            raise ValueError(f"{field} must be a UUID") from error

    def list_material_format_capabilities(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
    ) -> dict[str, Any]:
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
        return {
            "project_id": str(resolved),
            "items": format_capabilities(),
            "note": "Accepted files are never executed. metadata_only formats are searchable by safe metadata until a dedicated parser is available.",
        }

    def list_knowledge_assets(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        include_historical: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            rows = orm.execute(
                text("""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''),
                                    NULLIF(to_jsonb(d)->>'source_relative_path', ''),
                                    d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash,
                           d.asset_family_id, d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                     WHERE pmd.project_id = :project_id
                       AND d.project_id = :project_id
                       AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                       AND (:include_historical OR COALESCE(d.is_current, true) = true)
                  ORDER BY COALESCE(d.effective_at, d.updated_at, d.created_at) DESC, d.id
                     LIMIT :limit
                """),
                {
                    "project_id": str(resolved),
                    "include_historical": bool(include_historical),
                    "limit": self._limit(limit),
                },
            ).mappings().all()
        return {"project_id": str(resolved), "items": [material_item(row) for row in rows]}

    def search_project_materials(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        query: str,
        include_historical: bool = False,
        limit: int = 8,
    ) -> dict[str, Any]:
        cleaned = query.strip()
        if not cleaned:
            raise ValueError("query is required")
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            rows = orm.execute(
                text("""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''),
                                    NULLIF(to_jsonb(d)->>'source_relative_path', ''),
                                    d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash,
                           d.asset_family_id, d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at,
                           c.id AS chunk_id, c.chunk_index, c.source_page, c.source_line,
                           c.heading_path, LEFT(c.content, 2000) AS excerpt,
                           GREATEST(
                               ts_rank(c.content_tsv, plainto_tsquery('simple', :query)),
                               CASE WHEN c.content ILIKE :like_query THEN 0.35 ELSE 0 END,
                               CASE WHEN d.filename ILIKE :like_query THEN 0.25 ELSE 0 END
                           ) AS score
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                 LEFT JOIN public.document_chunks_v2 c ON c.document_id = d.id AND c.project_id = :project_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                     WHERE pmd.project_id = :project_id
                       AND d.project_id = :project_id
                       AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                       AND (:include_historical OR COALESCE(d.is_current, true) = true)
                       AND (
                           c.content_tsv @@ plainto_tsquery('simple', :query)
                           OR c.content ILIKE :like_query
                           OR d.filename ILIKE :like_query
                           OR COALESCE(to_jsonb(f)->>'relative_path', '') ILIKE :like_query
                       )
                  ORDER BY score DESC, c.created_at ASC
                     LIMIT :limit
                """),
                {
                    "project_id": str(resolved),
                    "query": cleaned,
                    "like_query": f"%{cleaned}%",
                    "include_historical": bool(include_historical),
                    "limit": self._limit(limit, maximum=30),
                },
            ).mappings().all()
        return {
            "project_id": str(resolved),
            "query": cleaned,
            "retrieval_version": "mcp-material-v1-safe-lexical",
            "filters_applied": ["project_acl", "approved", "ready", "current_version" if not include_historical else "explicit_history"],
            "items": [material_item(row, include_excerpt=True) for row in rows],
        }

    def get_document(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        document_id: str,
        include_historical: bool = False,
        chunk_limit: int = 40,
    ) -> dict[str, Any]:
        parsed_id = self._uuid(document_id, field="document_id")
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            rows = orm.execute(
                text("""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''),
                                    NULLIF(to_jsonb(d)->>'source_relative_path', ''),
                                    d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash,
                           d.asset_family_id, d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at,
                           c.id AS chunk_id, c.chunk_index, c.source_page, c.source_line,
                           c.heading_path, LEFT(c.content, 8000) AS excerpt, 1.0 AS score
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                 LEFT JOIN public.document_chunks_v2 c ON c.document_id = d.id AND c.project_id = :project_id
                     WHERE pmd.project_id = :project_id AND d.project_id = :project_id
                       AND d.id = :document_id AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                       AND (:include_historical OR COALESCE(d.is_current, true) = true)
                  ORDER BY c.chunk_index
                     LIMIT :limit
                """),
                {
                    "project_id": str(resolved),
                    "document_id": str(parsed_id),
                    "include_historical": bool(include_historical),
                    "limit": self._limit(chunk_limit, maximum=100),
                },
            ).mappings().all()
        if not rows:
            raise ValueError("document not found, not approved, not current, or not accessible")
        metadata = material_item(rows[0])
        chunks = [
            {
                "block_id": str(row.get("chunk_id")),
                "chunk_index": row.get("chunk_index"),
                "content": str(row.get("excerpt") or ""),
                "locator": material_item(row, include_excerpt=True)["locator"],
            }
            for row in rows if row.get("chunk_id") is not None
        ]
        return {
            "project_id": str(resolved),
            "document": metadata,
            "chunks": chunks,
            "truncated": metadata["chunk_count"] > len(chunks),
            "next_chunk_index": len(chunks) if metadata["chunk_count"] > len(chunks) else None,
        }

    def get_document_part(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        document_id: str,
        block_id: str,
        include_historical: bool = False,
    ) -> dict[str, Any]:
        parsed_document_id = self._uuid(document_id, field="document_id")
        try:
            parsed_block_id = uuid.UUID(block_id)
            block_filter = "c.id = :block_id"
            block_params: dict[str, Any] = {"block_id": str(parsed_block_id)}
        except ValueError:
            try:
                chunk_index = int(block_id)
            except ValueError as error:
                raise ValueError("block_id must be a chunk UUID or non-negative chunk index") from error
            if chunk_index < 0:
                raise ValueError("block_id chunk index must be non-negative")
            block_filter = "c.chunk_index = :chunk_index"
            block_params = {"chunk_index": chunk_index}
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            row = orm.execute(
                text(f"""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''), d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash, d.asset_family_id,
                           d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at,
                           c.id AS chunk_id, c.chunk_index, c.source_page, c.source_line,
                           c.heading_path, c.content AS excerpt, 1.0 AS score
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                      JOIN public.document_chunks_v2 c ON c.document_id = d.id AND c.project_id = :project_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                     WHERE pmd.project_id = :project_id AND d.project_id = :project_id
                       AND d.id = :document_id AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                       AND (:include_historical OR COALESCE(d.is_current, true) = true)
                       AND {block_filter}
                     LIMIT 1
                """),
                {
                    "project_id": str(resolved),
                    "document_id": str(parsed_document_id),
                    "include_historical": bool(include_historical),
                    **block_params,
                },
            ).mappings().first()
        if row is None:
            raise ValueError("document block not found or not accessible")
        item = material_item(row, include_excerpt=True)
        return {"project_id": str(resolved), "item": item}

    def get_document_structure(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        document_id: str,
        include_historical: bool = False,
        block_limit: int = 200,
    ) -> dict[str, Any]:
        """Return a safe, traceable outline without exposing raw storage bytes.

        Headings are sourced from the indexed ``heading_path`` column.  The
        operation is deliberately read-only and the returned outline is not a
        publishable Wiki document; callers must obtain human confirmation
        before turning it into a plan or gap list.
        """
        document = self.get_document(
            user_id=user_id,
            project_id=project_id,
            document_id=document_id,
            include_historical=include_historical,
            chunk_limit=block_limit,
        )
        sections: list[dict[str, Any]] = []
        by_path: dict[str, dict[str, Any]] = {}
        for chunk in document.get("chunks", []):
            locator = chunk.get("locator") or {}
            heading_path = str(locator.get("heading_path") or "").strip()
            section = by_path.get(heading_path)
            if section is None:
                section = {
                    "heading_path": heading_path or None,
                    "blocks": [],
                }
                by_path[heading_path] = section
                sections.append(section)
            section["blocks"].append(
                {
                    "block_id": chunk.get("block_id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "content_excerpt": str(chunk.get("content") or "")[:2000],
                    "locator": locator,
                }
            )
        return {
            "project_id": document["project_id"],
            "document": document["document"],
            "sections": sections,
            "block_count": sum(len(section["blocks"]) for section in sections),
            "truncated": bool(document.get("truncated")),
            "manual_confirmation_required": True,
            "publishable": False,
        }

    def validate_citations(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        citations: list[dict[str, Any]],
        include_historical: bool = False,
    ) -> dict[str, Any]:
        """Validate citation locators against approved project material only."""
        if not isinstance(citations, list):
            raise ValueError("citations must be a list")
        if len(citations) > 100:
            raise ValueError("citations cannot contain more than 100 items")
        with self.session_factory() as orm:
            resolved_project = self._resolve_project(
                orm, user_id=user_id, project_id=project_id
            )
        validated: list[dict[str, Any]] = []
        invalid: list[dict[str, Any]] = []
        for index, citation in enumerate(citations):
            if not isinstance(citation, dict):
                invalid.append({"index": index, "reason": "citation must be an object"})
                continue
            document_id = citation.get("document_id") or (citation.get("locator") or {}).get("document_id")
            locator = citation.get("locator") if isinstance(citation.get("locator"), dict) else citation
            block_id = locator.get("block_id")
            if block_id is None:
                block_id = locator.get("chunk_id")
            if block_id is None and "chunk_index" in locator:
                block_id = locator.get("chunk_index")
            if not document_id:
                invalid.append({"index": index, "reason": "document_id is required"})
                continue
            try:
                item = (
                    self.get_document_part(
                        user_id=user_id,
                        project_id=project_id,
                        document_id=str(document_id),
                        block_id=str(block_id),
                        include_historical=include_historical,
                    )
                    if block_id is not None
                    else self.get_document(
                        user_id=user_id,
                        project_id=project_id,
                        document_id=str(document_id),
                        include_historical=include_historical,
                        chunk_limit=1,
                    )
                )
                resolved_item = item.get("item") or item.get("document")
                resolved_locator = (resolved_item or {}).get("locator") or {}
                locator_mismatches = []
                for key in ("page", "line", "heading_path", "chunk_index", "relative_path"):
                    if key in locator and locator.get(key) is not None:
                        expected = str(locator.get(key))
                        actual = resolved_locator.get(key)
                        if actual is None or str(actual) != expected:
                            locator_mismatches.append(key)
                if locator_mismatches:
                    invalid.append({
                        "index": index,
                        "reason": "citation locator does not match the approved document block",
                        "fields": locator_mismatches,
                    })
                    continue
                validated.append({
                    "index": index,
                    "valid": True,
                    "citation": citation,
                    "resolved": resolved_item,
                })
            except (ValueError, PermissionError) as error:
                invalid.append({"index": index, "reason": str(error)})
        return {
            "project_id": str(resolved_project),
            "valid": validated,
            "invalid": invalid,
            "all_valid": not invalid,
            "manual_confirmation_required": False,
            "publishable": False,
        }

    def get_latest_document(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        logical_key: str,
    ) -> dict[str, Any]:
        key = logical_key.strip()
        if not key:
            raise ValueError("logical_key is required")
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            rows = orm.execute(
                text("""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''), d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash, d.asset_family_id,
                           d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                     WHERE pmd.project_id = :project_id AND d.project_id = :project_id
                       AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                       AND COALESCE(d.is_current, true) = true
                       AND (d.asset_family_id::text = :logical_key
                            OR lower(COALESCE(d.normalized_filename, d.filename)) = lower(:logical_key))
                  ORDER BY COALESCE(d.version_number, 1) DESC,
                           COALESCE(d.effective_at, d.updated_at, d.created_at) DESC
                     LIMIT 1
                """),
                {"project_id": str(resolved), "logical_key": key},
            ).mappings().all()
        if not rows:
            raise ValueError("latest document not found or not accessible")
        return {"project_id": str(resolved), "item": material_item(rows[0])}

    def compare_document_versions(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        asset_family_id: str,
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        family_id = self._uuid(asset_family_id, field="asset_family_id")
        if from_version < 1 or to_version < 1 or from_version == to_version:
            raise ValueError("from_version and to_version must be distinct positive integers")
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            rows = orm.execute(
                text("""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''), d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash, d.asset_family_id,
                           d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                     WHERE pmd.project_id = :project_id AND d.project_id = :project_id
                       AND d.asset_family_id = :asset_family_id
                       AND d.version_number IN (:from_version, :to_version)
                       AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                  ORDER BY d.version_number
                """),
                {
                    "project_id": str(resolved), "asset_family_id": str(family_id),
                    "from_version": from_version, "to_version": to_version,
                },
            ).mappings().all()
            by_version = {int(row["version_number"]): row for row in rows}
            if from_version not in by_version or to_version not in by_version:
                raise ValueError("both approved document versions must exist in the selected project")
            changes = orm.execute(
                text("""
                    WITH old_chunks AS (
                        SELECT chunk_index, md5(content) AS digest FROM public.document_chunks_v2
                         WHERE project_id = :project_id AND document_id = :from_document_id
                    ), new_chunks AS (
                        SELECT chunk_index, md5(content) AS digest FROM public.document_chunks_v2
                         WHERE project_id = :project_id AND document_id = :to_document_id
                    )
                    SELECT COALESCE(o.chunk_index, n.chunk_index) AS chunk_index,
                           CASE WHEN o.chunk_index IS NULL THEN 'added'
                                WHEN n.chunk_index IS NULL THEN 'removed'
                                ELSE 'changed' END AS change_type
                      FROM old_chunks o FULL OUTER JOIN new_chunks n USING (chunk_index)
                     WHERE o.digest IS DISTINCT FROM n.digest
                  ORDER BY chunk_index LIMIT 200
                """),
                {
                    "project_id": str(resolved),
                    "from_document_id": str(by_version[from_version]["document_id"]),
                    "to_document_id": str(by_version[to_version]["document_id"]),
                },
            ).mappings().all()
        return {
            "project_id": str(resolved), "asset_family_id": str(family_id),
            "from": material_item(by_version[from_version]),
            "to": material_item(by_version[to_version]),
            "changed_chunks": [dict(row) for row in changes],
            "change_count": len(changes), "changes_truncated": len(changes) == 200,
        }

    def compare_versions(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        asset_family_id: str,
        from_version: int,
        to_version: int,
    ) -> dict[str, Any]:
        """Task-MCP friendly alias for the explicit version comparison tool."""
        return self.compare_document_versions(
            user_id=user_id,
            project_id=project_id,
            asset_family_id=asset_family_id,
            from_version=from_version,
            to_version=to_version,
        )

    def get_recent_knowledge_updates(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        since: str,
        limit: int = 20,
    ) -> dict[str, Any]:
        parsed_since = _parse_datetime(since)
        if parsed_since is None:
            raise ValueError("since is required")
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            rows = orm.execute(
                text("""
                    SELECT d.id AS document_id, d.filename, d.display_name,
                           COALESCE(NULLIF(to_jsonb(f)->>'relative_path', ''), d.filename) AS relative_path,
                           d.format, d.size_bytes, pmd.content_hash, d.asset_family_id,
                           d.version_number, d.is_current,
                           COALESCE(d.approval_status, 'approved') AS approval_status,
                           d.chunk_count, d.created_at, d.updated_at
                      FROM public.project_material_documents pmd
                      JOIN public.documents d ON d.id = pmd.document_id
                 LEFT JOIN public.project_material_intake_files f ON f.id = pmd.original_file_id
                     WHERE pmd.project_id = :project_id AND d.project_id = :project_id
                       AND d.status = 'ready'
                       AND COALESCE(d.approval_status, 'approved') = 'approved'
                       AND COALESCE(d.is_current, true) = true
                       AND d.updated_at >= :since
                  ORDER BY d.updated_at DESC LIMIT :limit
                """),
                {"project_id": str(resolved), "since": parsed_since, "limit": self._limit(limit)},
            ).mappings().all()
        return {"project_id": str(resolved), "since": parsed_since.isoformat(), "items": [material_item(row) for row in rows]}

    def build_evidence_pack(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        query: str,
        limit: int = 12,
    ) -> dict[str, Any]:
        search_result = self.search_project_materials(
            user_id=user_id, project_id=project_id, query=query, limit=limit,
        )
        return {
            "project_id": search_result["project_id"], "query": search_result["query"],
            "retrieval_version": search_result["retrieval_version"],
            "filters_applied": search_result["filters_applied"],
            "items": search_result["items"],
            "gaps": [] if search_result["items"] else ["No approved current project material matched the query."],
            "conflicts": [],
            "manual_confirmation_required": True,
            "publishable": False,
            "note": "Evidence packs, plan drafts, and gap lists are read-only suggestions; human confirmation is required before Wiki publication.",
        }

    def draft_project_plan(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        goal: str,
        constraints: list[str] | None = None,
        limit: int = 12,
    ) -> dict[str, Any]:
        """Build a non-publishable plan outline backed by a cited evidence pack."""
        cleaned_goal = goal.strip()
        if not cleaned_goal:
            raise ValueError("goal is required")
        pack = self.build_evidence_pack(
            user_id=user_id, project_id=project_id, query=cleaned_goal, limit=limit
        )
        return {
            "project_id": pack["project_id"],
            "goal": cleaned_goal,
            "constraints": [str(item).strip() for item in (constraints or []) if str(item).strip()],
            "status": "draft",
            "publication_status": "not_published",
            "sections": [
                {"title": "目标与范围", "content": cleaned_goal},
                {"title": "现状与依据", "evidence": pack["items"]},
                {"title": "里程碑", "content": "待人工确认后补充"},
                {"title": "风险与待确认问题", "content": pack["gaps"] or "待人工确认"},
            ],
            "evidence_pack": pack,
            "manual_confirmation_required": True,
            "publishable": False,
        }

    def list_knowledge_gaps(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        query: str,
        limit: int = 12,
    ) -> dict[str, Any]:
        """Return explicit evidence gaps; does not infer or publish facts."""
        pack = self.build_evidence_pack(
            user_id=user_id, project_id=project_id, query=query, limit=limit
        )
        gaps = list(pack["gaps"])
        if pack["conflicts"]:
            gaps.append("Approved current materials contain unresolved version conflicts.")
        return {
            "project_id": pack["project_id"],
            "query": pack["query"],
            "gaps": gaps,
            "evidence_count": len(pack["items"]),
            "manual_confirmation_required": True,
            "publishable": False,
        }

    def get_approval_job_status(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str,
        job_id: str | None = None,
        draft_id: str | None = None,
    ) -> dict[str, Any]:
        if bool(job_id) == bool(draft_id):
            raise ValueError("provide exactly one of job_id or draft_id")
        field = "job_id" if job_id else "draft_id"
        parsed = self._uuid(job_id or draft_id or "", field=field)
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            row = orm.execute(
                text(f"""
                    SELECT job.id AS job_id, job.draft_id, job.decision,
                           job.status AS job_status, job.progress, job.current_step,
                           job.error_message, job.attempt_count, job.started_at,
                           job.completed_at, draft.approved_document_id AS document_id
                      FROM public.project_memory_approval_jobs job
                      JOIN public.project_memory_drafts draft ON draft.id = job.draft_id
                    WHERE draft.project_id = :project_id AND job.{('id' if field == 'job_id' else 'draft_id')} = :handle_id
                  ORDER BY job.created_at DESC LIMIT 1
                """),
                {"project_id": str(resolved), "handle_id": str(parsed)},
            ).mappings().first()
        if row is None:
            raise ValueError("approval job not found or not accessible")
        status = str(row["job_status"])
        return {
            "project_id": str(resolved), "job_id": str(row["job_id"]),
            "draft_id": str(row["draft_id"]), "decision": str(row["decision"]),
            "job_status": status, "progress": int(row["progress"] or 0),
            "current_step": str(row["current_step"] or status),
            "attempt_count": int(row["attempt_count"] or 0),
            "started_at": str(row["started_at"]) if row["started_at"] else None,
            "completed_at": str(row["completed_at"]) if row["completed_at"] else None,
            "document_id": str(row["document_id"]) if row["document_id"] else None,
            "pending": status in {"queued", "running"},
            "terminal": status in {"completed", "failed"},
            "has_error": bool(row["error_message"]),
            "error_message": "Approval processing failed; see the SmartBrain review page for details." if row["error_message"] else None,
        }

    def get_page(
        self,
        *,
        user_id: uuid.UUID,
        page_id: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        try:
            node_id = uuid.UUID(page_id)
        except ValueError as error:
            raise ValueError("page_id must be a UUID") from error
        with self.session_factory() as orm:
            resolved = self._resolve_project(
                orm,
                user_id=user_id,
                project_id=project_id,
                node_id=node_id,
            )
            page = query_get_page(orm, page_id=node_id, project_id=resolved)
        if page is None:
            raise ValueError("Wiki page not found")
        return _json_value(page)

    def related(
        self,
        *,
        user_id: uuid.UUID,
        node_id: str,
        project_id: str | None = None,
        relation: str | None = None,
        depth: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        try:
            parsed_node_id = uuid.UUID(node_id)
        except ValueError as error:
            raise ValueError("node_id must be a UUID") from error
        with self.session_factory() as orm:
            resolved = self._resolve_project(
                orm,
                user_id=user_id,
                project_id=project_id,
                node_id=parsed_node_id,
            )
            items = query_related_nodes(
                orm,
                node_id=parsed_node_id,
                project_id=resolved,
                relation=relation,
                depth=depth,
                limit=limit,
            )
        return {"project_id": str(resolved), "items": _json_value(items)}

    def recent(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str | None = None,
        since: str | None = None,
        memory_kinds: list[str] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            items = query_recent_updates(
                orm,
                project_id=resolved,
                since=_parse_datetime(since),
                memory_kinds=memory_kinds,
                limit=limit,
            )
        return {"project_id": str(resolved), "items": _json_value(items)}

    def decisions(
        self,
        *,
        user_id: uuid.UUID,
        project_id: str | None = None,
        topic: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            items = query_decision_records(
                orm,
                project_id=resolved,
                topic=topic,
                limit=limit,
            )
        return {"project_id": str(resolved), "items": _json_value(items)}

    def examples(
        self,
        *,
        user_id: uuid.UUID,
        topic: str,
        project_id: str | None = None,
        outcome: str = "any",
        limit: int = 8,
    ) -> dict[str, Any]:
        if outcome not in {"any", "failure", "success"}:
            raise ValueError("outcome must be any, failure, or success")
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            items = query_examples(
                orm,
                topic=topic,
                project_id=resolved,
                outcome=outcome,
                limit=limit,
            )
        return {"project_id": str(resolved), "items": _json_value(items)}

    def propose(
        self,
        *,
        user_id: uuid.UUID,
        scopes: list[str],
        project_id: str,
        title: str,
        memory_kind: str,
        content: str,
        summary: str = "",
        tags: list[str] | None = None,
        source_page_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if "wiki:propose" not in scopes:
            raise PermissionError("This token requires the wiki:propose scope")
        source_ids: list[uuid.UUID] = []
        try:
            source_ids = [uuid.UUID(item) for item in (source_page_ids or [])]
        except ValueError as error:
            raise ValueError("source_page_ids must contain UUIDs") from error
        with self.session_factory() as orm:
            resolved = self._resolve_project(orm, user_id=user_id, project_id=project_id)
            uploaded_by = self._user_identity(orm, user_id)
            if source_ids:
                rows = orm.execute(
                    text("""
                        SELECT id::text
                        FROM public.project_wiki_pages
                        WHERE project_id = :project_id AND status = 'active'
                          AND id = ANY(CAST(:source_ids AS uuid[]))
                    """),
                    {"project_id": str(resolved), "source_ids": [str(item) for item in source_ids]},
                ).all()
                if len(rows) != len(set(source_ids)):
                    raise ValueError("Every source page must exist in the selected project")
            page_id = create_memory_proposal(
                orm,
                project_id=resolved,
                proposed_by_user_id=user_id,
                title=title,
                memory_kind=memory_kind,
                content=content,
                summary=summary,
                tags=tags,
                source_page_ids=source_ids,
            )
        return {
            "page_id": str(page_id),
            "project_id": str(resolved),
            "status": "published",
            "uploaded_by": uploaded_by,
            "message": "Memory passed safety checks and was published directly to the project Wiki.",
        }
