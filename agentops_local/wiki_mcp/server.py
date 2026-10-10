from __future__ import annotations

import os
import uuid
from typing import Any

from mcp.server import MCPServer
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.settings import AuthSettings
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from agentops.common.orm import session_scope
from agentops.wiki_mcp.auth import WikiTokenVerifier
from agentops.wiki_mcp.operations import WikiOperations
from agentops.wiki_mcp.urls import build_auth_urls


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


MATERIAL_TOOLS_ENABLED = _env("WIKI_MCP_MATERIAL_TOOLS_ENABLED", "false").lower() in {
    "1", "true", "yes", "on"
}


def _token_secret() -> str:
    value = _env("WIKI_MCP_TOKEN_SECRET") or _env("AUTH_COOKIE_SECRET")
    if not value:
        raise RuntimeError("WIKI_MCP_TOKEN_SECRET or AUTH_COOKIE_SECRET must be configured")
    return value


def _identity() -> tuple[uuid.UUID, list[str]]:
    token = get_access_token()
    if token is None or not token.subject:
        raise PermissionError("Authenticated Wiki MCP token is required")
    try:
        user_id = uuid.UUID(token.subject)
    except ValueError as error:
        raise PermissionError("Wiki MCP token has an invalid user identity") from error
    return user_id, list(token.scopes)


class ProjectMemoryMCPServer(MCPServer):
    """Use the public MCP hooks to reject extra identity/usage write fields.

    The SDK's default function argument model ignores unknown fields. This
    dedicated tool must reject them, and advertise that rule in discovery.
    """
    conversation_fields = {'project_id', 'submission_id', 'title', 'messages', 'task_result', 'model'}

    async def list_tools(self):
        tools = await super().list_tools()
        for tool in tools:
            if tool.name == 'record_project_conversation':
                tool.input_schema = dict(tool.input_schema, additionalProperties=False)
                properties = tool.input_schema['properties']
                properties['title']['maxLength'] = 120
                properties['task_result']['maxLength'] = 300
                properties['messages'].update(minItems=1, maxItems=2, items={
                    'oneOf': [{'type': 'object', 'additionalProperties': False,
                        'required': ['role', 'content'], 'properties': {
                            'role': {'const': role},
                            'content': {'type': 'string', 'minLength': 1, 'maxLength': limit},
                        }} for role, limit in [('user', 300), ('assistant', 600)]]})
        return tools

    async def call_tool(self, name, arguments, context=None):
        if name == 'record_project_conversation' and set(arguments) - self.conversation_fields:
            raise ValueError('record_project_conversation accepts only its declared fields; uploader and usage are server-controlled')
        return await super().call_tool(name, arguments, context)

public_url = _env("WIKI_MCP_PUBLIC_URL", "http://127.0.0.1:8010").rstrip("/")
issuer_url, resource_server_url = build_auth_urls(public_url)
verifier = WikiTokenVerifier(secret=_token_secret(), session_factory=session_scope)
mcp = ProjectMemoryMCPServer(
    "smartbrain-company-memory",
    title="SmartBrain Company Memory",
    description="Search reviewed project memory, privacy-scoped member experience, and project meeting summaries.",
    instructions=(
        "Search before answering questions about company history, decisions, failures, workflows, or strategy. "
        "Prefer verified and recently updated pages, cite page IDs, and surface conflicts or stale guidance. "
        "Member Wiki tools inherit the token owner's same access: members see only themselves; organization owners/admins see members they administer. "
        "Meeting summary tools inherit project membership and never expose projects the token owner cannot read. "
        "Material evidence, plan drafts, and gap lists are read-only; they require human confirmation and are never published automatically."
    ),
    version="1.4.1",
    token_verifier=verifier,
    auth=AuthSettings(
        issuer_url=issuer_url,
        resource_server_url=resource_server_url,
        required_scopes=["wiki:read"],
    ),
)
operations = WikiOperations(session_factory=session_scope)


def _material_guard() -> None:
    if not MATERIAL_TOOLS_ENABLED:
        raise RuntimeError("MCP material tools are disabled by WIKI_MCP_MATERIAL_TOOLS_ENABLED")


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "smartbrain-company-memory"})


