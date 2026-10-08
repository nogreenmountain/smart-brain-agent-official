"""Local SmartBrain adapter for Codex/Claude desktop clients.

Adapter marker: 2026-09-24-legacy-agents-compat-r2

The adapter is intentionally small and dependency free.  A separate process
is started for each project directory, so two projects can be used at the same
time without a global "active project" race.  It accepts the API key from the
Codex request (or ``SMARTBRAIN_API_KEY``), refreshes the project context lease
before expiry, and forwards the request with the trusted context header.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Mapping
from urllib.error import HTTPError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import re


REFRESH_SKEW = timedelta(minutes=5)
AGENTS_PROJECT_ID = re.compile(r"^<!--\s*smartbrain-project-id:\s*([0-9a-fA-F-]{16,})\s*-->$", re.MULTILINE)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def inject_context_header(headers: Mapping[str, str], token: str) -> dict[str, str]:
    result = dict(headers)
    result["X-SmartBrain-Project-Context"] = token
    return result


def read_agents_project_id(path: Path) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"找不到项目目录中的 AGENTS.md: {path}") from exc
    match = AGENTS_PROJECT_ID.search(content)
    if not match:
        raise RuntimeError("AGENTS.md 缺少 smartbrain-project-id 元信息，请从项目页面重新下载")
    return match.group(1)


class ContextTokenManager:
    def __init__(
        self,
        *,
        api_base_url: str,
        project_id: str,
        api_key: str,
        cache_path: Path,
        opener: Callable[..., object] = urlopen,
        now: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.project_id = project_id
        self.api_key = api_key
        self.cache_path = cache_path
        self.opener = opener
        self.now = now
        self._lock = threading.Lock()

    def _read_cache(self) -> dict[str, str] | None:
        try:
            value = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, OSError, ValueError):
            return None
        expected_key = hashlib.sha256(self.api_key.encode("utf-8")).hexdigest()[:16]
        if (
            not isinstance(value, dict)
            or value.get("project_id") != self.project_id
            or value.get("key_fingerprint") != expected_key
        ):
            return None
        token = value.get("token")
        expires_at = value.get("expires_at")
        if not isinstance(token, str) or not token or not isinstance(expires_at, str):
            return None
        try:
            if _parse_datetime(expires_at) - self.now() <= REFRESH_SKEW:
                return None
        except ValueError:
            return None
        return {"token": token, "expires_at": expires_at}

    def _write_cache(self, payload: dict[str, str]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix="context-", suffix=".tmp", dir=self.cache_path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(payload, handle, ensure_ascii=False)
            os.replace(temp_name, self.cache_path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass

    def _request(self) -> dict[str, str]:
        url = f"{self.api_base_url}/v4/projects/{self.project_id}/context/client"
        request = Request(
            url,
            method="POST",
            data=b"{}",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with self.opener(request, timeout=20) as response:
                raw = response.read()
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"SmartBrain context refresh failed ({exc.code}): {detail}") from exc
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise RuntimeError("SmartBrain context refresh returned invalid JSON") from exc
        if not isinstance(payload, dict) or not isinstance(payload.get("token"), str):
            raise RuntimeError("SmartBrain context refresh returned no token")
        expires_at = payload.get("expires_at")
        if not isinstance(expires_at, str):
            raise RuntimeError("SmartBrain context refresh returned no expiry")
        return {"project_id": self.project_id, "token": payload["token"], "expires_at": expires_at}

    def ensure(self, *, force: bool = False) -> str:
        with self._lock:
            if not force:
                cached = self._read_cache()
                if cached:
                    return cached["token"]
            payload = self._request()
            payload["key_fingerprint"] = hashlib.sha256(self.api_key.encode("utf-8")).hexdigest()[:16]
            self._write_cache(payload)
            return payload["token"]


@dataclass(frozen=True)
class AdapterConfig:
    api_base_url: str
    project_id: str
    listen_host: str = "127.0.0.1"
    listen_port: int = 8791
    state_dir: Path = Path.home() / ".smartbrain" / "codex-adapter"
    agents_path: Path | None = None


class AdapterHandler(BaseHTTPRequestHandler):
    server_version = "SmartBrainCodexAdapter/1.0"

    def _adapter(self) -> "ProjectAdapter":
        return self.server.adapter  # type: ignore[attr-defined]

    def _json(self, status: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health" or self.path == "/control/status":
            adapter = self._adapter()
            self._json(200, {"ok": True, "project_id": adapter.config.project_id, "listen_port": adapter.config.listen_port})
            return
        self._proxy()

    def do_POST(self) -> None:  # noqa: N802
        self._proxy()

    def _proxy(self) -> None:
        adapter = self._adapter()
        if not self.path.startswith("/v1/") and self.path != "/v1":
            self._json(404, {"error": {"code": "not_found", "message": "adapter route not found"}})
            return
        try:
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            response_status, response_headers, response_body = adapter.forward(
                self.command, self.path, body, dict(self.headers.items())
            )
        except RuntimeError as exc:
            self._json(428, {"error": {"code": "project_context_required", "message": str(exc)}})
            return
        self.send_response(response_status)
        for key, value in response_headers.items():
            if key.lower() in {"content-length", "transfer-encoding", "connection"}:
                continue
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, *_args) -> None:
        return


class ProjectAdapter:
    def __init__(self, config: AdapterConfig, *, opener: Callable[..., object] = urlopen) -> None:
        self.config = config
        self.opener = opener

    def _api_key(self, headers: Mapping[str, str]) -> str:
        authorization = headers.get("Authorization") or headers.get("authorization")
        if authorization and authorization.lower().startswith("bearer "):
            return authorization.split(" ", 1)[1].strip()
        value = os.getenv("SMARTBRAIN_API_KEY", "").strip()
        if value:
            return value
        raise RuntimeError("请在 Codex 适配器环境中配置 SMARTBRAIN_API_KEY 或 Authorization")

    def _manager(self, headers: Mapping[str, str]) -> ContextTokenManager:
        key = self._api_key(headers)
        return ContextTokenManager(
            api_base_url=self.config.api_base_url,
            project_id=self.config.project_id,
            api_key=key,
            cache_path=self.config.state_dir / f"{self.config.project_id}.json",
            opener=self.opener,
        )

    def _validate_local_agents(self) -> None:
        if self.config.agents_path is None:
            return
        try:
            local_project_id = read_agents_project_id(self.config.agents_path)
        except RuntimeError as exc:
            # Older project AGENTS.md files predate the metadata comment.  The
            # adapter was launched with a server-issued project id, so keep
            # those files usable while still rejecting a present mismatch.
            if '缺少 smartbrain-project-id' in str(exc):
                return
            raise
        if local_project_id.lower() != self.config.project_id.lower():
            raise RuntimeError("当前项目目录的 AGENTS.md 与适配器项目不一致，请为每个项目单独启动适配器")

    def forward(self, method: str, path: str, body: bytes, headers: Mapping[str, str]):
        self._validate_local_agents()
        manager = self._manager(headers)
        token = manager.ensure()
        forwarded = inject_context_header(
            {key: value for key, value in headers.items() if key.lower() not in {"host", "content-length"}},
            token,
        )
        remote_base = f"{self.config.api_base_url.rstrip('/')}/v4/personal-api"
        remote_url = urljoin(remote_base + "/", path.lstrip("/"))
        request = Request(remote_url, data=body if method not in {"GET", "HEAD"} else None, method=method, headers=forwarded)
        try:
            with self.opener(request, timeout=120) as response:
                return response.status, dict(response.headers.items()), response.read()
        except HTTPError as exc:
            if exc.code == 428:
                token = manager.ensure(force=True)
                retry_headers = inject_context_header(forwarded, token)
                retry = Request(remote_url, data=body if method not in {"GET", "HEAD"} else None, method=method, headers=retry_headers)
                with self.opener(retry, timeout=120) as response:
                    return response.status, dict(response.headers.items()), response.read()
            return exc.code, dict(exc.headers.items()) if exc.headers else {}, exc.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="SmartBrain per-project Codex adapter")
    parser.add_argument("--api-base-url", required=True)
    parser.add_argument("--project-id")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--listen-host", default="127.0.0.1")
    parser.add_argument("--listen-port", type=int, default=8791)
    parser.add_argument("--state-dir", type=Path, default=Path.home() / ".smartbrain" / "codex-adapter")
    args = parser.parse_args()
    agents_path = args.project_dir / "AGENTS.md"
    try:
        discovered_project_id = read_agents_project_id(agents_path)
    except RuntimeError as exc:
        if args.project_id and '缺少 smartbrain-project-id' in str(exc):
            discovered_project_id = args.project_id
        else:
            raise
    if args.project_id and args.project_id.lower() != discovered_project_id.lower():
        parser.error("--project-id 与项目目录 AGENTS.md 的 smartbrain-project-id 不一致")
    project_id = args.project_id or discovered_project_id
    config = AdapterConfig(
        api_base_url=args.api_base_url,
        project_id=project_id,
        listen_host=args.listen_host,
        listen_port=args.listen_port,
        state_dir=args.state_dir,
        agents_path=agents_path,
    )
    server = ThreadingHTTPServer((config.listen_host, config.listen_port), AdapterHandler)
    server.adapter = ProjectAdapter(config)  # type: ignore[attr-defined]
    print(f"SmartBrain Codex adapter listening on http://{config.listen_host}:{config.listen_port}/v1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
