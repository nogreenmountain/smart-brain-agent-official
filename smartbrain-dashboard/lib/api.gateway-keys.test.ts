import { afterEach, describe, expect, it, vi } from 'vitest';
import { createAIGatewayKey, renameAIGatewayKey, revokeAIGatewayKey, deleteRevokedAIGatewayKey, getAIGatewayOperation } from './api';

afterEach(() => vi.unstubAllGlobals());

describe('personal key JSON transport', () => {
  it('sends a stable idempotency contract and preserves pending results on every mutation', async () => {
    const pending = { kind: 'operation', operation_id: 'operation-1', status: 'reconciling' };
    const fetch = vi.fn().mockResolvedValue({ ok: true, status: 202, json: async () => pending });
    vi.stubGlobal('fetch', fetch);
    const idem = 'ce346220-3b9b-4bbe-93d3-04621e3e3f40';
    expect(await createAIGatewayKey('Codex', idem)).toEqual(pending);
    expect(await revokeAIGatewayKey('key-1', idem)).toEqual(pending);
    expect(await deleteRevokedAIGatewayKey('key-1', idem)).toEqual(pending);
    for (const [, init] of fetch.mock.calls) {
      expect(new Headers(init.headers).get('Idempotency-Key')).toBe(idem);
      expect(new Headers(init.headers).get('X-SmartBrain-Gateway-Contract')).toBe('2');
    }
    await getAIGatewayOperation('operation-1');
    expect(fetch.mock.calls[3][0]).toContain('/operations/operation-1');
    expect(fetch.mock.calls[3][1].method).toBeUndefined();
  });
  it.each([
    ['create', () => createAIGatewayKey('Codex'), 'POST'],
    ['rename', () => renameAIGatewayKey('key-1', 'Codex'), 'PATCH'],
  ] as const)('%s declares the JSON body so FastAPI receives an object', async (_, invoke, method) => {
    const fetch = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ id: 'key-1' }) });
    vi.stubGlobal('fetch', fetch);
    await invoke();
    const init = fetch.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe(method);
    expect(new Headers(init.headers).get('Content-Type')).toBe('application/json');
    expect(JSON.parse(init.body as string)).toEqual({ label: 'Codex' });
    expect(init.credentials).toBe('include');
  });
});
