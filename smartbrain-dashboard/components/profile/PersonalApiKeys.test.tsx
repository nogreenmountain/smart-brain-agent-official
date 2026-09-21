import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { PersonalApiKeys } from './PersonalApiKeys';

const api = vi.hoisted(() => ({ list: vi.fn(), create: vi.fn(), rename: vi.fn(), revoke: vi.fn(), status: vi.fn(), remove: vi.fn(), submit: vi.fn(), operation: vi.fn(), pending: vi.fn() }));
vi.mock('@/lib/api', () => ({ listAIGatewayKeys: api.list, createAIGatewayKey: api.create,
  renameAIGatewayKey: api.rename, revokeAIGatewayKey: api.revoke, getMyKeyRequests: api.status,
  deleteRevokedAIGatewayKey: api.remove, submitKeyRequest: api.submit, getAIGatewayOperation: api.operation, listAIGatewayOperations: api.pending }));

const key = { id: 'key-1', label: 'Codex', masked_key: 'sbk_fixture…', is_active: true,
  created_at: '2026-09-07T04:00:00Z', last_used_at: null };

describe('PersonalApiKeys', () => {
  it('keeps pending creation separate from keys and only reads its result', async () => {
    const user=userEvent.setup();
    api.create.mockResolvedValue({kind:'operation',operation_id:'op-1',credential_id:'key-1',status:'reconciling'});
    api.operation.mockResolvedValue({operation_id:'op-1',credential_id:'key-1',status:'confirmed',error_code:'secret_not_delivered'});
    render(<PersonalApiKeys />);
    await screen.findByText('还没有 API Key');
    await user.type(screen.getByLabelText('密钥名称'),'Pending');
    await user.click(screen.getByRole('button',{name:'创建 API Key'}));
    expect(await screen.findByText(/操作正在核对/)).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'创建 API Key'})).toBeDisabled();
    expect(screen.queryByLabelText('新密钥完整值')).not.toBeInTheDocument();
    api.list.mockResolvedValue([{...key,backend:'litellm',base_url:'https://model.invalid/v1',models:['gpt-6-astra'],status:'active'}]);
    await user.click(screen.getByRole('button',{name:'查询处理结果'}));
    expect(await screen.findByText(/完整密钥未能交付/)).toBeInTheDocument();
    expect(await screen.findByText('https://model.invalid/v1')).toBeInTheDocument();
    expect(screen.queryByRole('button',{name:'重命名 Codex'})).not.toBeInTheDocument();
    expect(api.create).toHaveBeenCalledTimes(1);
  });

  it('retains the same create id after transport failure', async () => {
    const user=userEvent.setup();api.create.mockRejectedValueOnce(new Error('网络中断'));
    render(<PersonalApiKeys />);await screen.findByText('还没有 API Key');
    await user.type(screen.getByLabelText('密钥名称'),'Retry');
    await user.click(screen.getByRole('button',{name:'创建 API Key'}));
    await screen.findByRole('alert');
    await user.click(screen.getByRole('button',{name:'创建 API Key'}));
    await screen.findByLabelText('新密钥完整值');
    expect(api.create.mock.calls[0][1]).toMatch(/^[0-9a-f-]{36}$/);
    expect(api.create.mock.calls[1]).toEqual(api.create.mock.calls[0]);
  });

  it('does not hide a revoked record before gateway removal is confirmed', async () => {
    const user=userEvent.setup();api.list.mockResolvedValue([{...key,is_active:false,backend:'litellm',status:'revoked'}]);
    api.remove.mockResolvedValue({kind:'operation',operation_id:'op-2',credential_id:key.id,status:'reconciling'});
    api.operation.mockResolvedValue({operation_id:'op-2',credential_id:key.id,status:'reconciling'});
    render(<PersonalApiKeys />);await screen.findByText('Codex');
    await user.click(screen.getByRole('button',{name:'永久删除 Codex'}));
    await user.click(screen.getByRole('button',{name:'确认永久删除记录'}));
    expect(await screen.findByText(/操作正在核对/)).toBeInTheDocument();
    expect(screen.getByText('Codex')).toBeInTheDocument();
    expect(screen.queryByText('已删除 Token 记录')).not.toBeInTheDocument();
  });
  beforeEach(() => {
    vi.resetAllMocks();
    api.list.mockResolvedValue([]);
    api.pending.mockResolvedValue([]);
    api.status.mockResolvedValue({ allowed: 1, active: 0, requests: [] });
    api.remove.mockResolvedValue(undefined);
    api.create.mockResolvedValue({ ...key, key: 'sbk_fixture_only_once' });
    api.rename.mockResolvedValue({ ...key, label: '工作电脑' });
    api.revoke.mockResolvedValue({ ...key, is_active: false });
  });

  it('rediscovers a pending operation on mount without creating anything', async () => {
    const user=userEvent.setup();
    api.pending.mockResolvedValue([{operation_id:'op-reload',credential_id:'key-1',status:'submitted'}]);
    render(<PersonalApiKeys />);
    expect(await screen.findByText(/操作正在核对/)).toBeInTheDocument();
    await user.type(screen.getByLabelText('密钥名称'),'Another');
    expect(screen.getByRole('button',{name:'创建 API Key'})).toBeDisabled();
    expect(api.create).not.toHaveBeenCalled();
  });

  it('removes only revoked list records after inline confirmation and preserves failures', async () => {
    const user = userEvent.setup();
    api.list.mockResolvedValue([key, { ...key, id: 'revoked', label: 'Old', is_active: false }]);
    api.remove.mockRejectedValueOnce(new Error('移除失败'));
    render(<PersonalApiKeys />);
    await screen.findByText('Old');
    expect(screen.queryByRole('button', { name: '永久删除 Codex' })).not.toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '永久删除 Old' }));
    expect(api.remove).not.toHaveBeenCalled();
    await user.click(screen.getByRole('button', { name: '确认永久删除记录' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('移除失败');
    expect(screen.getByText('Old')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '确认永久删除记录' }));
    await waitFor(() => expect(screen.queryByText('Old')).not.toBeInTheDocument());
    expect(screen.getByText('Codex')).toBeInTheDocument();
    expect(api.revoke).not.toHaveBeenCalled();
  });

  it('loads an empty list without provisioning a key and explicitly creates a named key', async () => {
    const user = userEvent.setup();
    render(<PersonalApiKeys />);
    expect(await screen.findByText('还没有 API Key')).toBeInTheDocument();
    expect(api.create).not.toHaveBeenCalled();
    await user.type(screen.getByLabelText('密钥名称'), 'Codex');
    await user.click(screen.getByRole('button', { name: '创建 API Key' }));
    await waitFor(() => expect(api.create).toHaveBeenCalledWith('Codex', expect.any(String)));
    expect(await screen.findByLabelText('新密钥完整值')).toHaveValue('sbk_fixture_only_once');
    await user.click(screen.getByRole('button', { name: '我已保存，关闭' }));
    expect(screen.queryByLabelText('新密钥完整值')).not.toBeInTheDocument();
    expect(screen.getByText('sbk_fixture…')).toBeInTheDocument();
    expect(window.localStorage.getItem('gateway-api-key')).toBeNull();
  });

  it('blocks a second active key for the same user', async () => {
    const user = userEvent.setup();
    api.list.mockResolvedValue([key]);
    render(<PersonalApiKeys />);
    await screen.findByText('Codex');
    await user.type(screen.getByLabelText('密钥名称'), 'Second');
    expect(screen.getByText('活动密钥 1 / 1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: '创建 API Key' })).toBeDisabled();
    expect(api.create).not.toHaveBeenCalled();
  });

  it('renames a key and requires confirmation before revoking it', async () => {
    const user = userEvent.setup();
    api.list.mockResolvedValue([key]);
    render(<PersonalApiKeys />);
    await screen.findByText('Codex');
    await user.click(screen.getByRole('button', { name: '重命名 Codex' }));
    const input = screen.getByLabelText('新的密钥名称');
    await user.clear(input); await user.type(input, '工作电脑');
    await user.click(screen.getByRole('button', { name: '保存名称' }));
    await waitFor(() => expect(api.rename).toHaveBeenCalledWith('key-1', '工作电脑'));
    await screen.findByText('工作电脑');
    await user.click(screen.getByRole('button', { name: '删除 工作电脑' }));
    expect(api.revoke).not.toHaveBeenCalled();
    const confirmation = screen.getByRole('group', { name: '确认删除密钥' });
    await user.click(within(confirmation).getByRole('button', { name: '确认删除' }));
    await waitFor(() => expect(api.revoke).toHaveBeenCalledWith('key-1', expect.any(String)));
    expect(await screen.findByText('已删除')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /重命名/ })).not.toBeInTheDocument();
    expect(screen.getByText('sbk_fixture…')).toBeInTheDocument();
  });

  it('preserves a failed create name and prevents duplicate in-flight creation', async () => {
    const user = userEvent.setup();
    api.create.mockRejectedValueOnce(new Error('暂时不可用'));
    render(<PersonalApiKeys />);
    await screen.findByText('还没有 API Key');
    await user.type(screen.getByLabelText('密钥名称'), '脚本');
    await user.click(screen.getByRole('button', { name: '创建 API Key' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('暂时不可用');
    expect(screen.getByLabelText('密钥名称')).toHaveValue('脚本');
    let resolve: (value: typeof key & { key: string }) => void = () => {};
    api.create.mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
    await user.dblClick(screen.getByRole('button', { name: '创建 API Key' }));
    expect(api.create).toHaveBeenCalledTimes(2);
    resolve({ ...key, key: 'sbk_fixture_retry' });
    expect(await screen.findByLabelText('新密钥完整值')).toHaveValue('sbk_fixture_retry');
  });

  it('does not show a raw secret returned by an old list endpoint', async () => {
    api.list.mockResolvedValue([{ ...key, key: 'sbk_unexpected_list_secret' }]);
    render(<PersonalApiKeys />);
    await screen.findByText('Codex');
    expect(screen.queryByLabelText('新密钥完整值')).not.toBeInTheDocument();
    expect(document.body.textContent).not.toContain('sbk_unexpected_list_secret');
  });

  it('allows retrying a failed list request without creating keys', async () => {
    const user = userEvent.setup();
    api.list.mockRejectedValueOnce(new Error('列表加载失败')).mockResolvedValueOnce([]);
    render(<PersonalApiKeys />);
    expect(await screen.findByRole('alert')).toHaveTextContent('列表加载失败');
    await user.click(screen.getByRole('button', { name: '重新加载密钥' }));
    expect(await screen.findByText('还没有 API Key')).toBeInTheDocument();
    expect(api.create).not.toHaveBeenCalled();
  });

  it('keeps the full secret available for manual copy when clipboard fails', async () => {
    const user = userEvent.setup();
    vi.spyOn(navigator.clipboard, 'writeText').mockRejectedValue(new Error('denied'));
    render(<PersonalApiKeys />);
    await screen.findByText('还没有 API Key');
    await user.type(screen.getByLabelText('密钥名称'), 'Codex');
    await user.click(screen.getByRole('button', { name: '创建 API Key' }));
    await screen.findByLabelText('新密钥完整值');
    await user.click(screen.getByRole('button', { name: '复制完整密钥' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('手动复制');
    expect(screen.getByLabelText('新密钥完整值')).toHaveValue('sbk_fixture_only_once');
  });

  it('does not optimistically remove a key on delete failure and supports cancellation', async () => {
    const user = userEvent.setup();
    api.list.mockResolvedValue([key]);
    api.revoke.mockRejectedValueOnce(new Error('删除失败'));
    render(<PersonalApiKeys />);
    await screen.findByText('Codex');
    await user.click(screen.getByRole('button', { name: '删除 Codex' }));
    await user.click(screen.getByRole('button', { name: '确认删除' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('删除失败');
    expect(screen.getByText('可用')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: '取消删除' }));
    expect(screen.queryByRole('group', { name: '确认删除密钥' })).not.toBeInTheDocument();
    expect(api.revoke).toHaveBeenCalledTimes(1);
  });
});
