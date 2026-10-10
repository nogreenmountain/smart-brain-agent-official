# 已有项目 AGENTS.md 重新初始化为最新模板的解决方案

编写：Codex。核对时间：2026-10-10 09:47–09:54（Asia/Shanghai）。任务：`agents-template-reinitialize-20261010`。阶段：调查与隔离复现已完成，以下为待实施方案；本轮未修改业务源码、生产文档或数据库。

## 目标与成功标准

项目负责人对已有 AGENTS.md 点击“重新初始化为最新模板”，预览并确认后，服务器当前文件确实变为最新模板。原文件完整保留在可下载的版本历史中；遇到其他人刚修改文件时明确报冲突，不静默覆盖。缺失文件的自动补建、普通成员读取/下载、项目隔离保持。

覆盖指替换服务器的整个当前文件。自定义规则会从当前文件移出，旧字节留在历史；不自动猜测哪些段落应合并。需要保留自定义规则的负责人可以取消，继续使用“上传更新”。服务器成功后仍需下载并替换本地文件、新开 Codex 会话。

## 复现与根因

| 场景 | 本次实测 | 结论 |
|---|---|---|
| 文件不存在 | 执行当前初始化函数，生成模板 v4、716 字节的合成项目规则 | 初始化可以补缺 |
| 已有合成旧模板，文档版本1 | 执行当前接口函数后内容、version、SHA、更新时间均不变；重复亦不变 | 不能升级已有默认模板 |
| 已有合成自定义文档，文档版本9 | 同上，完整旧文档原样返回 | 不能主动覆盖自定义文件 |
| 当前 React 组件点击初始化 | initialize API 被调用1次，模拟成功返回旧文件；页面显示“AGENTS.md 已初始化”，仍是旧内容/版本/hash | 提示无法说明是否更新 |

后端 `agentops_local/api/routes/v4/project_agents.py:139` 的 `initialize_agents` 先生成新模板，但 INSERT 使用 `ON CONFLICT (project_id) DO NOTHING`，随后查询并返回原行。POST `/agents/initialize` 调用同一函数。GET、download、context 和项目创建也复用该补缺逻辑，不能直接将共用 INSERT 改为覆盖。前端 `ProjectAgentsPanel.tsx:76` 无条件提示成功；`lib/api.ts:1350` POST body 为 `{}`，没有覆盖模式或预期版本。GET 已设 `no-store`，该复现不依赖缓存。

09:54只读核对实际主API：CID `e6a1a794f8334ffda576f853b34eb6e9c99b70a89c9f785a51b68996fcb7cecb`，image `sha256:8eac15848ae9e29080d9deba458d588e572d8b0b1188f8f10dc60040ec41d402`，StartedAt `2026-10-08T14:08:37.368067076Z`。运行中后端源码 SHA `8fe177fb8b7d5534c6425e2b3c921a9f6de5927599cf9ea3677ae79f32580fea` 与复现源码一致，核对期间代际保持。已安装的 `archive_project_agents_version` 触发器为 enabled、AFTER INSERT OR UPDATE，归档的是 NEW；history 主键 `(project_id, version)`，同版本不同内容会拒绝。

**复现边界**：后端执行的是原接口/helper/template代码与真实内存 SQLite INSERT，仅移除 SELECT 的 PostgreSQL `::text` 方言；鉴权与响应对象为合成夹具。UI 使用当前组件与模拟API。没有对真实项目调用生产初始化POST，没有生产浏览器点击、真实PG并发或完整鉴权验收。本地后端 pytest 因缺依赖无法启动，不能记为产品通过；已有前端专项7项及新复现1项通过。

证据：`.artifacts/agents-template-reinitialize-20261010/backend/reproduction-result.json`、`backend/current-readonly.json`、`frontend/ui-reproduction.log`、`frontend/existing-focused-tests.log`。脚本和失败的环境启动日志均保留。

## 确定采用的设计

