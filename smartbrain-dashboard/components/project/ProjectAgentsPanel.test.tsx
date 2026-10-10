import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProjectAgentsPanel } from './ProjectAgentsPanel';

const api = vi.hoisted(() => {
  class MockApiError extends Error {
    constructor(public status: number, public body: unknown, message: string) {
      super(message);
      this.name = 'ApiError';
    }
  }
  return {
    ApiError: MockApiError,
    get: vi.fn(),
    initialize: vi.fn(),
    upload: vi.fn(),
    download: vi.fn(),
    adapter: vi.fn(),
    preview: vi.fn(),
    reset: vi.fn(),
    listVersions: vi.fn(),
    downloadVersion: vi.fn(),
  };
});
vi.mock('@/lib/api', () => ({
  ApiError: api.ApiError,
  getProjectAgents: api.get,
  getApiBaseUrl: () => 'https://brain.example',
  initializeProjectAgents: api.initialize,
  uploadProjectAgents: api.upload,
  downloadProjectAgents: api.download,
  getLocalProjectAdapterStatus: api.adapter,
  previewProjectAgentsTemplate: api.preview,
  resetProjectAgentsToTemplate: api.reset,
  listProjectAgentsVersions: api.listVersions,
  downloadProjectAgentsVersion: api.downloadVersion,
}));

