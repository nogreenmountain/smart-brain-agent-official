"""Local, review-first dispatch for the relay-auth production runners."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import pathlib
import re
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import relay_release_core as core


HERE = pathlib.Path(__file__).resolve().parent
CORE_SOURCE = HERE / "relay_release_core.py"
RUNNER_SOURCE = HERE / "relay_remote_runner.py"
REMOTE_RELEASE = "/srv/smartbrain/releases/personal-api-public-only-20261018-r1"
REMOTE_TOOLING = REMOTE_RELEASE + "/release-tooling"
REMOTE_CORE = REMOTE_TOOLING + "/relay_release_core.py"
REMOTE_RUNNER = REMOTE_TOOLING + "/relay_remote_runner.py"
REMOTE_MANIFEST = REMOTE_TOOLING + "/installed-manifest.json"
REMOTE_STAGE = REMOTE_RELEASE + "/evidence/release-stage.json"
REMOTE_SMOKE = REMOTE_RELEASE + "/evidence/authenticated-smoke-receipt.json"
REMOTE_FRESH_BACKUP = REMOTE_RELEASE + "/evidence/fresh-backup-receipt.json"
REMOTE_WINDOWS_READY = REMOTE_RELEASE + "/evidence/windows-ready-receipt.json"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_manifest() -> tuple[dict[str, Any], bytes, bytes]:
    core_bytes = CORE_SOURCE.read_bytes()
    runner_bytes = RUNNER_SOURCE.read_bytes()
    manifest = {
        "schema": "smartbrain.personal-relay-release-tooling/v1",
        "release": core.RELEASE,
        "core_sha256": _sha(core_bytes),
        "core_length": len(core_bytes),
        "runner_sha256": _sha(runner_bytes),
        "runner_length": len(runner_bytes),
    }
    return manifest, core_bytes, runner_bytes


def _validate_attempt_id(value: str) -> str:
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z", value):
        raise ValueError("attempt_id must use YYYYMMDDTHHMMSSZ")
    return value


def build_dispatch_program(
    action: str,
    *,
    smoke_timeout_seconds: int = 300,
    attempt_id: str | None = None,
    backup_receipt: Mapping[str, Any] | None = None,
    windows_receipt: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, Any]]:
    if action not in {"promote", "recover", "finalize"}:
        raise ValueError("unsupported remote action")
    if smoke_timeout_seconds < 60 or smoke_timeout_seconds > 900:
        raise ValueError("smoke timeout must be between 60 and 900 seconds")
    attempt = _validate_attempt_id(
        attempt_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    )
    manifest, core_bytes, runner_bytes = source_manifest()
    backup_bytes = b""
    windows_bytes = b""
    if action == "promote":
        if not isinstance(backup_receipt, Mapping) or not isinstance(windows_receipt, Mapping):
            raise ValueError("promote dispatch requires both gate receipts")
        core.reject_raw_secrets(backup_receipt)
        core.reject_raw_secrets(windows_receipt)
        if (
            backup_receipt.get("schema") != core.FRESH_BACKUP_SCHEMA
            or backup_receipt.get("release") != core.RELEASE
            or windows_receipt.get("schema") != core.WINDOWS_READY_SCHEMA
            or windows_receipt.get("release") != core.RELEASE
        ):
            raise core.GateError("gate receipt identity is invalid")
        backup_bytes = (
            json.dumps(backup_receipt, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
            + b"\n"
        )
        windows_bytes = (
            json.dumps(windows_receipt, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8")
            + b"\n"
        )
    unit = f"smartbrain-personal-public-only-{action}-20261018-r1-{attempt}"
    runner_args = [action]
    if action == "promote":
        runner_args.extend(["--smoke-timeout", str(smoke_timeout_seconds)])
    elif action == "recover":
        runner_args.extend(["--reason", "operator-requested"])

    payload = {
        "manifest": manifest,
        "core_b64": base64.b64encode(core_bytes).decode("ascii"),
        "runner_b64": base64.b64encode(runner_bytes).decode("ascii"),
        "remote_release": REMOTE_RELEASE,
        "remote_tooling": REMOTE_TOOLING,
        "remote_core": REMOTE_CORE,
        "remote_runner": REMOTE_RUNNER,
        "remote_manifest": REMOTE_MANIFEST,
        "unit": unit,
        "runner_args": runner_args,
        "remote_fresh_backup": REMOTE_FRESH_BACKUP,
        "remote_windows_ready": REMOTE_WINDOWS_READY,
        "backup_receipt_b64": base64.b64encode(backup_bytes).decode("ascii"),
        "backup_receipt_sha256": _sha(backup_bytes) if backup_bytes else "",
        "windows_receipt_b64": base64.b64encode(windows_bytes).decode("ascii"),
        "windows_receipt_sha256": _sha(windows_bytes) if windows_bytes else "",
    }
    encoded = base64.b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    program = f'''import base64, hashlib, json, os, pathlib, subprocess, tempfile
EXPECTED_CORE_SHA256={manifest["core_sha256"]!r}
EXPECTED_RUNNER_SHA256={manifest["runner_sha256"]!r}
EXPECTED_FRESH_BACKUP_PATH={REMOTE_FRESH_BACKUP!r}
EXPECTED_WINDOWS_READY_PATH={REMOTE_WINDOWS_READY!r}
EXPECTED_BACKUP_RECEIPT_SHA256={(_sha(backup_bytes) if backup_bytes else "")!r}
EXPECTED_WINDOWS_RECEIPT_SHA256={(_sha(windows_bytes) if windows_bytes else "")!r}
p=json.loads(base64.b64decode({encoded!r}))

def atomic(path, data, mode):
    path=pathlib.Path(path);path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.'+path.name+'.',dir=str(path.parent))
    tmp_path=pathlib.Path(tmp)
    try:
        with os.fdopen(fd,'wb') as handle:
            handle.write(data);handle.flush();os.fsync(handle.fileno())
        os.chmod(tmp_path,mode);os.replace(tmp_path,path)
        directory=os.open(str(path.parent),os.O_RDONLY)
        try: os.fsync(directory)
        finally: os.close(directory)
    finally:
        if tmp_path.exists(): tmp_path.unlink()

core_bytes=base64.b64decode(p['core_b64']);runner_bytes=base64.b64decode(p['runner_b64'])
manifest=p['manifest'];manifest_path=pathlib.Path(p['remote_manifest'])
if manifest['core_sha256']!=EXPECTED_CORE_SHA256 or hashlib.sha256(core_bytes).hexdigest()!=EXPECTED_CORE_SHA256: raise RuntimeError('core payload SHA mismatch')
if manifest['runner_sha256']!=EXPECTED_RUNNER_SHA256 or hashlib.sha256(runner_bytes).hexdigest()!=EXPECTED_RUNNER_SHA256: raise RuntimeError('runner payload SHA mismatch')
if manifest_path.exists():
    installed=json.loads(manifest_path.read_text())
    if installed!=manifest: raise RuntimeError('installed release tooling differs; do not overwrite')
    if hashlib.sha256(pathlib.Path(p['remote_core']).read_bytes()).hexdigest()!=manifest['core_sha256']: raise RuntimeError('installed core drift')
    if hashlib.sha256(pathlib.Path(p['remote_runner']).read_bytes()).hexdigest()!=manifest['runner_sha256']: raise RuntimeError('installed runner drift')
else:
    if p['runner_args'][0]!='promote': raise RuntimeError('release tooling must be installed by the promote dispatch')
    atomic(p['remote_core'],core_bytes,0o700);atomic(p['remote_runner'],runner_bytes,0o700)
    atomic(p['remote_manifest'],(json.dumps(manifest,sort_keys=True,indent=2)+'\\n').encode(),0o600)
if p['runner_args'][0]=='promote':
    if p['remote_fresh_backup']!=EXPECTED_FRESH_BACKUP_PATH or p['remote_windows_ready']!=EXPECTED_WINDOWS_READY_PATH: raise RuntimeError('gate receipt path mismatch')
    if p['backup_receipt_sha256']!=EXPECTED_BACKUP_RECEIPT_SHA256 or p['windows_receipt_sha256']!=EXPECTED_WINDOWS_RECEIPT_SHA256: raise RuntimeError('gate receipt expected SHA mismatch')
    backup_bytes=base64.b64decode(p['backup_receipt_b64']);windows_bytes=base64.b64decode(p['windows_receipt_b64'])
    if hashlib.sha256(backup_bytes).hexdigest()!=p['backup_receipt_sha256']: raise RuntimeError('backup receipt payload SHA mismatch')
    if hashlib.sha256(windows_bytes).hexdigest()!=p['windows_receipt_sha256']: raise RuntimeError('Windows receipt payload SHA mismatch')
    for path,data,digest in ((p['remote_fresh_backup'],backup_bytes,p['backup_receipt_sha256']),
                             (p['remote_windows_ready'],windows_bytes,p['windows_receipt_sha256'])):
        target=pathlib.Path(path)
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()!=digest: raise RuntimeError('installed gate receipt differs; do not overwrite')
        else: atomic(target,data,0o600)
command=['/usr/bin/systemd-run','--unit='+p['unit'],'--property=Type=oneshot','--property=UMask=0077',
         '--property=TimeoutStartSec=3600','--property=TimeoutStopSec=infinity','--property=KillMode=mixed',
         '--property=RemainAfterExit=yes','--no-block',
         '/usr/bin/python3',p['remote_runner']]+p['runner_args']
result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
if result.returncode: raise RuntimeError('systemd-run dispatch failed')
print(json.dumps({{'release':manifest['release'],'unit':p['unit'],'action':p['runner_args'][0],
                  'core_sha256':manifest['core_sha256'],'runner_sha256':manifest['runner_sha256']}}))
'''
    return program, {**manifest, "unit": unit, "action": action}


def build_status_program() -> str:
    manifest, _, _ = source_manifest()
    encoded = base64.b64encode(json.dumps(manifest, separators=(",", ":")).encode()).decode()
    return f'''import base64, hashlib, json, pathlib, subprocess
expected=json.loads(base64.b64decode({encoded!r}))
manifest_path=pathlib.Path({REMOTE_MANIFEST!r})
if not manifest_path.is_file(): raise RuntimeError('release tooling is not installed')
installed=json.loads(manifest_path.read_text())
if installed!=expected: raise RuntimeError('installed release tooling differs from local review')
if hashlib.sha256(pathlib.Path({REMOTE_CORE!r}).read_bytes()).hexdigest()!=expected['core_sha256']: raise RuntimeError('installed core drift')
if hashlib.sha256(pathlib.Path({REMOTE_RUNNER!r}).read_bytes()).hexdigest()!=expected['runner_sha256']: raise RuntimeError('installed runner drift')
result=subprocess.run(['/usr/bin/python3',{REMOTE_RUNNER!r},'status'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
if result.returncode: raise RuntimeError('remote status failed')
print(result.stdout.decode(),end='')
'''


def build_smoke_receipt_program(receipt: Mapping[str, Any]) -> str:
    core.reject_raw_secrets(receipt)
    if receipt.get("schema") != core.AUTH_SMOKE_SCHEMA or receipt.get("release") != core.RELEASE:
        raise core.GateError("authenticated smoke receipt identity is invalid")
    # Structural checks that do not depend on the remote awaiting timestamp.
    if receipt.get("direct_windows_models_status") != 403 or receipt.get("public_gateway_authenticated") is not True or receipt.get("credential_fingerprint_unchanged") is not True:
        raise core.GateError("authenticated smoke receipt must prove public success and direct denial")
    if not isinstance(receipt.get("new_container_id"), str) or not receipt["new_container_id"]:
        raise core.GateError("authenticated smoke receipt container identity is missing")
    digest = receipt.get("request_id_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise core.GateError("authenticated smoke receipt request id SHA is invalid")
    receipt_bytes = json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    encoded = base64.b64encode(receipt_bytes).decode("ascii")
    return f'''import base64, hashlib, importlib.util, json, pathlib, sys
tooling=pathlib.Path({REMOTE_TOOLING!r});sys.path.insert(0,str(tooling))
import relay_release_core as core
stage=core.StageStore(pathlib.Path({REMOTE_STAGE!r})).read()
if not stage or stage.get('stage')!='awaiting_smoke': raise RuntimeError('release is not awaiting authenticated smoke')
receipt=json.loads(base64.b64decode({encoded!r}))
core.validate_auth_smoke_receipt(receipt,now=core.utc_now(),
    awaiting_at=core.parse_timestamp(stage.get('awaiting_smoke_at'),'stage awaiting_smoke_at'),
    new_container_id=stage.get('new_id'))
core.atomic_write_json(pathlib.Path({REMOTE_SMOKE!r}),receipt)
print(json.dumps({{'release':core.RELEASE,'status':'authenticated-smoke-receipt-installed',
                  'new_id':stage.get('new_id'),'request_id_sha256':receipt['request_id_sha256']}}))
'''


def _default_remote(program: str, timeout: int) -> bytes:
    root = pathlib.Path(__file__).resolve().parents[2]
    helper = root / ".artifacts" / "ai-workspace-records-scroll-20261008"
    import sys

    sys.path.insert(0, str(helper))
    from remote_io import remote

    return remote(program, timeout=timeout)


def _invoke_remote(
    remote_fn: Callable[..., bytes] | None,
    program: str,
    *,
    timeout: int,
) -> bytes:
    function = remote_fn or _default_remote
    return function(program, timeout=timeout)


def promote_main(
    argv: list[str] | None = None,
    *,
    remote_fn: Callable[..., bytes] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="Guarded relay-auth promotion dispatcher")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--smoke-timeout", type=int, default=300)
    parser.add_argument("--backup-receipt", type=pathlib.Path)
    parser.add_argument("--windows-receipt", type=pathlib.Path)
    args = parser.parse_args(argv)
    if args.status:
        print(_invoke_remote(remote_fn, build_status_program(), timeout=60).decode(errors="replace"))
        return 0
    if not args.execute:
        print("review-only: refusing remote work; pass --execute after every receipt gate is ready")
        return 2
    if args.backup_receipt is None or args.windows_receipt is None:
        parser.error("--backup-receipt and --windows-receipt are required with --execute")
    backup_receipt = json.loads(args.backup_receipt.read_text(encoding="utf-8"))
    windows_receipt = json.loads(args.windows_receipt.read_text(encoding="utf-8"))
    program, _ = build_dispatch_program(
        "promote",
        smoke_timeout_seconds=args.smoke_timeout,
        backup_receipt=backup_receipt,
        windows_receipt=windows_receipt,
    )
    print(_invoke_remote(remote_fn, program, timeout=90).decode(errors="replace"))
    return 0


def recovery_main(
    argv: list[str] | None = None,
    *,
    remote_fn: Callable[..., bytes] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="Idempotent relay-auth recovery dispatcher")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args(argv)
    if args.status:
        print(_invoke_remote(remote_fn, build_status_program(), timeout=60).decode(errors="replace"))
        return 0
    if not args.execute:
        print("review-only: refusing remote recovery; pass --execute after inspecting the release stage")
        return 2
    program, _ = build_dispatch_program("recover")
    print(_invoke_remote(remote_fn, program, timeout=90).decode(errors="replace"))
    return 0


def finalize_main(
    argv: list[str] | None = None,
    *,
    remote_fn: Callable[..., bytes] | None = None,
) -> int:
    parser = argparse.ArgumentParser(description="Install a secret-free authenticated smoke receipt")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--receipt", type=pathlib.Path)
    args = parser.parse_args(argv)
    if not args.execute:
        print("review-only: refusing remote receipt installation; pass --execute with --receipt")
        return 2
    if args.receipt is None:
        parser.error("--receipt is required with --execute")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    program = build_smoke_receipt_program(receipt)
    print(_invoke_remote(remote_fn, program, timeout=60).decode(errors="replace"))
    return 0
