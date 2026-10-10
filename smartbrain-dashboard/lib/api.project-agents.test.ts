import { beforeEach, describe, expect, it, vi } from 'vitest';

import {
  createProjectContext,
  downloadProjectAgentsVersion,
  getProjectAgents,
  getProjectWikiUploadStats,
  initializeProjectAgents,
  listProjectAgentsVersions,
  previewProjectAgentsTemplate,
  resetProjectAgentsToTemplate,
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
    expect(fetch).toHaveBeenLastCalledWith(expect.stringContaining('/v4/projects/p1/conversation-upload-stats'), expect.objectContaining({ cache: 'no-store' }));
    await expect(initializeProjectAgents('p1')).resolves.toMatchObject({ filename: 'AGENTS.md' });
  });

  it('previews the latest template without caching', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      project_id: 'p1',
      current_version: 1,
      current_sha256: 'a'.repeat(64),
      current_updated_by: null,
      current_updated_at: null,
      template_version: 4,
      template_sha256: 'b'.repeat(64),
      identical: false,
    }), { status: 200 })));
    await expect(previewProjectAgentsTemplate('p1')).resolves.toMatchObject({ template_version: 4, identical: false });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v4/projects/p1/agents/template-preview'), expect.objectContaining({ cache: 'no-store' }));
  });

  it('posts the expected version and digests when resetting to the template', async () => {
    const payload = { expected_version: 1, expected_sha256: 'a'.repeat(64), template_sha256: 'b'.repeat(64) };
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      status: 'replaced',
      agents: { project_id: 'p1', filename: 'AGENTS.md', content: '# new', version: 5, sha256: 'c'.repeat(64), updated_at: null },
    }), { status: 200 })));
    await expect(resetProjectAgentsToTemplate('p1', payload)).resolves.toMatchObject({ status: 'replaced' });
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v4/projects/p1/agents/reset-to-template'),
      expect.objectContaining({ method: 'POST', body: JSON.stringify(payload) }),
    );
  });

  it('lists archived versions and unwraps the versions array', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({
      project_id: 'p1',
      versions: [{ version: 4, sha256: 'd'.repeat(64), updated_by: null, created_at: '2026-10-10T01:00:00Z' }],
    }), { status: 200 })));
    await expect(listProjectAgentsVersions('p1')).resolves.toEqual([expect.objectContaining({ version: 4 })]);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v4/projects/p1/agents/versions'), expect.objectContaining({ cache: 'no-store' }));
  });

  it('downloads an archived version as a blob', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('archived', { status: 200 })));
    await expect(downloadProjectAgentsVersion('p1', 4)).resolves.toBeInstanceOf(Blob);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v4/projects/p1/agents/versions/4/download'), expect.objectContaining({ credentials: 'include' }));
  });

});