1. 保留现有 initialize 的“缺失才创建”语义，兼容旧客户端和读取路径。已有文件的网页按钮改为“重新初始化为最新模板”，进入预览后才提交新动作；缺失时仍显示“初始化”。
2. 增加独立的预览与重置接口；使用既有 `require_admin` 权限（项目 admin/owner、既有系统管理员规则），服务端鉴权始终生效。普通成员可照常读取当前文件，不能重置或操作历史。
3. 当前 `version` 继续作为文档修订序号，保持已有值，绝不把所有文件重置为4。模板版本独立表示；新模板仍使用 `smartbrain-agents-version: 4`。文件无论v2还是v9，都可能是自定义文件，不能只看 version 或注释判断其来源。
4. 预览绑定当前修订号/hash和目标模板版本/hash；确认时重新计算并核对二者。内容或模板/项目名称在预览后变化时返回409并要求重新预览。
5. 保存共用项目行锁、严格历史校验和单次事务；新修订号取 `max(当前version, 已有history最大version)+1`，缺失且无历史时从1开始。已完全相同的内容返回 unchanged，不增加版本、不变更更新时间。
6. 不批量更新所有既有项目；只处理用户主动选择、当前有管理权限的项目。不修改个人Key、项目归属账单、OAuth、适配器、Wiki和员工内容。

## 接口合同

接口均沿用 Cookie 认证和原项目UUID路径，不接受客户端提供目标项目名称、模板正文、操作者或任意模板版本。

| 接口 | 权限与行为 |
|---|---|
| 现有 `POST /v4/projects/{id}/agents/initialize` | 保留缺失补建、已有原样返回；响应可加 `action=created/unchanged`，保留原文件字段 |
| 新 `GET /v4/projects/{id}/agents/template-preview` | 管理权限；只读，不补建。返回当前 revision/hash/字节数、目标最新模板的内容/version/hash/字节数和会否替换 |
| 新 `POST /v4/projects/{id}/agents/reset-to-template` | 管理权限；须提交预览状态和确认。成功返回 action、previous_version、当前文件、独立 template_version |
| 新 `GET /v4/projects/{id}/agents/versions` | 管理权限；分页返回历史元数据，不返回所有正文 |
| 新 `GET /v4/projects/{id}/agents/versions/{version}/download` | 管理权限；只读返回该版本原字节，不调用补建helper；不存在404 |
| 现有 upload | 保持 markdown body；共享保存事务/锁，新版客户端通过头部携带预期revision/hash，旧协议兼容期详见下文 |

确认请求示例（仅字段示意）：

```json
{
  "expected_version": 9,
  "expected_sha256": "<预览时当前文件的完整64位SHA>",
  "expected_template_version": 4,
  "expected_template_sha256": "<预览时目标模板的完整64位SHA>",
  "confirm_replace": true
}
```

缺失文档必须提交 `expected_version=null` 与 `expected_sha256=null`，表示确认的就是缺失状态；服务端发现已被创建则409。两字段不得只填一个。未确认或字段错误422；缺少必需并发条件428；未登录401、无权限403、项目不存在404。模板或文件冲突409使用明确错误码 `agents_changed` / `agents_template_changed`；不把冲突伪装为初始化成功。

响应示例：

```json
{
  "action": "replaced",
  "previous_version": 9,
  "template_version": 4,
  "agents": {
    "project_id": "<当前项目UUID>",
    "filename": "AGENTS.md",
    "version": 10,
    "sha256": "<新文件SHA>",
    "content": "<服务端为当前项目生成的模板>"
  }
}
```

`action` 为 `created/replaced/unchanged`。文档revision与模板版本分别展示。失败/超时保留原文件和预览，不显示成功；响应丢失时先GET核对，不自动重发写请求。相同旧预期状态的并发确认只有一条可以写入，另一条409；刷新后再次确认完全相同模板则unchanged。

## 保存、历史与模板一致性

