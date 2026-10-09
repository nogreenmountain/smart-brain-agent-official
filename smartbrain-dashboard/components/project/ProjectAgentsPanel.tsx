'use client';

import { ChangeEvent, useEffect, useState } from 'react';
import { Download, FileCode2, RefreshCw, Upload } from 'lucide-react';
import { Button } from '@/components/Button';
import {
  downloadProjectAgents,
  getProjectAgents,
  initializeProjectAgents,
  uploadProjectAgents,
  type ProjectAgentsFile,
} from '@/lib/api';

const DOWNLOAD_NOTICE = '请下载到对应项目文件夹，若没有项目文件夹，请新建并添加。';

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : '操作失败，请重试';
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

  return (
    <section aria-labelledby="project-agents-heading" className="rounded-lg border border-[#d7e0ec] bg-white p-5 shadow-sm">
      {guideOpen && (
        <div role="dialog" aria-modal="true" aria-labelledby="project-agents-guide-heading" className="mb-5 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h3 id="project-agents-guide-heading" className="font-semibold text-blue-950">开始一个项目的具体流程</h3>
          <ol className="mt-2 space-y-1 text-sm leading-6 text-blue-900">
            <li>1. 创建项目文件夹。</li>
            <li>2. 打开智慧大脑，项目负责人编辑修改 AGENTS.md，界定项目规则和项目细节等需要项目成员共同规范的 AI 使用过程。</li>
            <li>3. 下载 AGENTS.md 到项目文件夹，在 Codex 中打开该文件夹并读取项目规则。</li>
            <li>4. 连接 company-memory 插件，确认当前账号具备该项目的写入权限。</li>
            <li>5. 完成任务后，让 AI 按 AGENTS.md 调用 record_project_conversation 仅提交简短的用户请求和最终结果摘要，不含思考过程、进度或工具日志；核对回执中的项目、上传成员和保存状态。</li>
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
          </div>
          <div className="mt-4 rounded-lg border border-[#d7e0ec] bg-[#f7f9fc] p-3 text-xs leading-5 text-[#50627b]">
            <p className="font-semibold text-[#10213e]">项目记录方式：AGENTS.md + company-memory</p>
            <p className="mt-1">上传身份和时间由服务端确定；只提交授权选定的内容，不保证自动记录每次模型请求。成功保存后仍需核对 Wiki 是否已发布。</p>
            <p className="mt-1">已有 AGENTS.md 不会自动覆盖。负责人请确认文件包含项目 UUID 和插件提交规则，更新后再分发给成员。</p>
          </div>
        </>
      )}
    </section>
  );
}
