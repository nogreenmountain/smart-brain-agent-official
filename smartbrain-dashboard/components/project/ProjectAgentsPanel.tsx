'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import { CheckCircle2, Download, FileCode2, RefreshCw, Upload, WifiOff, Zap } from 'lucide-react';
import { Button } from '@/components/Button';
import {
  downloadProjectAgents,
  getApiBaseUrl,
  getProjectAgents,
  getLocalProjectAdapterStatus,
  initializeProjectAgents,
  uploadProjectAgents,
  type ProjectAgentsFile,
  type LocalProjectAdapterStatus,
} from '@/lib/api';
import { buildProjectAdapterLauncher } from '@/lib/projectAdapterLauncher';

const DOWNLOAD_NOTICE = '请下载到对应项目文件夹，若没有项目文件夹，请新建并添加。';

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请重试';
}

function saveTextFile(filename: string, content: string): void {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function adapterPort(projectId: string): number {
  // Stable per project, so multiple project adapters can run concurrently.
  let hash = 0;
  for (const char of projectId) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return 30000 + (hash % 20000);
}

export function ProjectAgentsPanel({
  projectId,
  projectName,
  canManage,
}: {
  projectId: string;
  projectName: string;
  canManage: boolean;
}) {
  const [agents, setAgents] = useState<ProjectAgentsFile | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [guideOpen, setGuideOpen] = useState(true);
  const [adapterStatus, setAdapterStatus] = useState<LocalProjectAdapterStatus | null>(null);
  const [adapterChecked, setAdapterChecked] = useState(false);
  const localPort = adapterPort(projectId);

  async function reload() {
    setLoading(true);
    setError('');
    try {
      setAgents(await getProjectAgents(projectId));
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setGuideOpen(true);
    setAdapterStatus(null);
    setAdapterChecked(false);
    void reload();
    // A project page mount is the boundary at which the workflow is shown.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleUpload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = '';
    if (!file) return;
    if (file.name !== 'AGENTS.md') {
      setError('文件名必须严格为 AGENTS.md');
      return;
    }
    setBusy(true);
    setError('');
    setNotice('');
    try {
      setAgents(await uploadProjectAgents(projectId, file));
      setNotice('AGENTS.md 已更新');
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setBusy(false);
    }
  }

  async function handleInitialize() {
    setBusy(true);
    setError('');
    try {
      setAgents(await initializeProjectAgents(projectId));
      setNotice('AGENTS.md 已初始化');
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setBusy(false);
    }
  }

  async function handleDownload() {
    setBusy(true);
    setError('');
    setNotice(DOWNLOAD_NOTICE);
    try {
      const blob = await downloadProjectAgents(projectId);
      const picker = (window as Window & {
        showDirectoryPicker?: () => Promise<{
          getFileHandle: (name: string, options: { create: boolean }) => Promise<{
            createWritable: () => Promise<{ write: (value: Blob) => Promise<void>; close: () => Promise<void> }>;
          }>;
        }>;
      }).showDirectoryPicker;
      if (picker) {
        const directory = await picker();
        const fileHandle = await directory.getFileHandle('AGENTS.md', { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(blob);
        await writable.close();
        setNotice('AGENTS.md 已下载到所选项目文件夹');
        return;
      }
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'AGENTS.md';
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (nextError) {
      setError(errorMessage(nextError));
    } finally {
      setBusy(false);
    }
  }

  async function checkAdapter() {
    setBusy(true);
    setError('');
    setAdapterChecked(true);
    try {
      const status = await getLocalProjectAdapterStatus(localPort);
      if (status.project_id !== projectId) {
        setAdapterStatus(null);
        setError(`本机 ${localPort} 端口当前绑定的是其他项目，请启动本项目专用适配器`);
        return;
      }
      setAdapterStatus(status);
      setNotice('本项目适配器已连接；令牌会在后台自动获取、续期并随请求携带');
    } catch (nextError) {
      setAdapterStatus(null);
      setError('本机适配器未连接。请先按下方命令启动本项目专用适配器');
    } finally {
      setBusy(false);
    }
  }

  function downloadOneClickLauncher() {
    const adapterDownloadUrl = typeof window === 'undefined'
      ? `${getApiBaseUrl()}/downloads/smartbrain_codex_adapter.py`
      : `${window.location.origin}/downloads/smartbrain_codex_adapter.py`;
    const files = buildProjectAdapterLauncher({ apiBaseUrl: getApiBaseUrl(), adapterDownloadUrl, projectId, port: localPort });
    saveTextFile('Start-SmartBrain-Codex-Project.cmd', files.cmd);
    setNotice('已下载一键启动器，双击即可；如果文件不在项目目录，启动器会自动弹出项目文件夹选择');
  }

  return (
    <section aria-labelledby="project-agents-heading" className="rounded-lg border border-[#d7e0ec] bg-white p-5 shadow-sm">
      {guideOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="project-agents-guide-heading" className="mb-5 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h3 id="project-agents-guide-heading" className="font-semibold text-blue-950">开始一个项目的具体流程</h3>
          <ol className="mt-2 space-y-1 text-sm leading-6 text-blue-900">
            <li>1. 创建项目文件夹。</li>
            <li>2. 打开智慧大脑，项目负责人编辑修改 AGENTS.md，界定项目规则和项目细节等需要项目成员共同规范的 AI 使用过程。</li>
            <li>3. 安装并启动本项目专用的 SmartBrain 桌面适配器；它会读取 AGENTS.md，并自动获取、续期项目令牌。</li>
            <li>4. 进入 CODEX 或 CLAUDE 创建项目，并选中刚创建的项目文件夹，让 AGENTS.md 被项目读到并完成初始化。</li>
            <li>5. 在请求中不需要写提示词或手工添加请求头；适配器会自动携带本项目令牌。同一台电脑可以为多个项目分别启动适配器。</li>
          </ol>
          <Button className="mt-3" size="sm" onClick={() => setGuideOpen(false)}>开始使用</Button>
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <FileCode2 size={20} aria-hidden="true" className="text-brand-600" />
        <h2 id="project-agents-heading" className="text-lg font-semibold text-[#10213e]">项目AGENTS.md</h2>
        <span className="text-xs text-[#6e7d97]">{projectName}</span>
      </div>
      <p className="mt-2 text-sm leading-6 text-[#6e7d97]">让 AI 理解项目规则，与智慧大脑高效协作</p>
      {error && <div role="alert" className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {notice && <p role="status" className="mt-3 text-sm text-emerald-800">{notice}</p>}
      {loading ? <p role="status" className="mt-4 text-sm text-[#6e7d97]">正在加载 AGENTS.md…</p> : (
        <>
          <div className="mt-4 rounded-lg bg-[#f7f9fc] p-3 text-xs text-[#50627b]">
            <p>版本：{agents?.version ?? '未初始化'} · 摘要：{agents?.sha256?.slice(0, 12) ?? '—'}</p>
            <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap text-[11px] leading-5">{agents?.content ?? '尚未初始化，请先初始化。'}</pre>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {canManage && <Button size="sm" onClick={handleInitialize} disabled={busy}><RefreshCw size={15} aria-hidden="true" />初始化</Button>}
            {canManage && <label className="inline-flex h-8 cursor-pointer items-center gap-1.5 rounded-lg border border-[#d7e0ec] bg-white px-3 text-sm font-medium text-[#10213e] hover:bg-[#f7f9fc]">
              <Upload size={15} aria-hidden="true" />上传更新
              <input aria-label="上传 AGENTS.md" type="file" accept=".md,text/markdown" className="sr-only" onChange={handleUpload} disabled={busy} />
            </label>}
            <Button size="sm" variant="secondary" onClick={handleDownload} disabled={busy}><Download size={15} aria-hidden="true" />下载</Button>
            <Button size="sm" variant="secondary" onClick={checkAdapter} disabled={busy}>
              {adapterStatus ? <CheckCircle2 size={15} aria-hidden="true" /> : <WifiOff size={15} aria-hidden="true" />}
              {adapterStatus ? '适配器已连接' : '检测本机适配器'}
            </Button>
            <Button size="sm" variant="secondary" onClick={downloadOneClickLauncher} disabled={busy}><Zap size={15} aria-hidden="true" />下载一键启动器</Button>
          </div>
          <div className="mt-4 rounded-lg border border-[#d7e0ec] bg-[#f7f9fc] p-3 text-xs leading-5 text-[#50627b]">
            <p className="font-semibold text-[#10213e]">本项目桌面适配器</p>
            <p className="mt-1">专用端口：{localPort} · {adapterChecked ? (adapterStatus ? '已连接' : '未连接') : '尚未检测'}</p>
            <p className="mt-1">在包含两个适配器脚本的目录执行（启动脚本会提示输入 API Key）：</p>
            <p className="mt-1"><a className="text-brand-700 underline" href="/downloads/smartbrain_codex_adapter.py" download>下载 Python 适配器</a> · <a className="text-brand-700 underline" href="/downloads/Start-SmartBrainCodexAdapter.ps1" download>下载 PowerShell 启动脚本</a></p>
            <code className="mt-1 block break-all rounded bg-white p-2 text-[11px]">powershell -ExecutionPolicy Bypass -File .\Start-SmartBrainCodexAdapter.ps1 -ApiBaseUrl &quot;{getApiBaseUrl()}&quot; -ProjectDir . -ListenPort {localPort}</code>
            <p className="mt-2">然后把 Codex 的项目 Provider 地址设置为 <code>http://127.0.0.1:{localPort}/v1</code>。适配器只在内存和本机缓存中保存短期令牌，不要求把令牌写进提示词。</p>
            <p className="mt-1">PowerShell 启动脚本未传入 <code>-ApiKey</code> 时会现场提示输入，密钥不会写入项目文件。</p>
          </div>
        </>
      )}
    </section>
  );
}
