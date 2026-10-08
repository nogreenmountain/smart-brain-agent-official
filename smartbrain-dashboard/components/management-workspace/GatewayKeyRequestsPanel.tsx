'use client';

import { useEffect, useState } from 'react';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { listKeyRequestReview, reviewKeyRequest, type AIGatewayKeyRequest } from '@/lib/api';

export function GatewayKeyRequestsPanel() {
  const [requests, setRequests] = useState<AIGatewayKeyRequest[]>([]);
  const [comment, setComment] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState<string | null>(null);

  async function reload() {
    try { setRequests(await listKeyRequestReview()); }
    catch (nextError) { setError(nextError instanceof Error ? nextError.message : '申请加载失败'); }
  }

  useEffect(() => { void reload(); }, []);

  async function review(id: string, decision: 'approve' | 'reject') {
    setBusy(id); setError('');
    try { await reviewKeyRequest(id, decision, comment[id] || ''); setRequests((rows) => rows.filter((row) => row.id !== id)); }
    catch (nextError) { setError(nextError instanceof Error ? nextError.message : '审批失败'); }
    finally { setBusy(null); }
  }

  return <section aria-labelledby="gateway-key-requests-heading" className="rounded-lg border border-[#d7e0ec] bg-white p-5 shadow-sm">
    <h2 id="gateway-key-requests-heading" className="text-lg font-semibold text-[#10213e]">API Key 增量申请</h2>
    <p className="mt-1 text-sm text-[#6e7d97]">仅 hanshangbo 账号可以审批；审批数量表示账号允许的活动 Key 总数。</p>
    {error && <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>}
    {!requests.length && !error && <p className="mt-4 text-sm text-[#6e7d97]">暂无待审批申请。</p>}
    <div className="mt-4 space-y-3">{requests.map((item) => <div key={item.id} className="rounded-lg border border-[#e6ecf3] p-3"><div className="flex flex-wrap justify-between gap-2"><span className="font-medium text-[#10213e]">目标活动 Key：{item.requested_total} 把</span><span className="text-xs text-[#6e7d97]">{new Date(item.created_at).toLocaleString('zh-CN')}</span></div><p className="mt-2 text-sm leading-6 text-[#50627b]">{item.reason}</p><Input className="mt-2" aria-label={`申请 ${item.id} 审批备注`} placeholder="审批备注（可选）" value={comment[item.id] || ''} onChange={(event) => setComment((current) => ({ ...current, [item.id]: event.target.value }))} /><div className="mt-3 flex gap-2"><Button size="sm" disabled={busy === item.id} onClick={() => review(item.id, 'approve')}>同意</Button><Button size="sm" variant="secondary" disabled={busy === item.id} onClick={() => review(item.id, 'reject')}>拒绝</Button></div></div>)}</div>
  </section>;
}