新增可空 `template_version` 到 current/history，CHECK为正整数或NULL，默认NULL。旧行不重写正文/修订号，不批量根据注释推断来源；未知模板来源显示“自定义或历史文件”。新reset/自动模板创建填实际模板版本，新upload默认NULL。API保留兼容字段 `version`，不要修改历史context token含义。

在同一事务中：

1. 固定锁顺序：项目父行 `FOR UPDATE` → 当前文件行 → history。项目父行解决文件不存在时无法锁行的问题。reset、upload和补建写路径均遵守；项目创建trigger在其父行插入事务内完成。设置 `lock_timeout=2s`、`statement_timeout=10s`，失败完整rollback。
2. 锁后再次验证管理员资格和项目存在；重新生成项目名称/UUID正确的当前模板。校验当前/模板预期状态，禁止 stale preview。
3. 目标与当前字节/hash完全相同则no-op。否则验证存储SHA与内容重算一致，并确保旧当前修订已归档；若该history键已有不同字节/hash则失败，不压过原冲突检查。
4. 旧历史缺失时将旧内容、原修订号及原操作者补到history。当前history仅有 `created_at`，表示归档时间，并无 `updated_at`；不能声称旧current更新时间已完整保存在现有结构。增量迁移增加可空 `source_updated_at`，新归档填写被保存current的原 `updated_at`，旧历史未知值保持NULL。该动作与新current更新必须同事务；不能先commit旧归档后留不确定写状态。
5. 取严格递增的新revision，更新current及操作者。兼容已安装的 `updated_by` 与 `updated_by_user_id`；新保存二者一致，旧归档不改原归属。现有AFTER触发器只负责归档新current，扩展为包含template_version。重构upload避免手工插入新history与trigger双写；对同键不同内容依然报错。
6. commit后返回从保存行读取的文件/hash，不返回预览缓存。读回当前/历史与download字节一致。迁移与保存预检以已安装schema为准：history真实主键为 `(project_id, version)`，`id` 仅可空/default UUID，不能按仓库历史迁移误认为其是主键。验收包含实际trigger/约束预检和事务失败回滚。

恢复历史不降低revision：管理员下载旧版，再经带预期状态的上传生成新修订。历史列表提供“下载此版本”，说明如何上传恢复；不承诺目前已有此入口。候选验收必须真实恢复旧字节为新revision并核对SHA，才能称可恢复。

Python `build_default_agents` 与数据库 `initialize_project_agents()` 当前各维护一份默认内容。本次将模板放入仓库的权威资源（建议 `agentops_local/project_memory/agents_template.md`），生成/核对SQL函数的对应字节；运行镜像必须包含资源，部署source manifest必须收录。新项目trigger、自动補缺、preview/reset对CR/LF、首尾空白/Unicode项目名、UUID替换必须输出相同字节/hash。后继迁移从同一资源生成，禁止只改Python却忘记trigger；不修改已应用的历史迁移。

## 前端流程

1. 点击已有文档的“重新初始化为最新模板”，请求只读预览；弹窗展示当前与新模板、项目名/UUID、文档revision/模板版本。明确“将替换当前自定义规则，旧版保留在历史”。取消不发写请求。
2. 用户点“确认覆盖并保留旧版”后提交绑定状态；pending禁用重复操作、切项目后丢弃旧请求结果。开始动作清除旧notice/error。
3. created提示“已创建最新模板”；replaced提示“已更新为最新模板”；unchanged提示“已是最新模板”。收到新文件即更新预览。409提示“文件或模板已变化，请重新预览”，保留原显示、重新读取；错误不留上一条成功notice。
4. 成功后提供下载与历史下载。提醒覆盖实际项目目录AGENTS.md、核对AGENTS.override.md并新开Codex会话；不声称网页更新会改变另一台电脑或已启动会话。

