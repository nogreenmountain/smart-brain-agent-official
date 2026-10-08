import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { PersonalUsageStats } from './PersonalUsageStats';

const getStats = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api', () => ({ getPersonalUsageStats: getStats }));

describe('PersonalUsageStats', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getStats.mockResolvedValue({ usage_date: '2026-09-23', conversation_count: 4, wiki_upload_count: 3, pending_wiki_count: 1, failed_wiki_count: 0, projects: [{ project_id: 'p1', project_name: '测试项目', conversation_count: 4, wiki_upload_count: 3 }] });
  });

  it('shows today conversation and wiki counts by project', async () => {
    render(<PersonalUsageStats />);
    expect(await screen.findByText('今日 AI 使用统计')).toBeInTheDocument();
    expect(screen.getAllByText(/对话/)[0]).toHaveTextContent('4');
    expect(screen.getByText(/Wiki 上传/)).toHaveTextContent('3');
    expect(screen.getByText(/测试项目/).parentElement).toHaveTextContent('4 条对话 · 3 条 Wiki');
  });
});
