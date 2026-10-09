"""Read-only deployment verification. Python 3.12+, standard library only.

All diagnostics identify names and paths, never private environment values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def check_images(expected, actual):
    errors = []
    for name, row in expected.items():
        image = actual.get(name)
        if image is None:
            errors.append(f'image missing: {name}')
        elif image.get('Id') != row['image_id']:
            errors.append(f'image identity mismatch: {name}')
        elif image.get('Os', '') + '/' + image.get('Architecture', '') != row['platform']:
            errors.append(f'image platform mismatch: {name}')
    return errors


def check_resources(limits, actual):
    return ['resource below reserve: ' + name for name, threshold in limits.items()
            if name.startswith('min_') and actual.get(name[4:], -1) < threshold]


def check_private_root(repo, private):
    p = Path(private).resolve()
    if p == Path(repo).resolve() or p.is_relative_to(Path(repo).resolve()):
        return ['private root must be outside checkout']
    return []


def read_env(path):
    values, errors = {}, []
    if not Path(path).is_file():
        return values, ['environment file missing: ' + Path(path).name]
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        k, sep, value = line.partition('=')
        k = k.strip()
        if not sep or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k):
            errors.append('invalid environment syntax: ' + Path(path).name)
        elif k in values:
            errors.append(f'duplicate environment name: {Path(path).name}:{k}')
        else:
            values[k] = value
    return values, errors


def check_env(path, required):
    values, errors = read_env(path)
    for name in required:
        if name not in values or not values[name]:
            errors.append(f'missing environment name: {Path(path).name}:{name}')
        elif '__SET_' in values[name] or values[name].startswith(('CHANGE_ME', 'REPLACE_')):
            errors.append(f'unconfigured environment name: {Path(path).name}:{name}')
    # Even optional populated placeholders must be resolved or explicitly empty.
    for name, value in values.items():
        if name not in required and '__SET_' in value:
            errors.append(f'unconfigured environment name: {Path(path).name}:{name}')
    return errors


def safe_path(root, name):
    p = Path(name)
    root = Path(root).resolve()
    if p.is_absolute() or '..' in p.parts or not (root / p).resolve().is_relative_to(root):
        raise ValueError('unsafe bundle path')
    return root / p


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def check_bundle(root, manifest):
    errors = []
    for row in manifest.get('files', []):
        try:
            p = safe_path(root, row['path'])
        except ValueError:
            errors.append('unsafe bundle path')
            continue
        if not p.is_file():
            errors.append('bundle file missing: ' + row['path'])
        elif file_sha(p) != row['sha256']:
            errors.append('bundle hash mismatch: ' + row['path'])
    return errors


def check_sources(repo):
    here = Path(repo) / 'deploy/current'
    manifest = json.loads((here / 'runtime-source-manifest.json').read_text(encoding='utf-8'))
    errors = []
    for role, row in manifest['components'].items():
        for name, sha in row['python_sources'].items():
            p = safe_path(here / 'runtime-sources' / role / 'agentops', name)
            if not p.is_file() or file_sha(p) != sha:
                errors.append(f'runtime source changed: {role}/{name}')
    for name, sha in manifest.get('configuration_files', {}).items():
        p = safe_path(here, name)
        if not p.is_file() or file_sha(p) != sha:
            errors.append('deployment configuration changed: ' + name)
    return errors


def check_receipt(path, mode):
    if not Path(path).is_file():
        return ['restoration receipt missing']
    d = json.loads(Path(path).read_text(encoding='utf-8'))
    checks = ('postgres', 'clickhouse', 'files', 'roles', 'authorization', 'secrets')
    if d.get('mode') != mode or d.get('verified') is not True or any(d.get(k) is not True for k in checks):
        return ['restoration receipt incomplete or unverified']
    if not d.get('evidence_directory') or not d.get('verified_at'):
        return ['restoration receipt lacks evidence identity']
    return []


def command(args):
    try:
        r = subprocess.run(args, capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError('external command unavailable or timed out') from None
    if r.returncode:
        # Docker errors can contain rendered secrets; never echo stdout/stderr.
        raise ValueError('external command failed; inspect private diagnostics locally')
    return r.stdout


def docker_images(services):
    actual = {}
    for name, row in services.items():
        try:
            actual[name] = json.loads(command(['docker', 'image', 'inspect', row['image_id']]))[0]
        except ValueError:
            pass
    return actual


def available_memory():
    if Path('/proc/meminfo').exists():
        m = re.search(r'^MemAvailable:\s+(\d+) kB', Path('/proc/meminfo').read_text(), re.M)
        return int(m.group(1)) * 1024 if m else 0
    return 0  # Deployment preflight requires a Linux Docker host.


def check_mount_paths(config):
    errors = []
    for name, service in config['services'].items():
        for mount in service.get('volumes', []):
            if mount.get('type') == 'bind' and not Path(mount['source']).exists():
                errors.append(f"bind mount source missing: {name}:{mount['target']}")
    return errors


def preflight(config, mode, profiles):
    settings, errors = read_env(config)
    for k in ('PRIVATE_ROOT', 'STATE_ROOT', 'BACKUP_ROOT', 'PUBLIC_HOST', 'PERSONAL_UPSTREAM_URL'):
        if not settings.get(k) or '__SET_' in settings[k]:
            errors.append('deployment setting missing: ' + k)
    if errors:
        return errors
    private = Path(settings['PRIVATE_ROOT'])
    errors += check_private_root(ROOT, private)
    errors += check_private_root(ROOT, settings['STATE_ROOT'])
    if sys.platform != 'linux':
        errors.append('deployment preflight requires Linux host')
    lock = json.loads((HERE / 'release-lock.json').read_text())
    selected = {n: s for n, s in lock['services'].items() if not s.get('profiles') or set(s['profiles']) & set(profiles)}
    for n, s in selected.items():
        errors += check_env(private / 'env' / (n + '.env'), s.get('required_env', []))
    for name in lock['required_private_files']:
        if not (private / name).is_file():
            errors.append('private prerequisite missing: ' + name)
    for name in lock['state_directories']:
        if not (Path(settings['STATE_ROOT']) / name).is_dir():
            errors.append('state directory missing: ' + name)
    errors += check_receipt(private / 'restoration.json', mode)
    errors += check_sources(ROOT)
    if errors:
        return errors
    profile_args = [arg for profile in profiles for arg in ('--profile', profile)]
    rendered = json.loads(command(['docker', 'compose', '--env-file', str(Path(config).resolve()), '-f', str(HERE / 'compose.yaml'), *profile_args, 'config', '--format', 'json']))
    errors += check_mount_paths(rendered)
    if set(rendered['services']) - set(lock['services']):
        errors.append('unlocked compose services present')
    for n, s in rendered['services'].items():
        if s['image'] != lock['services'][n]['image_id']:
            errors.append('compose image changed: ' + n)
    errors += check_images(selected, docker_images(selected))
    info = json.loads(command(['docker', 'info', '--format', '{{json .}}']))
    if not info.get('ServerVersion', '').startswith('29.'):
        errors.append('exact image identity requires Docker Engine 29.x containerd store')
    if 'rag' in profiles and 'nvidia' not in info.get('Runtimes', {}):
        errors.append('RAG GPU runtime missing: nvidia')
    actual = {'memory_available_bytes': available_memory(),
              'docker_free_bytes': shutil.disk_usage(info['DockerRootDir']).free,
              'data_free_bytes': shutil.disk_usage(settings['STATE_ROOT']).free,
              'backup_free_bytes': shutil.disk_usage(settings.get('BACKUP_ROOT', settings['STATE_ROOT'])).free}
    errors += check_resources(lock['resource_reserves'], actual)
    return errors


def smoke(base):
    errors = []
    for path, status in [('/login', 200), ('/workday', 200), ('/health/ready', 200),
                         ('/v4/ai-gateway/keys', 401), ('/v4/personal-api/v1/models', 401),
                         ('/downloads/smartbrain_codex_adapter.py', 410)]:
        req = urllib.request.Request(base.rstrip('/') + path)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                code = response.status
        except urllib.error.HTTPError as e:
            code = e.code
        except (OSError, urllib.error.URLError):
            code = 0
        if code != status:
            errors.append(f'HTTP contract failed: {path}: expected {status}, got {code}')
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['sources', 'images', 'bundle', 'preflight', 'smoke'])
    p.add_argument('--config', default=str(HERE / '.env'))
    p.add_argument('--mode', choices=['restore', 'fresh'], default='restore')
    p.add_argument('--profiles', default='')
    p.add_argument('--bundle-root')
    p.add_argument('--url')
    a = p.parse_args()
    try:
        lock = json.loads((HERE / 'release-lock.json').read_text())
        if a.action == 'sources':
            errors = check_sources(ROOT)
        elif a.action == 'images':
            errors = check_images(lock['services'], docker_images(lock['services']))
        elif a.action == 'bundle':
            if not a.bundle_root:
                raise ValueError('--bundle-root required')
            errors = check_bundle(a.bundle_root, json.loads((Path(a.bundle_root) / 'bundle-manifest.json').read_text()))
        elif a.action == 'preflight':
            errors = preflight(a.config, a.mode, a.profiles.split(',') if a.profiles else [])
        else:
            if not a.url:
                raise ValueError('--url required')
            errors = smoke(a.url)
    except (ValueError, KeyError, OSError, json.JSONDecodeError):
        errors = ['invalid or missing prerequisite; inspect private files locally']
    print(json.dumps({'action': a.action, 'ok': not errors, 'errors': errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
