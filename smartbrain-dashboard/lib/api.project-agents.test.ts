import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  createProjectContext,
  getProjectAgents,
  getLocalProjectAdapterStatus,
  getProjectWikiUploadStats,
  initializeProjectAgents,
  uploadProjectAgents,
} from './api';

describe('project AGENTS API helpers', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads the project AGENTS document', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ project_id: 'p1', filename: 'AGENTS.md', content: 'x', version: 1, sha256: 'a'.repeat(64) }), { status: 200, headers: { 'Content-Type': 'application/json' } })));
    await expect(getProjectAgents('p1')).resolves.toMatchObject({ filename: 'AGENTS.md' });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v4/projects/p1/agents'), expect.objectContaining({ credentials: 'include' }));
  });

  it('sends strict filename and raw markdown for updates', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ project_id: 'p1', filename: 'AGENTS.md', content: 'updated', version: 2, sha256: 'b'.repeat(64) }), { status: 200, headers: { 'Content-Type': 'application/json' } })));
    await uploadProjectAgents('p1', new File(['updated'], 'AGENTS.md', { type: 'text/markdown' }));
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v4/projects/p1/agents/upload'), expect.objectContaining({ method: 'POST', headers: expect.objectContaining({ 'X-File-Name': 'AGENTS.md' }) }));
  });

  it('exposes context and member upload statistics helpers', async () => {
    vi.stubGlobal('fetch', vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ token: 'sbc_x', project_id: 'p1', agents_version: 1, agents_sha256: 'a'.repeat(64), expires_at: '2026-09-23T00:00:00Z' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ project_id: 'p1', total: 2, members: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ project_id: 'p1', filename: 'AGENTS.md', content: 'x', version: 1, sha256: 'a'.repeat(64) }), { status: 200 })));
    await expect(createProjectContext('p1', 'key-1')).resolves.toMatchObject({ token: 'sbc_x' });
    await expect(getProjectWikiUploadStats('p1')).resolves.toMatchObject({ total: 2 });
    await expect(initializeProjectAgents('p1')).resolves.toMatchObject({ filename: 'AGENTS.md' });
  });

  it('checks the per-project local adapter without sending browser credentials', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ ok: true, project_id: 'p1', listen_port: 8811 }), { status: 200 })));
    await expect(getLocalProjectAdapterStatus(8811)).resolves.toMatchObject({ project_id: 'p1' });
    expect(fetch).toHaveBeenCalledWith('http://127.0.0.1:8811/control/status', expect.objectContaining({ mode: 'cors' }));
  });
});
