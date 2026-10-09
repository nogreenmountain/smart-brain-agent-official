"""Export/import the exact Image IDs in release-lock; never pull or retag.

Archives remain private. Import verifies archive SHA and every image config
identity before docker load. No host extraction is performed.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tarfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify


def archive_image_ids(path):
    with tarfile.open(path, 'r:*') as t:
        for member in t.getmembers():
            p = PurePosixPath(member.name)
            if p.is_absolute() or '..' in p.parts or member.issym() or member.islnk():
                raise ValueError('unsafe image archive')
        if 'index.json' in t.getnames():
            def blob(desc):
                digest = desc['digest']
                if not digest.startswith('sha256:') or len(digest) != 71:
                    raise ValueError('invalid OCI digest')
                data = t.extractfile('blobs/sha256/' + digest[7:]).read()
                if hashlib.sha256(data).hexdigest() != digest[7:]:
                    raise ValueError('OCI descriptor hash mismatch')
                return json.loads(data)
            def platform_config(desc):
                obj = blob(desc)
                if 'manifests' in obj:
                    candidates = [d for d in obj['manifests'] if d.get('platform', {}).get('os') == 'linux'
                                  and d.get('platform', {}).get('architecture') == 'amd64']
                    if not candidates:
                        raise ValueError('OCI Linux amd64 manifest missing')
                    return platform_config(candidates[0])
                config = blob(obj['config'])
                if config.get('os') != 'linux' or config.get('architecture') != 'amd64':
                    raise ValueError('OCI image platform mismatch')
                return config
            index = json.load(t.extractfile('index.json'))
            for descriptor in index['manifests']:
                platform_config(descriptor)
            # Docker 29/containerd uses manifest/index digest as Image ID.
            return {d['digest'] for d in index['manifests']}
        manifest = t.extractfile('manifest.json')
        if manifest is None:
            raise ValueError('image archive manifest missing')
        ids = set()
        for row in json.load(manifest):
            p = PurePosixPath(row['Config'])
            if p.is_absolute() or '..' in p.parts:
                raise ValueError('unsafe image archive')
            config = t.extractfile(row['Config'])
            if config is None:
                raise ValueError('image configuration missing')
            data = config.read()
            meta = json.loads(data)
            if meta.get('os') != 'linux' or meta.get('architecture') != 'amd64':
                raise ValueError('image platform mismatch')
            ids.add('sha256:' + hashlib.sha256(data).hexdigest())
        return ids


def verify_archive(root, manifest, expected):
    errors = verify.check_bundle(root, manifest)
    files = manifest.get('files', [])
    if len(files) != 1 or files[0].get('path') != 'images.tar':
        errors.append('unexpected image archive layout')
    if set(manifest.get('image_ids', [])) != expected:
        errors.append('bundle release identity mismatch')
    if not errors and archive_image_ids(Path(root) / 'images.tar') != expected:
        errors.append('archive image identities mismatch')
    return errors


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['export', 'verify', 'import'])
    p.add_argument('--directory', required=True)
    p.add_argument('--lock', type=Path, default=verify.HERE / 'release-lock.json', help='Exact full or delta release lock')
    a = p.parse_args()
    lock = json.loads(a.lock.read_text())
    ids = sorted({s['image_id'] for s in lock['services'].values()})
    root = Path(a.directory).resolve()
    errors = verify.check_private_root(verify.ROOT, root)
    if errors:
        print(json.dumps({'ok': False, 'errors': errors})); return 1
    try:
        if a.action == 'export':
            if root.exists():
                raise ValueError('export directory already exists; preserve prior bundle')
            unique = {s['image_id']: s['size_bytes'] for s in lock['services'].values()}
            if shutil.disk_usage(root.parent).free < sum(unique.values()) * 2 + 250 * 2**30:
                raise ValueError('insufficient backup reserve for export')
            errors = verify.check_images(lock['services'], verify.docker_images(lock['services']))
            if errors:
                print(json.dumps({'ok': False, 'errors': errors})); return 1
            root.mkdir(mode=0o700)
            archive = root / 'images.tar'
            with archive.open('xb') as output:
                r = subprocess.run(['docker', 'save', *ids], stdout=output, stderr=subprocess.PIPE, timeout=3600)
            archive.chmod(0o600)
            if r.returncode:
                raise ValueError('export failed; preserve incomplete archive')
            if archive_image_ids(archive) != set(ids):
                raise ValueError('export identity mismatch')
            manifest = {'release': lock['release'], 'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        'image_ids': ids, 'files': [{'path': 'images.tar', 'sha256': verify.file_sha(archive), 'bytes': archive.stat().st_size}]}
            (root / 'bundle-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
            (root / 'bundle-manifest.json').chmod(0o600)
        else:
            manifest = json.loads((root / 'bundle-manifest.json').read_text())
            errors = verify_archive(root, manifest, set(ids))
            if errors:
                print(json.dumps({'ok': False, 'errors': errors})); return 1
            if a.action == 'import':
                info = json.loads(verify.command(['docker', 'info', '--format', '{{json .}}']))
                unique = {s['image_id']: s['size_bytes'] for s in lock['services'].values()}
                if shutil.disk_usage(info['DockerRootDir']).free < sum(unique.values()) + 40 * 2**30:
                    raise ValueError('insufficient Docker reserve for import')
                r = subprocess.run(['docker', 'load', '-i', str(root / 'images.tar')], capture_output=True, timeout=3600)
                if r.returncode:
                    raise ValueError('image import failed; private diagnostics withheld')
                errors = verify.check_images(lock['services'], verify.docker_images(lock['services']))
                if errors:
                    print(json.dumps({'ok': False, 'errors': errors})); return 1
        print(json.dumps({'ok': True, 'action': a.action, 'image_count': len(ids)})); return 0
    except (ValueError, OSError, KeyError, tarfile.TarError, subprocess.TimeoutExpired):
        print(json.dumps({'ok': False, 'errors': ['image bundle operation failed; preserve artifacts and inspect privately']})); return 1


if __name__ == '__main__':
    sys.exit(main())