@mcp.tool(description="Save an explicitly authorized concise summary of the visible user request and assistant FINAL result to one project, never a transcript. At most two ordered messages: user <=300 characters, assistant <=600; task_result <=300, title <=120, total payload <=6000 UTF-8 bytes. Do not read, reproduce, summarize, or submit hidden thinking/reasoning/analysis, progress commentary, system/developer instructions, tool calls/results/logs, code dumps, configuration or environment. Violations are rejected, never silently truncated. Requires explicit project UUID and wiki:propose scope. Reuse submission_id (UUID) only with identical content. Uploader/time are server-controlled; model is client-declared and tokens unknown. status=saved and wiki_status=published are separate; retry failed Wiki publishing with the same submission_id.")
def record_project_conversation(
    project_id: str, submission_id: str, title: str,
    messages: list[dict[str, str]], task_result: str = '', model: str | None = None,
) -> dict[str, Any]:
    user_id, scopes = _identity()
    return operations.record_conversation(user_id=user_id, scopes=scopes,
        project_id=project_id, submission_id=submission_id, title=title,
        messages=messages, task_result=task_result, model=model)


@mcp.tool(description="List accepted upload formats and current parser/search capabilities. Accepted files are never executed.")
def list_material_format_capabilities(project_id: str) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.list_material_format_capabilities(user_id=user_id, project_id=project_id)


@mcp.tool(description="List approved, current project knowledge assets with safe citations and version metadata.")
def list_knowledge_assets(project_id: str, include_historical: bool = False, limit: int = 50) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.list_knowledge_assets(user_id=user_id, project_id=project_id, include_historical=include_historical, limit=limit)


@mcp.tool(description="Search approved current project materials and return traceable citations. Binary uploads are metadata-only and never executed.")
def search_project_materials(project_id: str, query: str, include_historical: bool = False, limit: int = 8) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.search_project_materials(user_id=user_id, project_id=project_id, query=query, include_historical=include_historical, limit=limit)


@mcp.tool(description="Read an approved project document and its traceable content blocks without exposing raw storage bytes.")
def get_document(project_id: str, document_id: str, include_historical: bool = False, chunk_limit: int = 40) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.get_document(user_id=user_id, project_id=project_id, document_id=document_id, include_historical=include_historical, chunk_limit=chunk_limit)


@mcp.tool(description="Read one approved document block by block UUID or chunk index with citation metadata.")
def get_document_part(
    project_id: str,
    document_id: str,
    block_id: str,
    include_historical: bool = False,
) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.get_document_part(
        user_id=user_id,
        project_id=project_id,
        document_id=document_id,
        block_id=block_id,
        include_historical=include_historical,
    )


@mcp.tool(description="Return a safe outline of an approved document grouped by heading path. Output is read-only and requires human confirmation before use in a plan or Wiki publication.")
def get_document_structure(
    project_id: str,
    document_id: str,
    include_historical: bool = False,
    block_limit: int = 200,
) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.get_document_structure(
        user_id=user_id,
        project_id=project_id,
        document_id=document_id,
        include_historical=include_historical,
        block_limit=block_limit,
    )


@mcp.tool(description="Validate document/block citation locators against approved project materials. This tool never writes or publishes Wiki content.")
def validate_citations(
    project_id: str,
    citations: list[dict[str, Any]],
    include_historical: bool = False,
) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.validate_citations(
        user_id=user_id,
        project_id=project_id,
        citations=citations,
        include_historical=include_historical,
    )


@mcp.tool(description="Resolve the latest approved effective version of a logical project document.")
def get_latest_document(project_id: str, logical_key: str) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.get_latest_document(user_id=user_id, project_id=project_id, logical_key=logical_key)


@mcp.tool(description="Compare two approved versions of the same project document family by changed blocks.")
def compare_document_versions(project_id: str, asset_family_id: str, from_version: int, to_version: int) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.compare_document_versions(user_id=user_id, project_id=project_id, asset_family_id=asset_family_id, from_version=from_version, to_version=to_version)


