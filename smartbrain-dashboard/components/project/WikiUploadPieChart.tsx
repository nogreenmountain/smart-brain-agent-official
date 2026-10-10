'use client';

import { useEffect, useMemo, useState } from 'react';
import { getProjectWikiUploadStats, type WikiUploadStats } from '@/lib/api';

const COLORS = ['#4a7bff', '#17a58a', '#f0a23a', '#df5a67', '#8b5cf6', '#0ea5e9'];

export function WikiUploadPieChart({ projectId }: { projectId: string }) {
  const [stats, setStats] = useState<WikiUploadStats | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    setError('');
    getProjectWikiUploadStats(projectId)
      .then((next) => { if (alive) setStats(next); })
      .catch((nextError) => { if (alive) setError(nextError instanceof Error ? nextError.message : '统计加载失败'); });
    return () => { alive = false; };
  }, [projectId]);

  const gradient = useMemo(() => {
    if (!stats?.total) return '#e6ecf3 0 100%';
    let start = 0;
    return stats.members.map((member, index) => {
      const end = start + member.ratio * 100;
      const value = `${COLORS[index % COLORS.length]} ${start}% ${end}%`;
      start = end;
      return value;
    }).join(', ');
  }, [stats]);

  return (
    <section aria-labelledby="conversation-upload-stats-heading" className="rounded-lg border border-[#d7e0ec] bg-white p-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 id="conversation-upload-stats-heading" className="text-sm font-semibold text-[#10213e]">对话上传统计</h3>
          <p className="mt-1 text-xs text-[#6e7d97]">按成员统计已保存的项目对话，重试不重复计数</p>
        </div>
        <span className="text-xs text-[#6e7d97]">合计 {stats?.total ?? '—'}</span>
      </div>
      {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
      {!error && (
        <div className="mt-4 flex flex-wrap items-center gap-5">
          <div aria-label="对话上传比例饼图" className="h-28 w-28 shrink-0 rounded-full" style={{ background: `conic-gradient(${gradient})` }} />
          <ul className="min-w-0 flex-1 space-y-2">
            {stats?.members.length ? stats.members.map((member, index) => (
              <li key={member.user_id} className="flex items-center justify-between gap-3 text-sm text-[#253655]">
                <span className="flex min-w-0 items-center gap-2 truncate"><span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />{member.display_name}</span>
                <span className="shrink-0 text-xs text-[#6e7d97]">{member.count} · {(member.ratio * 100).toFixed(1)}%</span>
              </li>
            )) : <li className="text-sm text-[#6e7d97]">暂无已保存的项目对话</li>}
          </ul>
        </div>
      )}
    </section>
  );
}
