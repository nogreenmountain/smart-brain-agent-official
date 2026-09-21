# M02 — project-management

## 业务职责

管理组织内项目、部门层级、项目成员、创建申请和项目生命周期。

## 不负责

不负责资料内容、RAG 索引、Wiki 编译、AI 用量和部署。

## 当前实现

- `agentops_local/api/routes/v4/projects.py`
- `agentops_local/api/routes/v4/team_members.py`
- 项目/部门/成员相关迁移和前端页面。

## 数据与接口

- 数据：`projects`、`departments`、`project_members`、`project_creation_requests`、`project_department_migrations`。
- 输入：项目元数据、成员变更、部门迁移请求。
- 输出：项目目录、成员角色、生命周期状态、审批结果。
- 公共接口：Project Catalog、Project Membership、Department Migration API。
- 内部接口：SQL 锁、迁移状态机、审计写入。

## 权限与耦合

依赖 M01 的组织和项目权限。当前清理逻辑还会直接修改 documents、material intakes、memory drafts、Wiki pages 和 meeting summaries，形成跨领域写耦合。

## 测试与拆分条件

需要 RLS/跨组织/成员角色/迁移并发测试。拆分前必须把跨域清理改成事件或明确的领域命令。
