from pathlib import Path
import importlib


ROUTES_INIT = Path(__file__).parents[1] / "api" / "routes" / "v4" / "__init__.py"


def test_personal_gateway_routes_are_registered_in_v4_router() -> None:
    source = ROUTES_INIT.read_text(encoding="utf-8")

    assert "from .ai_gateway import" in source
    assert "ai_gateway_router" in source
    assert "ai_gateway_device_router" in source
    assert "router.include_router(ai_gateway_router)" in source
    assert "router.include_router(ai_gateway_device_router)" in source


def test_gateway_content_projection_does_not_require_optional_daily_access_module() -> None:
    module = importlib.import_module("agentops_local.ai_usage.gateway_content")
    assert module.INLINE_MESSAGE_BYTES > 0
    assert "event_payload" in module.METADATA_SQL


def test_personal_gateway_source_and_proxy_are_present() -> None:
    scope = (Path(__file__).parents[1] / "api" / "personal_gateway_scope.py").read_text(encoding="utf-8")
    proxy = (Path(__file__).parents[1] / "api" / "personal_gateway_proxy.py").read_text(encoding="utf-8")
    assert "app.api_route('/v1/{path:path}'" in scope
    assert "route._gateway_claims" in scope
    assert "_ingest_gateway_events" in proxy
    assert "authorization" in proxy
