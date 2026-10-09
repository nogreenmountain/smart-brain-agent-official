import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('image_bundle', ROOT / 'deploy/current/images.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def make_tar(p, config_path='config.json'):
    config = b'{"architecture":"amd64","os":"linux","rootfs":{"type":"layers","diff_ids":[]}}'
    manifest = json.dumps([{'Config': config_path, 'RepoTags': None, 'Layers': []}]).encode()
    with tarfile.open(p, 'w') as t:
        for n, b in [('manifest.json', manifest), (config_path, config)]:
            member = tarfile.TarInfo(n); member.size = len(b); t.addfile(member, io.BytesIO(b))
    return 'sha256:' + hashlib.sha256(config).hexdigest()


def test_oci_identity_is_config_hash_not_tag(tmp_path):
    p = tmp_path / 'images.tar'; expected = make_tar(p)
    assert m.archive_image_ids(p) == {expected}


def test_unsafe_archive_member_rejected(tmp_path):
    p = tmp_path / 'images.tar'; make_tar(p, '../outside.json')
    import pytest
    with pytest.raises(ValueError, match='unsafe image archive'):
        m.archive_image_ids(p)


def test_tamper_and_unexpected_image_refuse_load(tmp_path):
    p = tmp_path / 'images.tar'; image = make_tar(p)
    manifest = {'files': [{'path': 'images.tar', 'sha256': '0' * 64}], 'image_ids': [image]}
    assert m.verify_archive(tmp_path, manifest, {image})
    manifest['files'][0]['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
    assert m.verify_archive(tmp_path, manifest, {'sha256:' + 'f' * 64})
    assert m.verify_archive(tmp_path, manifest, {image}) == []


def test_docker_29_oci_identity_uses_root_index_digest(tmp_path):
    p = tmp_path / 'oci.tar'
    config = b'{"architecture":"amd64","os":"linux"}'
    blobs = {}
    def add(b):
        sha = hashlib.sha256(b).hexdigest(); blobs['blobs/sha256/' + sha] = b
        return {'digest': 'sha256:' + sha, 'size': len(b)}
    config_ref = add(config)
    manifest_ref = add(json.dumps({'config': config_ref, 'layers': []}).encode())
    manifest_ref['platform'] = {'os': 'linux', 'architecture': 'amd64'}
    image_ref = add(json.dumps({'manifests': [manifest_ref]}).encode())
    blobs['index.json'] = json.dumps({'manifests': [image_ref]}).encode()
    with tarfile.open(p, 'w') as t:
        for n, b in blobs.items():
            member = tarfile.TarInfo(n); member.size = len(b); t.addfile(member, io.BytesIO(b))
    assert m.archive_image_ids(p) == {image_ref['digest']}


def test_verify_uses_explicit_delta_lock_and_rejects_wrong_images(tmp_path, monkeypatch):
    root=tmp_path/'bundle';root.mkdir()
    image=make_tar(root/'images.tar')
    manifest={'files':[{'path':'images.tar','sha256':hashlib.sha256((root/'images.tar').read_bytes()).hexdigest()}],'image_ids':[image]}
    (root/'bundle-manifest.json').write_text(json.dumps(manifest))
    lock=tmp_path/'delta.json'
    lock.write_text(json.dumps({'release':'fixture-delta','services':{'proxy':{'image_id':image,'size_bytes':1,'platform':'linux/amd64'}}}))
    monkeypatch.setattr(m.sys,'argv',['images.py','verify','--directory',str(root),'--lock',str(lock)])
    assert m.main()==0
    lock.write_text(json.dumps({'services':{'proxy':{'image_id':'sha256:'+'a'*64}}}))
    assert m.main()==1
