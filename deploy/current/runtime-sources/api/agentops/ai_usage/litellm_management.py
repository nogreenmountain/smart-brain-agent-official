"""Pinned LiteLLM management adapter. No model traffic or mutation retries."""
import hashlib
import json
import ipaddress
from urllib.parse import urlsplit
import httpx


class ManagementUnavailable(RuntimeError):
    pass


class LiteLLMManagement:
    def __init__(self, base_url, master_key, *, models, transport=None):
        url = urlsplit(base_url)
        if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment:
            raise ValueError('Invalid management endpoint')
        if url.scheme == 'http':
            try:
                address = ipaddress.ip_address(url.hostname)
            except ValueError:
                raise ValueError('HTTP management endpoint must be a private IP') from None
            if not (address.is_private or address.is_loopback) or address.is_unspecified or address.is_multicast:
                raise ValueError('HTTP management endpoint must be a private IP')
        if not master_key or any(c in master_key for c in '\r\n') or not models or any(not isinstance(m, str) or not m for m in models):
            raise ValueError('Management credential and model allowlist are required')
        self.models = list(models)
        self.client = httpx.Client(base_url=base_url, headers={'Authorization': 'Bearer ' + master_key},
                                   transport=transport, timeout=10, follow_redirects=False, trust_env=False)

    def create_key(self, *, secret, user_id, operation_id, label):
        result = self._request('POST', '/key/generate', payload={
            'key': secret, 'user_id': user_id, 'models': self.models, 'key_alias': label,
            'metadata': {'smartbrain_operation_id': operation_id}, 'key_type': 'llm_api', 'blocked': False,
        })
        if result.get('key') != secret:
            raise ManagementUnavailable('Key creation result is unconfirmed')
        return hashlib.sha256(secret.encode()).hexdigest()

    def _request(self, method, path, *, payload=None, params=None, allow_missing=False):
        try:
            with self.client.stream(method, path, json=payload, params=params) as response:
                if allow_missing and response.status_code == 404:
                    return None
                if response.status_code != 200:
                    raise ManagementUnavailable('Gateway management result is unconfirmed')
                raw = bytearray()
                for chunk in response.iter_bytes():
                    if len(raw) + len(chunk) > 65536:
                        raise ManagementUnavailable('Gateway management response is invalid')
                    raw.extend(chunk)
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ManagementUnavailable('Gateway management response is invalid')
                return result
        except (httpx.HTTPError, ValueError, RecursionError):
            raise ManagementUnavailable('Gateway management result is unconfirmed') from None

    def lookup_key(self, key_hash, *, user_id, operation_id):
        result = self._request('GET', '/key/info', params={'key': key_hash}, allow_missing=True)
        if result is None:
            return None
        info = result.get('info')
        if (not isinstance(info, dict) or result.get('key') != key_hash
                or info.get('user_id') != user_id or info.get('models') != self.models
                or not isinstance(info.get('metadata'), dict)
                or info['metadata'].get('smartbrain_operation_id') != operation_id
                or info.get('allowed_routes') != ['llm_api_routes'] or info.get('key_type') != 'llm_api'
                or (info.get('blocked') is not None and type(info['blocked']) is not bool)):
            raise ManagementUnavailable('Gateway key identity or policy does not match')
        return {'exists': True, 'blocked': info.get('blocked') is True}

    def block_key(self, key_hash, *, user_id, operation_id):
        identity = {'user_id': user_id, 'operation_id': operation_id}
        before = self.lookup_key(key_hash, **identity)
        if before is None or before['blocked']:
            return True
        self._request('POST', '/key/block', payload={'key': key_hash})
        after = self.lookup_key(key_hash, **identity)
        if after is not None and not after['blocked']:
            raise ManagementUnavailable('Key revocation is unconfirmed')
        return True

    def delete_blocked_key(self, key_hash, *, user_id, operation_id):
        identity = {'user_id': user_id, 'operation_id': operation_id}
        before = self.lookup_key(key_hash, **identity)
        if before is None:
            return True
        if not before['blocked']:
            raise ManagementUnavailable('Active key cannot be removed')
        self._request('POST', '/key/delete', payload={'keys': [key_hash]})
        if self.lookup_key(key_hash, **identity) is not None:
            raise ManagementUnavailable('Key deletion is unconfirmed')
        return True

    def close(self):
        self.client.close()