describe('ProjectAgentsPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    api.get.mockResolvedValue({ project_id: 'p1', filename: 'AGENTS.md', content: '# 项目', version: 1, sha256: 'a'.repeat(64), updated_at: null });
    api.initialize.mockResolvedValue({ project_id: 'p1', filename: 'AGENTS.md', content: '# 项目', version: 1, sha256: 'a'.repeat(64), updated_at: null });
    api.adapter.mockResolvedValue({ ok: true, project_id: 'p1', listen_port: 8811 });
    api.preview.mockResolvedValue({
      project_id: 'p1',
      current_version: 1,
      current_sha256: 'a'.repeat(64),
      current_updated_by: null,
      current_updated_at: null,
      template_version: 4,
      template_sha256: 'b'.repeat(64),
      identical: false,
    });
    api.reset.mockResolvedValue({
      status: 'replaced',
      agents: { project_id: 'p1', filename: 'AGENTS.md', content: '# 新模板', version: 5, sha256: 'b'.repeat(64), updated_at: '2026-10-10T00:00:00Z' },
    });
    api.listVersions.mockResolvedValue([
      { version: 4, sha256: 'd'.repeat(64), updated_by: null, created_at: '2026-10-10T01:00:00Z' },
    ]);
    api.downloadVersion.mockResolvedValue(new Blob(['archived']));
  });

  it('shows the project workflow every time the panel is entered', async () => {
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    expect(await screen.findByRole('dialog')).toHaveTextContent('1. 创建项目文件夹');
    expect(screen.getByText('让 AI 理解项目规则，与智慧大脑高效协作')).toBeInTheDocument();
    expect(screen.getByText('测试项目')).toBeInTheDocument();
  });

  it('rejects a file whose name is not exactly AGENTS.md', async () => {
    const user = userEvent.setup();
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    await user.click(await screen.findByRole('button', { name: '开始使用' }));
    const input = screen.getByLabelText('上传 AGENTS.md');
    await user.upload(input, new File(['x'], 'agents.md', { type: 'text/markdown' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('文件名必须严格为 AGENTS.md');
    expect(api.upload).not.toHaveBeenCalled();
  });

  it.each([true, false])('uses company-memory without adapter UI or detection (manager=%s)', async (canManage) => {
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage={canManage} />);
    expect(await screen.findByText(/record_project_conversation/)).toBeInTheDocument();
    expect(screen.queryByText(/本项目桌面适配器|专用端口|Provider 地址|尚未检测/)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /适配器|一键启动器/ })).not.toBeInTheDocument();
    expect(document.querySelector('a[href*="/downloads/"]')).toBeNull();
    expect(api.adapter).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: '下载' })).toBeInTheDocument();
    expect(screen.queryByLabelText('上传 AGENTS.md') !== null).toBe(canManage);
  });

  it('shows reinitialize when a file exists instead of plain initialize', async () => {
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    expect(await screen.findByRole('button', { name: '重新初始化为最新模板' })).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: '初始化' })).not.toBeInTheDocument();
  });

  it('previews and confirms reinitialization with a compare-and-set payload', async () => {
    const user = userEvent.setup();
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    await user.click(await screen.findByRole('button', { name: '重新初始化为最新模板' }));
    const dialog = await screen.findByRole('dialog', { name: '重新初始化为最新模板' });
    expect(dialog).toHaveTextContent('当前文件：版本 v1 · 摘要 aaaaaaaaaaaa');
    expect(dialog).toHaveTextContent('最新模板：模板 v4 · 摘要 bbbbbbbbbbbb');
    expect(dialog).toHaveTextContent('确认后当前 AGENTS.md 将被最新模板覆盖');
    await user.click(screen.getByRole('button', { name: '确认覆盖为最新模板' }));
    expect(api.reset).toHaveBeenCalledWith('p1', {
      expected_version: 1,
      expected_sha256: 'a'.repeat(64),
      template_sha256: 'b'.repeat(64),
    });
    expect(await screen.findByText(/已更新到最新模板（版本 v5）/)).toBeInTheDocument();
    expect(screen.queryByRole('dialog', { name: '重新初始化为最新模板' })).not.toBeInTheDocument();
  });

  it('does not offer overwrite when the file already matches the template', async () => {
    const user = userEvent.setup();
    api.preview.mockResolvedValue({
      project_id: 'p1',
      current_version: 4,
      current_sha256: 'b'.repeat(64),
      current_updated_by: null,
      current_updated_at: null,
      template_version: 4,
      template_sha256: 'b'.repeat(64),
      identical: true,
    });
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    await user.click(await screen.findByRole('button', { name: '重新初始化为最新模板' }));
    const dialog = await screen.findByRole('dialog', { name: '重新初始化为最新模板' });
    expect(dialog).toHaveTextContent('当前内容已与最新模板一致，无需覆盖');
    expect(screen.queryByRole('button', { name: '确认覆盖为最新模板' })).not.toBeInTheDocument();
    expect(api.reset).not.toHaveBeenCalled();
  });

  it('refreshes the preview after a 409 conflict instead of overwriting blindly', async () => {
    const user = userEvent.setup();
    api.reset.mockRejectedValue(new api.ApiError(409, { detail: 'AGENTS.md 已被其他人修改' }, 'AGENTS.md 已被其他人修改'));
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    await user.click(await screen.findByRole('button', { name: '重新初始化为最新模板' }));
    await user.click(await screen.findByRole('button', { name: '确认覆盖为最新模板' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('文件或模板在预览后已变化');
    expect(api.preview).toHaveBeenCalledTimes(2);
    expect(screen.getByRole('dialog', { name: '重新初始化为最新模板' })).toBeInTheDocument();
  });

  it('cancelling the preview never resets the file', async () => {
    const user = userEvent.setup();
    render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
    await user.click(await screen.findByRole('button', { name: '重新初始化为最新模板' }));
    await screen.findByRole('dialog', { name: '重新初始化为最新模板' });
    await user.click(screen.getByRole('button', { name: '取消' }));
    expect(api.reset).not.toHaveBeenCalled();
    expect(screen.queryByRole('dialog', { name: '重新初始化为最新模板' })).not.toBeInTheDocument();
  });

  it('lists archived versions and downloads a selected version', async () => {
    const user = userEvent.setup();
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const createObjectURL = vi.fn().mockReturnValue('blob:mock');
    const revokeObjectURL = vi.fn();
    vi.stubGlobal('URL', { createObjectURL, revokeObjectURL });
    try {
      render(<ProjectAgentsPanel projectId="p1" projectName="测试项目" canManage />);
      await user.click(await screen.findByRole('button', { name: '版本历史' }));
      expect(api.listVersions).toHaveBeenCalledWith('p1');
      expect(await screen.findByText(/v4 · 摘要 dddddddddddd/)).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: '下载此版本' }));
      expect(api.downloadVersion).toHaveBeenCalledWith('p1', 4);
    } finally {
      clickSpy.mockRestore();
      vi.unstubAllGlobals();
    }
  });
});
