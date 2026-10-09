import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { ProjectAgentsPanel } from './ProjectAgentsPanel';

const api = vi.hoisted(() => ({ get: vi.fn(), initialize: vi.fn(), upload: vi.fn(), download: vi.fn(), adapter: vi.fn() }));
vi.mock('@/lib/api', () => ({
  getProjectAgents: api.get,
  getApiBaseUrl: () => 'https://brain.example',
  initializeProjectAgents: api.initialize,
  uploadProjectAgents: api.upload,
  downloadProjectAgents: api.download,
  getLocalProjectAdapterStatus: api.adapter,
}));

describe('ProjectAgentsPanel', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    api.get.mockResolvedValue({ project_id: 'p1', filename: 'AGENTS.md', content: '# 项目', version: 1, sha256: 'a'.repeat(64), updated_at: null });
    api.initialize.mockResolvedValue({ project_id: 'p1', filename: 'AGENTS.md', content: '# 项目', version: 1, sha256: 'a'.repeat(64), updated_at: null });
    api.adapter.mockResolvedValue({ ok: true, project_id: 'p1', listen_port: 8811 });
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
});
