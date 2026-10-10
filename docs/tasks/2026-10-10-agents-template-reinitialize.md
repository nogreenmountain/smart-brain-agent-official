# 已有项目 AGENTS.md 重新初始化为最新模板

## 任务身份与范围

- 任务编号：`agents-template-reinitialize-20261010`
- 负责人：Codex
- 创建／更新时间：2026-10-10 09:47–09:54、15:40–15:56（Asia/Shanghai）
- 开发阶段：调查、复现、方案与本地实施验证已完成；生产发布未授权
- 部署范围：未部署；业务源码与测试已作为本地候选修改，生产数据与服务未动
- 目标：复现已有 AGENTS.md 点击初始化无法被最新模板覆盖的问题，实施安全的显式重置方案
- 本轮授权：用户要求调查、复现、写方案并解决；生产发布、真实 PG 验收不在本轮授权内

## 代码与版本

- 权威源码：`C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端`
- 分支／基线：`codex/project-memory-no-adapter`／`431022ba5fe5169aa6be97a5e602f5995692ab91`
- 当前 API 源：`agentops_local/api/routes/v4/project_agents.py`
- API 源 SHA（09:54）：`8fe177fb8b7d5534c6425e2b3c921a9f6de5927599cf9ea3677ae79f32580fea`
- 既有 dirty 修改：保留；本任务未将其归入变更，也未整体提交或推送

## 实施内容（本地候选，15:40–15:53）

- 后端 `project_agents.py`：新增 `GET /agents/template-preview`（管理员，no-store，返回当前 version/sha256 与模板 version/sha256 及 identical）、`POST /agents/reset-to-template`（管理员，CAS 负载 expected_version/expected_sha256/template_sha256；模板摘要或文件版本不符返回 409；内容已相同返回 `unchanged` 不写库）、`GET /agents/versions` 与 `GET /agents/versions/{version}/download`（成员可读版本历史与归档下载）。重置先锁当前 files 行（无行时锁 projects 父行），归档旧字节到 `project_agents_file_versions` 后再写入，新修订号取 max(当前 version, 历史最大 version)+1；全新文件版本 = 模板版本（AGENTS_TEMPLATE_VERSION=4），与既有 initialize 语义一致。
- 归档不依赖数据库触发器：迁移中 `archive_project_agents_version` 只有 CREATE FUNCTION 且无 CREATE TRIGGER，且其引用的 `updated_by_user_id` 列不存在，不能依赖；本次按 `upload_agents` 既有模式显式 INSERT 历史行。
- 前端 `lib/api.ts`：新增 `ProjectAgentsTemplatePreview`/`ProjectAgentsResetResult`/`ProjectAgentsVersionSummary` 类型与 4 个对应 API 函数（均带 encodeURIComponent，错误统一 ApiError）。
- 前端 `ProjectAgentsPanel.tsx`：已有文件时显示"重新初始化为最新模板"（无文件时才显示"初始化"）；点击后弹预览弹窗，展示当前版本/摘要与模板版本/摘要，identical 时提示无需覆盖且不提供确认键；确认携带 CAS 负载，409 时提示并自动重新拉取最新预览；新增成员可见的版本历史列表与逐版本下载（`AGENTS-v{N}.md`）。GET/download/context/项目创建的共用补缺语义未动。

## 已完成与未完成

| 项目 | 状态 | 证据 |
|---|---|---|
| 缺失 AGENTS 初始化 | 已复现 | `.artifacts/agents-template-reinitialize-20261010/backend/reproduction-result.json` |
| 已有旧模板再次初始化 | 已复现 | 同上，version/hash/正文不变 |
| 已有自定义文件再次初始化 | 已复现 | 同上，version/hash/正文不变 |
| 前端点击与假成功提示 | 已复现 | `.artifacts/agents-template-reinitialize-20261010/frontend/ui-reproduction.log` |
| 实际 API 源与当前容器身份只读核对 | 已完成 | `backend/current-readonly.json`，生产身份核对期间保持 |
| 后端预览/CAS重置/版本历史候选 | 已实施并本地验证 | `backend-pytest-final.log` 21 passed |
| 前端预览弹窗/CAS重试/版本历史候选 | 已实施并本地验证 | `frontend-vitest-final.log` 40 files／205 passed；`frontend-tsc-final.log` exit 0；`frontend-build-final.log` exit 0 |
| 真实 PG 并发/HTTP/完整鉴权候选验收 | 未执行 | 需单独隔离数据库与候选代码 |
| 生产修复或模板批量覆盖 | 未执行 | 需单独授权并核对容量门禁 |

## 根因

`initialize_agents()` 生成模板后使用 `ON CONFLICT (project_id) DO NOTHING`，已有行原样返回；显式 POST 因此返回200但不改变内容。GET、download、context 和项目创建也复用该补缺函数，不能把它直接改成覆盖。前端无条件把成功HTTP响应显示为“AGENTS.md 已初始化”，不比较 hash/version。

## 验证记录