@mcp.tool(description="Compare two approved versions of a document family (task-oriented alias).")
def compare_versions(project_id: str, asset_family_id: str, from_version: int, to_version: int) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.compare_versions(
        user_id=user_id,
        project_id=project_id,
        asset_family_id=asset_family_id,
        from_version=from_version,
        to_version=to_version,
    )


@mcp.tool(description="List approved current project materials updated after an ISO-8601 timestamp.")
def get_recent_knowledge_updates(project_id: str, since: str, limit: int = 20) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.get_recent_knowledge_updates(user_id=user_id, project_id=project_id, since=since, limit=limit)


@mcp.tool(description="Build a cited evidence pack from approved current project materials for plan/decision generation.")
def build_evidence_pack(project_id: str, query: str, limit: int = 12) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.build_evidence_pack(user_id=user_id, project_id=project_id, query=query, limit=limit)


@mcp.tool(description="Create a read-only project plan outline from approved evidence. The draft is never published automatically and requires human confirmation.")
def draft_project_plan(project_id: str, goal: str, constraints: list[str] | None = None, limit: int = 12) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.draft_project_plan(
        user_id=user_id, project_id=project_id, goal=goal,
        constraints=constraints, limit=limit,
    )


@mcp.tool(description="List explicit evidence gaps for a project query. This is a read-only checklist requiring human confirmation.")
def list_knowledge_gaps(project_id: str, query: str, limit: int = 12) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.list_knowledge_gaps(
        user_id=user_id, project_id=project_id, query=query, limit=limit,
    )


@mcp.tool(description="Read the durable status of a project-material approval job. This tool never approves or rejects content.")
def get_approval_job_status(project_id: str, job_id: str | None = None, draft_id: str | None = None) -> dict[str, Any]:
    _material_guard()
    user_id, _ = _identity()
    return operations.get_approval_job_status(user_id=user_id, project_id=project_id, job_id=job_id, draft_id=draft_id)
@mcp.tool(description="List projects the current token owner can read.")
def list_wiki_projects() -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.list_projects(user_id=user_id)


@mcp.tool(description="List member Wikis visible to the current token owner. The token owner gets the same access as in SmartBrain: self only for regular members, administered organization members for owners/admins.")
def list_member_wikis() -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.list_member_wikis(user_id=user_id)


