import { render, screen, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { WikiUploadPieChart } from './WikiUploadPieChart';

const getStats = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api', () => ({ getProjectWikiUploadStats: getStats }));

describe('WikiUploadPieChart', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getStats.mockResolvedValue({ project_id: 'p1', total: 3, members: [
      { user_id: 'u1', display_name: '张三', count: 2, ratio: 2 / 3 },
      { user_id: 'u2', display_name: '李四', count: 1, ratio: 1 / 3 },
    ] });
  });

  it('shows member ratios from successful wiki uploads', async () => {
    render(<WikiUploadPieChart projectId="p1" />);
    expect(await screen.findByText('Wiki 上传统计')).toBeInTheDocument();
    const rows = screen.getAllByRole('listitem');
    expect(within(rows[0]).getByText('张三')).toBeInTheDocument();
    expect(rows[0]).toHaveTextContent('2 · 66.7%');
    expect(rows[1]).toHaveTextContent('李四');
    expect(rows[1]).toHaveTextContent('1 · 33.3%');
  });
});