| 时间 | 命令与环境 | 结果 | 证据与限制 |
|---|---|---|---|
| 09:44 | dashboard focused tests，Node/Vitest | 2 files／7 tests passed | `frontend/existing-focused-tests.log` |
| 09:47 | 当前组件隔离点击复现 | 1 test passed；旧内容/version/hash不变但提示初始化 | `frontend/ui-reproduction.log` |
| 09:49 | bundled Python，AST加载实际 helper，内存SQLite执行原INSERT | 3场景通过；缺失生成v4，已有v1/v9不变 | `backend/reproduction-result.json`；非真实PG并发/HTTP |
| 09:54 | `inspect_current_readonly.py` 远程只读 | API源码SHA一致；触发器、history约束、容器代际核对 | `backend/current-readonly.json`；无业务写入 |
| 09:43 | backend pytest | 未启动：bundled Python无pytest/FastAPI | `.artifacts/agents-template-reinitialize-20261010/backend-project-agents-tests.log` |
| 15:45 | dashboard 两目标文件测试 | 2 files／17 tests passed | 含预览弹窗、CAS 负载、409 重取预览、取消不写、版本历史下载 |
| 15:47 | `project-memory/page.test.tsx` 全量中单测失败 | 创建项目改为按需弹窗后兼容路由测试仍断言常驻表单；属管理工作台布局任务遗留，仅更新该用例为弹窗流程，页面源码未动 | 修复后同文件 6 passed |
| 15:53 | dashboard 全量 vitest | 40 files／205 tests passed | `frontend-vitest-final.log` |
| 15:54 | TypeScript `--noEmit` | exit 0 | `frontend-tsc-final.log` |
| 15:55 | Next 生产构建 | exit 0 | `frontend-build-final.log` |
| 15:55 | backend pytest（专用 venv） | 21 passed in 0.97s | `backend-pytest-final.log`；整目录收集另有 25 个预有 `No module named 'agentops'` 错误，git stash 对照证明与本改动无关 |

## 方案与下一步

详细方案见 [`docs/plans/2026-10-10-agents-template-reinitialize.md`](../plans/2026-10-10-agents-template-reinitialize.md)。核心是保留缺失补建，新增管理员可用的预览＋CAS确认的 reset-to-template 动作，锁定项目父行和当前行，归档旧字节，使用递增文档revision，返回 `created/replaced/unchanged`，前端明确提示并提供历史下载。模板版本与文档revision分开，不能用4覆盖所有已有version。

## 决策与变更日志

| 时间 | 变化 | 原因 |
|---|---|---|
| 09:47 | 开始隔离调查 | 用户反馈已有项目初始化不能被新模板覆盖 |
| 09:49 | 当前 helper 动态复现通过 | 确认不是缓存，而是冲突忽略语义 |
| 09:54 | 实际安装触发器/约束只读核对 | 为历史归档、并发和迁移方案提供边界 |
| 15:40 | 按已确认方案实施后端正预览/CAS/历史 | 用户确认方案并要求解决 |
| 15:53 | 前端弹窗与版本历史完成、全套件转绿 | 含布局任务遗留的兼容路由测试修正 |

## 候选源码 SHA256（15:56 核对）

| 文件 | SHA256 |
|---|---|
| `agentops_local/api/routes/v4/project_agents.py` | `6B7D17F05DD66496AB5BFC85E7368C76B15EF20915EB1DB09C7795BB27EADD12` |
| `agentops_local/tests/test_project_agents.py` | `2B80DF0574D4232B9D0C274F6387A9BE78033D815AA8A522DA05AE8965E109E1` |
| `smartbrain-dashboard/lib/api.ts` | `D7464BAF191361A83D36065CDDF546B8449D043C3DE4AB7A3CC5E270EC6FAE47` |
| `smartbrain-dashboard/lib/api.project-agents.test.ts` | `E847AB6DE8640A16B0445BCE660589D0BF300FB490C5E22510B547829CCFFB69` |
| `smartbrain-dashboard/components/project/ProjectAgentsPanel.tsx` | `E678EB4086F13C63FD27E12DE5309C4D19095E72F57632C8129D53EE885EE0BE` |
| `smartbrain-dashboard/components/project/ProjectAgentsPanel.test.tsx` | `9F8AE8416831E08797B090882A8B03AD52028FB417318F15290F48B834D7FB1F` |
| `smartbrain-dashboard/app/(with-shell)/project-memory/page.test.tsx` | `19C31CA4DE26998BAD2B79AE51E2810657EACDF1B1266C97045166CE67196D68` |

汇总清单：`.artifacts/agents-template-reinitialize-20261010/implementation-manifest.json`。

## 运行中任务与不可重跑动作

本任务没有运行中的生产任务、模型请求、迁移、上传、模板覆盖或重启。隔离复现使用合成UUID与内存数据库，可安全重跑；不得重跑旧任务中的真实项目读取/上传脚本。

## 2026-10-10 17:25 已发布生产（agents-template-release-20261010-r1）

核对时间：17:09–17:16（Asia/Shanghai）。本任务后端四端点与前端面板随 [agents-template-release-20261010-r1](../releases/agents-template-release-20261010-r1.md) 实际发布生产：主 API 容器 `621935d93b37…`（镜像 `aa31ae74b5ef…`，仅叠加替换 project_agents.py）、主前端容器 `85f21545e254…`（镜像 `743d5093f6c4…`）；公网 5×200＋5×401、新文案 chunk 公网可获、45 旧静态资产保留、1023 无关容器代际保持、backup 20；旧容器停止保留，归档与镜像 tar 完成（非冻结备份点）。真实管理员会话的功能闭环（预览→CAS 重置→历史下载）未执行，待员工侧授权验收；生产实际回退未触发。