上传与reset共享锁，但仅锁不能阻止旧客户端blind upload在reset之后覆盖。新版网页上传必须发送预期version/hash；生产兼容期允许旧upload继续既有显式替换行为，记录该边界，不宣布所有旧客户端都获得CAS。待确认所有调用方升级后再单独决定是否对无条件upload返回428；不在本次偷偷破坏旧上传协议。

## 实施阶段与验证

| 阶段 | 文件与变更 | 放行证据 |
|---|---|---|
| 1 接口/保存候选 | `project_agents.py`、`test_project_agents.py`；新增reset/preview、结果类型、共享锁/保存、旧字节历史校验，保留ensure语义 | 先写当前Red病例，候选Green；读取/下载/普通initialize回归不覆盖已有文件 |
| 2 模板/历史 | 新template资源、新可空template_version迁移及触发器扩展；新增隔离PG测试。历史列表/下载、恢复经上传 | 使用当前实际PG schema/trigger建立独立测试库；回退旧正文、新revision/旧UUID/完整历史保持 |
| 3 前端 | `ProjectAgentsPanel.tsx/.test.tsx`、`lib/api.ts`、`api.project-agents.test.ts`；预览确认、状态文案、历史下载、CAS上传 | UI测试、tsc、构建及本地/隔离浏览器点击；下载重算SHA一致 |
| 4 发布候选核验 | 新本任务部署目录、source manifest/release记录；API先于前端、向后兼容迁移 | 实际镜像测试/隔离HTTP+PG、自审及实时容量/backup/maintenance门禁；生产实施另有明确授权后执行 |

关键验收矩阵（未实施，均待候选验证）：

| 病例 | 期望 |
|---|---|
| 旧默认、自定义任意revision | reset后为当前模板，旧字节可下载；revision严格递增 |
| 当前即模板、重复点击 | unchanged，无额外history/更新时间变化 |
| cancel、普通成员、跨项目/禁用账号 | 无写入；鉴权按现有规则拒绝 |
| 两个reset同预期、reset与upload并发 | 不产生重复版本/丢历史；stale确认409 |
| 缺失行并发补建/reset/upload | 父行锁串行，只有一致的current/history，无唯一键500 |
| 相同version不同旧history内容 | 拒绝并完整回滚，冲突证据保留 |
| 历史最大revision高于current | 新revision越过最大历史，不碰撞、不覆盖旧行 |
| 事务断开/SQL失败/响应丢失 | 原子保存；查询原结果，无盲重试 |
| 历史下载再上传恢复 | 旧内容完整还原为新revision，旧版本持续存在 |
| 项目名变更/Unicode/换行；发布模板升级 | 预览失效409；Python/trigger/reset三路径字节一致 |
| 原GET/download/context/project create | 保持项目权限/旧协议，不因新reset逻辑覆盖自定义 |
| 前端失败/409/双击/切项目 | 不留假成功、不提交旧项目预览、不写两次 |

## 发布、回退与限制

当前只交付方案。未进行业务源码修改、生产迁移、初始化/上传、模板批量更新、服务重启或模型请求。刚清退的测试用户/项目不能复活；候选复现使用独立合成数据。

上线前重新核对活动API/前端、edge双视图、备份/maintenance、真实容量，使用当前release机制，不能沿用到期夜间授权。最低储备仍为Docker40GiB、`/srv/smartbrain`20GiB、backups/cold各250GiB；08:31历史值Docker仅高约36MiB，09:54本轮没有重测空间，不能宣布可build/发布。容量不足则停止发布，不删除历史来过门槛。

先应用兼容的增量schema/trigger，再API，再前端。回退功能时先撤前端新入口，再回API；保留已新增的可空字段和所有历史，禁止降版本或删除本次reset结果。需要回退某个文档时按下载旧版→受保护上传生成新revision执行，保存明确操作者与时间，不用代码回滚偷偷恢复文档。

本次已证明原覆盖问题的机制；没有证明修复已上线。完整PG恢复、全writer冻结/整机恢复和真实30人容量仍是原独立未验项，不由此方案替代。
