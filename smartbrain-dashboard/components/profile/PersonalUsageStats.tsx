'use client';

import { useEffect, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { getPersonalUsageStats, type PersonalUsageStats as PersonalUsageStatsData } from '@/lib/api';

export function PersonalUsageStats() {
  const [stats, setStats] = useState<PersonalUsageStatsData | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;
    getPersonalUsageStats()
      .then((next) => { if (alive) setStats(next); })
      .catch((nextError) => { if (alive) setError(nextError instanceof Error ? nextError.message : '统计加载失败'); });
    return () => { alive = false; };
  }, []);

  return (
    <section aria-labelledby="personal-usage-stats-heading" className="rounded-lg border border-[#d7e0ec] bg-white p-5 shadow-sm lg:col-span-2">
      <div className="flex items-center gap-2"><BarChart3 size={19} className="text-brand-600" aria-hidden="true" /><h2 id="personal-usage-stats-heading" className="text-lg font-semibold text-[#10213e]">今日 AI 使用统计</h2></div>
      {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
      {!error && stats && <>
        <div className="mt-4 grid gap-3 sm:grid-cols-4"><div className="rounded-lg bg-[#f7f9fc] p-3 text-sm text-[#50627b]">对话 <strong className="ml-1 text-lg text-[#10213e]">{stats.conversation_count}</strong></div><div className="rounded-lg bg-[#f7f9fc] p-3 text-sm text-[#50627b]">Wiki 上传 <strong className="ml-1 text-lg text-[#10213e]">{stats.wiki_upload_count}</strong></div><div className="rounded-lg bg-[#f7f9fc] p-3 text-sm text-[#50627b]">待处理 <strong className="ml-1 text-lg text-[#10213e]">{stats.pending_wiki_count}</strong></div><div className="rounded-lg bg-[#f7f9fc] p-3 text-sm text-[#50627b]">失败 <strong className="ml-1 text-lg text-[#10213e]">{stats.failed_wiki_count}</strong></div></div>
        <div className="mt-4 space-y-2">{stats.projects.length ? stats.projects.map((project) => <div key={project.project_id ?? project.project_name} className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-[#e6ecf3] px-3 py-2 text-sm"><span className="font-medium text-[#253655]">{project.project_name}</span><span className="text-xs text-[#6e7d97]">{project.conversation_count} 条对话 · {project.wiki_upload_count} 条 Wiki</span></div>) : <p className="text-sm text-[#6e7d97]">今天还没有项目对话记录。</p>}</div>
      </>}
      {!error && !stats && <p role="status" className="mt-4 text-sm text-[#6e7d97]">正在加载今日统计…</p>}
    </section>
  );
}
