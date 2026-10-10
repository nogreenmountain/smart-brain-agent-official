"""Rebuild the existing installer bundle with the current company-memory skill."""
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / 'plugins/company-memory'
BUNDLE = ROOT / 'smartbrain-dashboard/public/downloads/smartbrain-company-memory-codex.zip'
MARKETPLACE = {
    'name': 'smartbrain',
    'interface': {'displayName': 'SmartBrain'},
    'plugins': [{
        'name': 'company-memory',
        'source': {'source': 'local', 'path': './plugins/company-memory'},
        'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'},
        'category': 'Productivity',
    }],
}

if __name__ == '__main__':
    with ZipFile(BUNDLE, 'w', ZIP_DEFLATED) as archive:
        archive.writestr('.agents/plugins/marketplace.json', json.dumps(MARKETPLACE, indent=2))
        for path in sorted(PLUGIN.rglob('*')):
            if path.is_file() and not path.is_symlink():
                archive.write(path, 'plugins/company-memory/' + path.relative_to(PLUGIN).as_posix())
    with ZipFile(BUNDLE) as archive:
        assert archive.testzip() is None
        manifest = json.loads(archive.read('plugins/company-memory/.codex-plugin/plugin.json'))
        assert manifest['version'] == '0.2.0+codex.20261008'
        for path in PLUGIN.rglob('*'):
            if path.is_file():
                assert archive.read('plugins/company-memory/' + path.relative_to(PLUGIN).as_posix()) == path.read_bytes()
    print('Plugin installer structure and source bytes verified: ' + manifest['version'])
