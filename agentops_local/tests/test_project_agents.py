import hashlib
import importlib.util
import sys
import types
import uuid
from pathlib import Path

from fastapi.routing import APIRoute

import pytest
from fastapi import HTTPException

def _load_module():
    # The server overlay is loaded as ``agentops`` in production, while the
    # workspace tests keep it under ``agentops_local``. Stub only the auth/ORM
    # dependencies needed to exercise these pure helpers.
    auth = types.ModuleType("agentops.auth.middleware")
    auth.AuthenticatedRoute = APIRoute
    orm = types.ModuleType("agentops.common.orm")
    orm.get_orm_session = lambda: None
    authz = types.ModuleType("agentops.rag.authz")
    authz.AuthzError = Exception
    authz.current_user_id = lambda request: None
    authz.is_system_admin = lambda *args, **kwargs: False
    authz.require_admin = lambda *args, **kwargs: None
    authz.require_member = lambda *args, **kwargs: None
    injected = {
        "agentops": types.ModuleType("agentops"),
        "agentops.auth": types.ModuleType("agentops.auth"),
        "agentops.common": types.ModuleType("agentops.common"),
        "agentops.rag": types.ModuleType("agentops.rag"),
        "agentops.auth.middleware": auth,
        "agentops.common.orm": orm,
        "agentops.rag.authz": authz,
    }
    previous = {name: sys.modules.get(name) for name in injected}
    for name, module in injected.items():
        sys.modules.setdefault(name, module)
    path = Path(__file__).parents[1] / "api/routes/v4/project_agents.py"
    spec = importlib.util.spec_from_file_location("project_agents_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    for name, old in previous.items():
        if old is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = old
    return module


project_agents = _load_module()
AGENTS_FILENAME = project_agents.AGENTS_FILENAME
AGENTS_TEMPLATE_VERSION = project_agents.AGENTS_TEMPLATE_VERSION
build_default_agents = project_agents.build_default_agents
sha256_text = project_agents.sha256_text
validate_agents_filename = project_agents.validate_agents_filename
download_response_headers = project_agents.download_response_headers


def test_default_agents_template_replaces_project_name_and_contains_memory_workflow():
    project_id = uuid.uuid4()
    content = build_default_agents(project_id=project_id, project_name="材料研发")

    assert "# 材料研发 项目协作规则" in content
    assert f"smartbrain-project-id: {project_id}" in content
    assert "company-memory" in content
    assert "对话记录" in content
    assert "user/assistant" in content
    assert f"smartbrain-agents-version: {AGENTS_TEMPLATE_VERSION}" in content


def test_default_agents_is_short_and_keeps_only_the_essential_project_contract():
    content = build_default_agents(project_id=uuid.uuid4(), project_name="材料研发")
    assert len(content.encode("utf-8")) <= 1200
    assert len(content.splitlines()) <= 12
    assert sum(line.startswith("- ") for line in content.splitlines()) <= 3
    assert "user/assistant" in content
    assert "密钥" in content and "个人信息" in content
    assert "停止记录" in content
    assert "验证" in content
    assert "失败" in content


def test_agents_filename_is_strictly_case_sensitive():
    assert validate_agents_filename(AGENTS_FILENAME) is True
    for name in ("agents.md", "AGENTS.MD", "foo/AGENTS.md", "AGENTS.md.bak", None, ""):
        assert validate_agents_filename(name) is False


def test_default_agents_uses_explicit_project_and_delegates_protocol_to_plugin():
    pid = uuid.uuid4()
    content = build_default_agents(project_id=pid, project_name='测试项目')
    assert 'record_project_conversation' in content
    assert f'project_id="{pid}"' in content
    assert '遵循插件规则' in content
    assert '回执' in content
    skill = (Path(__file__).parents[2] / 'plugins/company-memory/skills/company-memory/SKILL.md').read_text(encoding='utf-8')
    for detail in ('submission_id', 'unknown', 'published'):
        assert detail in skill
    assert 'SmartBrain request_id' not in content
    assert '适配器' not in content


def test_sha256_text_matches_standard_digest():
    assert sha256_text("hello") == hashlib.sha256(b"hello").hexdigest()


def test_download_response_headers_are_http_latin1_safe():
    headers = download_response_headers()

    assert "X-SmartBrain-Download-Notice" not in headers
    for value in headers.values():
        value.encode("latin-1")


def test_v4_router_registers_project_agents_endpoints():
    source = (Path(__file__).parents[1] / "api/routes/v4/__init__.py").read_text(encoding="utf-8")
    assert "from .project_agents import client_router as project_agents_client_router" in source
    assert "router.include_router(project_agents_router)" in source
    assert "router.include_router(project_agents_client_router)" in source


def test_client_context_route_is_separate_from_browser_session_router():
    routes = {route.path: route for route in project_agents.client_router.routes}
    route = routes["/projects/{project_id}/context/client"]
    assert route.endpoint.__name__ == "create_client_project_context"
    assert route.path not in {item.path for item in project_agents.router.routes if item.path.endswith("/context")}


def test_project_agents_migration_seeds_existing_projects_without_overwriting_custom_files():
    migration = (Path(__file__).parents[2] / "supabase" / "migrations" / "20260923000000_project_agents_context_conversations.sql").read_text(encoding="utf-8")
    assert "FROM public.projects p" in migration
    assert "ON CONFLICT (project_id) DO NOTHING" in migration
    assert "digest(convert_to(content, 'UTF8'), 'sha256')" in migration
    assert "ADD COLUMN IF NOT EXISTS requested_total" in migration
    assert "requested_total = COALESCE(requested_total, requested_limit)" in migration
    assert "DROP CONSTRAINT IF EXISTS ai_gateway_key_requests_status_check" in migration


class _FakeResult:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class _FakeOrm:
    def __init__(self, rows):
        self.rows = iter(rows)

    def execute(self, *_args, **_kwargs):
        return _FakeResult(next(self.rows))


def test_context_validation_requires_matching_key_and_agents_digest(monkeypatch):
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    key_id = uuid.uuid4()
    token = "sbc_test"
    digest = sha256_text("content")
    row = types.SimpleNamespace(project_id=str(project_id), agents_version=2, agents_sha256=digest)
    agents = types.SimpleNamespace(version=2, sha256=digest)
    monkeypatch.setenv("SB_GATEWAY_REQUIRE_PROJECT_CONTEXT", "true")

    assert project_agents.resolve_gateway_project_context(
        _FakeOrm([row, agents]), user_id=user_id, key_id=key_id, token=token
    ) == project_id

    with pytest.raises(HTTPException) as exc:
        project_agents.resolve_gateway_project_context(
            _FakeOrm([None]), user_id=user_id, key_id=key_id, token=token
        )
    assert exc.value.status_code == 428
