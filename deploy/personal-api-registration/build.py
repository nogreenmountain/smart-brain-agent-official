"""Build the two-file overlay after the new backup is independently verified."""
import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path('/srv/smartbrain/releases/personal-api-registration-20261019-r1')


def main():
    sys.path.insert(0, str(ROOT))
    from release import Ops, OLD, IMAGE, PROXY_SHA
    ops = Ops()
    evidence = ROOT / 'evidence'
    with ops.helper.acquire_locks():
        assert not (evidence / 'build-intent.json').exists(), 'existing build attempt; observe instead'
        gates = ops.gates()
        current = ops.helper.inspect(OLD)
        assert current['Image'] == IMAGE and current['State']['Running']
        assert ops.helper.source_sha(OLD) == PROXY_SHA
        ops.helper.validate_unit(OLD)
        sources = {name: hashlib.sha256((ROOT / 'input' / name).read_bytes()).hexdigest()
                   for name in ('personal_gateway_scope.py', 'personal_gateway_app.py')}
        base_tag = 'smartbrain/local-personal-registration-base:20261019-28cd0714'
        tag = 'smartbrain/personal-key-api:2026.10.19-registration-r1'
        assert not ops.helper.container_exists(tag), 'candidate tag already exists'
        ops.base.core.atomic_write_json(evidence / 'build-intent.json', {
            'at': datetime.now(timezone.utc).isoformat(), 'base_image': IMAGE,
            'tag': tag, 'sources': sources, 'gates': gates})
        ops.base.run(['docker', 'tag', IMAGE, base_tag])
        assert ops.helper.inspect(base_tag)['Id'] == IMAGE
        with (evidence / 'build.log').open('wb') as log:
            result = subprocess.run(['docker', 'build', '--pull=false', '--network=none',
                                     '--build-arg', 'BASE_IMAGE=' + base_tag, '-t', tag,
                                     str(ROOT / 'input')], stdout=log, stderr=subprocess.STDOUT, timeout=240)
        assert result.returncode == 0, 'candidate build failed; inspect retained log'
        image = ops.helper.inspect(tag)['Id']
        ops.gates()
        value = {'at': datetime.now(timezone.utc).isoformat(), 'base_image': IMAGE,
                 'image': image, 'tag': tag, 'sources': sources, 'build_exit': 0}
        ops.base.core.atomic_write_json(evidence / 'build-verified.json', value)
        print(json.dumps(value))


if __name__ == '__main__':
    main()
