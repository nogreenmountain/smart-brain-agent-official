import json
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.smartbrain_codex_adapter import ContextTokenManager, inject_context_header, read_agents_project_id


class _Response:
    def __init__(self, payload, *, status=200, headers=None):
        self.payload = json.dumps(payload).encode("utf-8") if isinstance(payload, dict) else payload
        self.status = status
        self.headers = headers or {"Content-Type": "application/json"}

    def getcode(self):
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.payload


def test_context_manager_caches_and_refreshes_before_expiry(tmp_path: Path):
    calls = []

    def opener(request, timeout):
        calls.append((request.full_url, dict(request.header_items()), request.data))
        return _Response({
            "project_id": "p1",
            "token": f"sbc_{len(calls)}",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
            "refresh_after": (datetime.now(timezone.utc) + timedelta(hours=7, minutes=55)).isoformat(),
        })

    manager = ContextTokenManager(
        api_base_url="https://brain.example",
        project_id="p1",
        api_key="sbk_test",
        cache_path=tmp_path / "token.json",
        opener=opener,
    )
    assert manager.ensure() == "sbc_1"
    assert manager.ensure() == "sbc_1"
    assert len(calls) == 1

    cached = json.loads((tmp_path / "token.json").read_text(encoding="utf-8"))
    cached["key_fingerprint"] = hashlib.sha256(b"sbk_test").hexdigest()[:16]
    cached["expires_at"] = (datetime.now(timezone.utc) + timedelta(minutes=2)).isoformat()
    (tmp_path / "token.json").write_text(json.dumps(cached), encoding="utf-8")
    assert manager.ensure() == "sbc_2"
    assert len(calls) == 2
    assert calls[0][0].endswith("/v4/projects/p1/context/client")


def test_inject_context_header_does_not_mutate_authorization():
    headers = {"Authorization": "Bearer sbk_test", "Content-Type": "application/json"}
    result = inject_context_header(headers, "sbc_test")
    assert result["Authorization"] == "Bearer sbk_test"
    assert result["X-SmartBrain-Project-Context"] == "sbc_test"
    assert "X-SmartBrain-Project-Context" not in headers


def test_adapter_reads_project_id_from_agents_metadata(tmp_path: Path):
    path = tmp_path / "AGENTS.md"
    path.write_text("# demo\n<!-- smartbrain-project-id: 12345678-1234-1234-1234-123456789abc -->\n", encoding="utf-8")
    assert read_agents_project_id(path) == "12345678-1234-1234-1234-123456789abc"


def test_adapter_accepts_legacy_agents_without_metadata_when_project_id_is_explicit(tmp_path: Path):
    calls = []
    agents_path = tmp_path / "AGENTS.md"
    agents_path.write_text("# legacy project rules\n", encoding="utf-8")

    def opener(request, timeout):
        calls.append(request)
        if request.full_url.endswith("/context/client"):
            return _Response({
                "project_id": "p1",
                "token": "sbc_legacy",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
            })
        return _Response(b'{"id":"legacy_resp"}')

    from tools.smartbrain_codex_adapter import AdapterConfig, ProjectAdapter

    adapter = ProjectAdapter(
        AdapterConfig("https://brain.example", "p1", state_dir=tmp_path, agents_path=agents_path),
        opener=opener,
    )
    status, _headers, body = adapter.forward(
        "POST", "/v1/responses", b'{"model":"gpt-5.6-luna"}', {"Authorization": "Bearer sbk_test"}
    )
    assert status == 200
    assert body == b'{"id":"legacy_resp"}'
    assert calls[1].headers["X-smartbrain-project-context"] == "sbc_legacy"


def test_project_adapter_injects_cached_context_into_each_forwarded_request(tmp_path: Path):
    calls = []

    def opener(request, timeout):
        calls.append(request)
        if request.full_url.endswith("/context/client"):
            return _Response({
                "project_id": "p1",
                "token": "sbc_context",
                "expires_at": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
            })
        return _Response(b'{"id":"resp_1"}')

    from tools.smartbrain_codex_adapter import AdapterConfig, ProjectAdapter

    adapter = ProjectAdapter(AdapterConfig("https://brain.example", "p1", state_dir=tmp_path), opener=opener)
    status, _headers, body = adapter.forward(
        "POST", "/v1/responses", b'{"model":"gpt-5.6-luna"}', {"Authorization": "Bearer sbk_test", "Content-Type": "application/json"}
    )
    assert status == 200
    assert body == b'{"id":"resp_1"}'
    assert calls[1].full_url.endswith("/v4/personal-api/v1/responses")
    assert calls[1].headers["X-smartbrain-project-context"] == "sbc_context"
