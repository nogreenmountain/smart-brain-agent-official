# M01 — platform-core

## 业务职责

提供用户身份、会话、组织成员关系、角色权限、公共审计和共享配置接口。

## 不负责

不负责项目业务、Wiki 内容、AI 用量、模型调用、文件解析或部署编排。

## 当前实现

- `api/agentops/auth/`
- `agentops_local/auth/`
- `agentops_local/common/`
- `agentops_local/rag/authz.py` 中仍有待下沉的权限能力

## 数据与接口

- 数据：`auth.users`、`public.users`、`orgs`、`user_orgs`、`org_invites`、`audit_logs`。
- 输入：JWT/Cookie、用户 ID、组织 ID、资源权限请求。
- 输出：认证主体、角色、权限判定、审计事件。
- 公共接口：`AuthenticatedRoute`、`current_user_id`、`require_member`、`require_admin`、`is_system_admin` 的稳定替代接口。
- 内部接口：session/ORM 实现、JWT 解析细节、Supabase client。

## 权限与敏感数据

处理 JWT、Cookie、用户身份和权限信息。任何日志不得输出 token、Cookie 或密码。

## 测试与部署

应覆盖认证失败、禁用用户、组织角色、跨组织访问和审计。当前不能独立部署，必须作为 API 的平台层运行。

## 当前耦合与拆分风险

多个领域直接导入 authz 和 ORM；若先拆仓，容易复制权限判断或绕过 RLS。拆分前必须先形成单向权限 port 和兼容适配层。