@mcp.tool(description="Search reusable member experience for a task using hybrid semantic and keyword retrieval. Pass member as an employee ID, name, or email; regular members remain restricted to themselves.")
def search_member_experience(
    query: str,
    member: str | None = None,
    tags: list[str] | None = None,
    outcome: str | None = None,
    task_type: str | None = None,
    updated_after: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.search_member(
        user_id=user_id,
        query=query,
        member=member,
        tags=tags,
        outcome=outcome,
        task_type=task_type,
        updated_after=updated_after,
        limit=limit,
    )


@mcp.tool(description="Read one complete reusable member experience in the standardized Markdown format. Access is inherited from the current token owner.")
def get_member_experience(experience_id: str) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.get_member_experience(
        user_id=user_id,
        experience_id=experience_id,
    )


@mcp.tool(description="Return recently updated member experiences, optionally for one accessible member and after an ISO-8601 time.")
def get_member_recent_experience(
    member: str | None = None,
    since: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.recent_member_experience(
        user_id=user_id,
        member=member,
        since=since,
        limit=limit,
    )


@mcp.tool(description="List recent meeting summaries in a project. Access always inherits the token owner's project membership.")
def list_meeting_summaries(
    project_id: str | None = None,
    since: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.list_meeting_summaries(
        user_id=user_id, project_id=project_id, since=since, limit=limit,
    )


@mcp.tool(description="Search extracted meeting-file contents, titles, and participants using hybrid semantic and keyword retrieval. Access inherits project membership.")
def search_meeting_summaries(
    query: str,
    project_id: str | None = None,
    tags: list[str] | None = None,
    since: str | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.search_meeting_summaries(
        user_id=user_id, query=query, project_id=project_id,
        tags=tags, since=since, limit=limit,
    )


@mcp.tool(description="Read one meeting's complete extracted file content and metadata. Access inherits project membership.")
def get_meeting_summary(meeting_summary_id: str) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.get_meeting_summary(
        user_id=user_id, meeting_summary_id=meeting_summary_id,
    )


@mcp.tool(description="Search project Wiki memory using keyword and semantic retrieval with optional kind, tag, date, and verification filters.")
def search_wiki(
    query: str,
    project_id: str | None = None,
    memory_kinds: list[str] | None = None,
    tags: list[str] | None = None,
    updated_after: str | None = None,
    verified_only: bool = False,
    limit: int = 8,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.search(
        user_id=user_id,
        query=query,
        project_id=project_id,
        memory_kinds=memory_kinds,
        tags=tags,
        updated_after=updated_after,
        verified_only=verified_only,
        limit=limit,
    )


@mcp.tool(description="Read a complete Wiki page including sources, links, validity, version, and verification state.")
def get_page(page_id: str, project_id: str | None = None) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.get_page(user_id=user_id, page_id=page_id, project_id=project_id)


@mcp.tool(description="Traverse incoming and outgoing Wiki relationships from a page, up to depth two.")
def get_related_nodes(
    node_id: str,
    project_id: str | None = None,
    relation: str | None = None,
    depth: int = 1,
    limit: int = 20,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.related(
        user_id=user_id,
        node_id=node_id,
        project_id=project_id,
        relation=relation,
        depth=depth,
        limit=limit,
    )


@mcp.tool(description="Return recently changed Wiki pages, optionally filtered by time and memory kind.")
def get_recent_updates(
    project_id: str | None = None,
    since: str | None = None,
    memory_kinds: list[str] | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.recent(
        user_id=user_id,
        project_id=project_id,
        since=since,
        memory_kinds=memory_kinds,
        limit=limit,
    )


@mcp.tool(description="Retrieve decision records and strategies for a project, with optional topic search.")
def get_decision_records(
    project_id: str | None = None,
    topic: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.decisions(user_id=user_id, project_id=project_id, topic=topic, limit=limit)


@mcp.tool(description="Find failure cases, success cases, and retrospectives relevant to a topic.")
def get_examples(
    topic: str,
    project_id: str | None = None,
    outcome: str = "any",
    limit: int = 8,
) -> dict[str, Any]:
    user_id, _ = _identity()
    return operations.examples(
        user_id=user_id,
        topic=topic,
        project_id=project_id,
        outcome=outcome,
        limit=limit,
    )


@mcp.tool(description="Publish structured memory directly to the project Wiki after scope, project access, source, and content safety checks.")
def propose_memory(
    project_id: str,
    title: str,
    memory_kind: str,
    content: str,
    summary: str = "",
    tags: list[str] | None = None,
    source_page_ids: list[str] | None = None,
) -> dict[str, Any]:
    user_id, scopes = _identity()
    return operations.propose(
        user_id=user_id,
        scopes=scopes,
        project_id=project_id,
        title=title,
        memory_kind=memory_kind,
        content=content,
        summary=summary,
        tags=tags,
        source_page_ids=source_page_ids,
    )


def main() -> None:
    host = _env("WIKI_MCP_HOST", "0.0.0.0")
    port = int(_env("WIKI_MCP_PORT", "8010"))
    allowed_hosts = [
        item.strip()
        for item in _env(
            "WIKI_MCP_ALLOWED_HOSTS",
            "127.0.0.1:*,localhost:*,192.168.10.29:*,wiki-mcp:*",
        ).split(",")
        if item.strip()
    ]
    allowed_origins = [
        item.strip()
        for item in _env(
            "WIKI_MCP_ALLOWED_ORIGINS",
            "http://127.0.0.1:*,http://localhost:*,http://192.168.10.29:*",
        ).split(",")
        if item.strip()
    ]
    mcp.run(
        "streamable-http",
        host=host,
        port=port,
        streamable_http_path="/mcp",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        ),
    )


if __name__ == "__main__":
    main()
