'use client';

import { FormEvent, useEffect, useRef, useState } from 'react';
import { Copy, KeyRound, Plus } from 'lucide-react';
import { Button } from '@/components/Button';
import { Input } from '@/components/Input';
import { createAIGatewayKey, deleteRevokedAIGatewayKey, getAIGatewayOperation, listAIGatewayOperations, listAIGatewayKeys, renameAIGatewayKey, revokeAIGatewayKey, type AIGatewayKey, type AIGatewayOperation } from '@/lib/api';

const safeKey = (key: AIGatewayKey): AIGatewayKey => ({ ...key, key: null });
const message = (error: unknown) => error instanceof Error ? error.message : '操作失败，请重试';
export function PersonalApiKeys() {
  const [keys, setKeys] = useState<AIGatewayKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [secret, setSecret] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [editedName, setEditedName] = useState('');
  const [deleting, setDeleting] = useState<string | null>(null);
  const [notice, setNotice] = useState('');
  const [permanentDelete, setPermanentDelete] = useState<string | null>(null);
  const editInput = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState<AIGatewayOperation | null>(null);
  const [operationsLoaded, setOperationsLoaded] = useState(false);
  const attempts = useRef(new Map<string, string>());
  const checking = useRef(false);
  function attempt(action: string) {
    if (!attempts.current.has(action)) attempts.current.set(action, crypto.randomUUID());
    return attempts.current.get(action)!;
  }

  async function refreshPending(operation: AIGatewayOperation) {
    if (checking.current) return;
    checking.current = true;
    try {
      const result = await getAIGatewayOperation(operation.operation_id);
      if (result.status === 'confirmed' || result.status === 'failed_confirmed') {
        await reload();
        const remaining = await listAIGatewayOperations();
        setPending(remaining[0] ?? null);
        setNotice(result.status === 'failed_confirmed' ? '操作已确认失败，请检查列表后再操作。' :
          (result.error_code ?? operation.error_code) === 'secret_not_delivered' ? '完整密钥未能交付，请停用这把密钥后重新创建。' : '操作已确认，请检查最新列表。');
      }
    } catch (error) { setError(message(error)); }
    finally { checking.current = false; }
  }

  useEffect(() => {
    if (!pending) return;
    let reads = 0;
    const timer = window.setInterval(() => {
      if (++reads > 24) { window.clearInterval(timer); return; }
      void refreshPending(pending);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [pending]);

  useEffect(() => { if (editing) editInput.current?.focus(); }, [editing]);

  useEffect(() => {
    let alive = true;
    listAIGatewayKeys().then((rows) => {
      if (alive) { setKeys(rows.map(safeKey)); setLoaded(true); }
    }).catch((error) => { if (alive) setError(message(error)); })
      .finally(() => { if (alive) setLoading(false); });
    listAIGatewayOperations().then((operations) => {
      if (alive) { setPending(operations[0] ?? null); setOperationsLoaded(true); }
    }).catch((error) => { if (alive) setError('待处理状态加载失败：' + message(error)); });
    return () => { alive = false; };
  }, []);

  async function reload() {
    setLoading(true); setError('');
    try { const rows = await listAIGatewayKeys(); setKeys(rows.map(safeKey)); setLoaded(true); }
    catch (error) { setError(message(error)); }
    finally { setLoading(false); }
  }

  async function reloadOperations() {
    setBusy(true); setError('');
    try {
      const operations = await listAIGatewayOperations();
      setPending(operations[0] ?? null); setOperationsLoaded(true);
    } catch (error) { setError('待处理状态加载失败：' + message(error)); }
    finally { setBusy(false); }
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (busy || secret || pending || !name.trim()) return;
    setBusy(true); setError(''); setCopied(false);
    try {
      const action = 'create:' + name.trim();
      const created = await createAIGatewayKey(name.trim(), attempt(action));
      attempts.current.delete(action);
      if (!('id' in created)) {
        setPending(created); setName(''); return;
      }
      setKeys((rows) => [safeKey(created), ...rows.filter((row) => row.id !== created.id)]);
      setName('');
      if (created.key) setSecret(created.key);
      else setError('服务端未返回完整密钥，请刷新列表检查状态。不要重复提交创建请求。');
    } catch (error) { setError(message(error)); }
    finally { setBusy(false); }
  }

  async function copy() {
    if (!secret) return;
    try { await navigator.clipboard.writeText(secret); setCopied(true); }
    catch { setError('无法访问剪贴板，请选中完整密钥手动复制。'); }
  }

  async function rename(event: FormEvent, id: string) {
    event.preventDefault();
    if (busy || !editedName.trim()) return;
    setBusy(true); setError(''); setNotice('');
    try {
      const next = await renameAIGatewayKey(id, editedName.trim());
      setKeys((rows) => rows.map((row) => row.id === id ? safeKey(next) : row));
      setEditing(null); setNotice('密钥名称已更新');
    } catch (error) { setError(message(error)); }
    finally { setBusy(false); }
  }

  async function revoke(id: string) {
    if (busy) return;
    setBusy(true); setError(''); setNotice('');
    try {
      const action = 'revoke:' + id;
      const next = await revokeAIGatewayKey(id, attempt(action));
      attempts.current.delete(action);
      if (!('id' in next)) {
        setPending(next); setDeleting(null); return;
      }
      setKeys((rows) => rows.map((row) => row.id === id ? safeKey(next) : row));
      setDeleting(null); setNotice('密钥已删除，历史记录仍保留');
    } catch (error) { setError(message(error)); }
    finally { setBusy(false); }
  }

  const activeCount = keys.filter((key) => key.is_active).length;
  const maxActiveKeys = 1;
  return <section id="api-keys" aria-labelledby="api-keys-heading" className="min-w-0 rounded-lg border border-[#d7e0ec] bg-white p-5 shadow-sm lg:col-span-2">
    <div className="flex flex-wrap items-center gap-2">
      <KeyRound size={20} aria-hidden="true" className="text-brand-600" />
      <h2 id="api-keys-heading" className="text-lg font-semibold text-[#10213e]">个人 API Key</h2>
      <span className="text-xs text-[#6e7d97]">活动密钥 {loaded ? activeCount : '未知'} / 1</span>
    </div>
    <p className="mt-2 text-sm leading-6 text-[#6e7d97]">每个账号只能有一把活动 API Key。停用后可保留历史记录，但不会自动发放第二把。</p>
    <p className="mt-2 text-sm leading-6 text-[#6e7d97]">公司网关会记录请求内容和 Token 用量并归属到你的账号。新网关的工作记录、Wiki 和日报接入以实际启用范围为准。</p>
    <p className="mt-2 text-xs text-[#6e7d97]">密钥仅用于已启用个人鉴权的公司网关，请求地址以管理员发布的接入配置为准。</p>
    {error && <div role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
    {notice && <p role="status" className="mt-3 text-sm text-emerald-800">{notice}</p>}
    {pending && <div role="status" className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-900"><p>操作正在核对，请勿重复创建或移除密钥。待确认的创建仍占用名额。</p><Button variant="secondary" onClick={() => refreshPending(pending)}>查询处理结果</Button></div>}
    {!loaded && !loading && <Button variant="secondary" className="mt-3" onClick={reload}>重新加载密钥</Button>}
    {!operationsLoaded && !loading && <Button variant="secondary" className="mt-3" disabled={busy} onClick={reloadOperations}>重新加载处理状态</Button>}
    {secret && <div className="mt-4 space-y-3 rounded-lg border border-amber-300 bg-amber-50 p-4">
      <p className="text-sm font-semibold text-amber-900">请现在保存：关闭后无法再次查看完整密钥</p>
      <Input aria-label="新密钥完整值" value={secret} readOnly autoComplete="off" spellCheck={false} onFocus={(event) => event.target.select()} />
      <div className="flex flex-wrap gap-2">
        <Button variant="secondary" onClick={copy}><Copy size={15} aria-hidden="true" />{copied ? '已复制' : '复制完整密钥'}</Button>
        <Button onClick={() => { setSecret(null); setCopied(false); }}>我已保存，关闭</Button>
      </div>
    </div>}
    <form onSubmit={create} className="mt-5 flex flex-wrap items-end gap-3">
      <label className="min-w-0 flex-1 basis-52">
        <span className="mb-1.5 block text-xs font-semibold text-[#6e7d97]">密钥名称</span>
        <Input value={name} onChange={(event) => setName(event.target.value)} maxLength={100} placeholder="例如：Codex 工作电脑" autoComplete="off" disabled={busy || Boolean(secret)} />
      </label>
      <Button type="submit" disabled={!loaded || !operationsLoaded || loading || busy || Boolean(pending || secret || editing || deleting) || !name.trim() || activeCount >= maxActiveKeys}><Plus size={16} aria-hidden="true" />{busy ? '处理中…' : '创建 API Key'}</Button>
    </form>
    {activeCount >= maxActiveKeys && <p className="mt-2 text-sm text-[#6e7d97]">活动 Key 名额已用完；请先删除当前 Key 后再创建。</p>}
    {loading ? <p role="status" className="mt-5 text-sm text-[#6e7d97]">正在加载密钥…</p> : loaded && keys.length === 0 ? <p className="mt-5 rounded-lg bg-[#f7f9fc] p-5 text-sm text-[#6e7d97]">还没有 API Key</p> : null}
    <ul aria-label="我的 API Key" className="mt-5 divide-y divide-[#e6ecf3]">
      {keys.map((key) => <li key={key.id} className="min-w-0 py-4">
        <div className="flex flex-wrap items-center gap-2"><span className="break-words font-medium text-[#10213e]">{key.label}</span><span className="text-xs text-[#6e7d97]">{key.status && ['revoking','removing','needs_attention'].includes(key.status) ? '待核对' : key.is_active ? '可用' : '已删除'}</span></div>
        {key.backend === 'litellm' && <div className="mt-2 text-xs text-[#50627b]"><p>Codex 新网关</p><code className="break-all">{key.base_url}</code><p>模型：{key.models?.join('、')}</p></div>}
        <code className="mt-1 block break-all text-sm text-[#50627b]">{key.masked_key}</code>
        <p className="mt-2 text-xs leading-5 text-[#6e7d97]">创建：{new Date(key.created_at).toLocaleString('zh-CN')} · 最近使用：{key.last_used_at ? new Date(key.last_used_at).toLocaleString('zh-CN') : '尚未使用'}</p>
        {key.is_active && editing !== key.id && deleting !== key.id && <div className="mt-3 flex flex-wrap gap-2">
          {key.backend !== 'litellm' && <Button size="sm" variant="secondary" aria-label={`重命名 ${key.label}`} disabled={busy || Boolean(secret || editing || deleting)} onClick={() => { setEditing(key.id); setEditedName(key.label); setError(''); setNotice(''); }}>重命名</Button>}
          <Button size="sm" variant="secondary" className="text-red-700" aria-label={`删除 ${key.label}`} disabled={busy || Boolean(secret || editing || deleting)} onClick={() => { setDeleting(key.id); setError(''); setNotice(''); }}>删除</Button>
        </div>}
        {editing === key.id && <form onSubmit={(event) => rename(event, key.id)} className="mt-3 flex flex-wrap items-end gap-2">
          <label className="min-w-0 flex-1 basis-52"><span className="mb-1 block text-xs">新的密钥名称</span><Input ref={editInput} value={editedName} maxLength={100} disabled={busy} onChange={(event) => setEditedName(event.target.value)} /></label>
          <Button type="submit" disabled={busy || !editedName.trim()}>保存名称</Button>
          <Button type="button" variant="secondary" disabled={busy} onClick={() => setEditing(null)}>取消重命名</Button>
        </form>}
        {deleting === key.id && <div role="group" aria-label="确认删除密钥" className="mt-3 space-y-3 rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="break-words text-sm text-red-800">确定删除“{key.label}”？使用它的工具将无法发起新的 AI 请求，历史用量和对话不会被删除。</p>
          <div className="flex flex-wrap gap-2"><Button variant="danger" disabled={busy} onClick={() => revoke(key.id)}>确认删除</Button><Button variant="secondary" disabled={busy} onClick={() => setDeleting(null)}>取消删除</Button></div>
        </div>}
        {!key.is_active && permanentDelete !== key.id && <Button size="sm" variant="secondary" className="mt-3 text-red-700" aria-label={`永久删除 ${key.label}`} disabled={busy} onClick={() => { setPermanentDelete(key.id); setError(''); }}>永久删除记录</Button>}
        {!key.is_active && permanentDelete === key.id && <div role="group" aria-label="确认永久删除记录" className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3"><p className="text-sm text-red-800">永久删除此记录？历史用量和对话不会被删除。</p><div className="mt-2 flex gap-2"><Button variant="danger" disabled={busy || Boolean(pending)} onClick={async () => { setBusy(true); setError(''); try { const action='remove:'+key.id; const result=await deleteRevokedAIGatewayKey(key.id,attempt(action)); attempts.current.delete(action); if(result) {setPending(result);setPermanentDelete(null);return;} setKeys((current) => current.filter((item) => item.id !== key.id)); setNotice('已删除 Token 记录'); setPermanentDelete(null); } catch (error) { setError(message(error)); } finally { setBusy(false); } }}>确认永久删除记录</Button><Button variant="secondary" disabled={busy} onClick={() => setPermanentDelete(null)}>取消</Button></div></div>}
      </li>)}
    </ul>
  </section>;
}
