# AGENTS.md + company-memory 项目记录及适配器退出

- 负责人：当前 Codex；任务编号 project-memory-no-adapter-20261008。
- 用户已确认计划并授权修复、部署。生产于 12:46–12:49 发布，13:00 公网/浏览器及收尾核对通过。
- 工作目录 deb4；分支 codex/project-memory-no-adapter；基线 431022b。另一个 state-sync 工作树没有修改。本轮未提交/推送。
- [执行计划](../plans/2026-10-08-agents-company-memory-no-adapter.md)、[实际发布记录](../releases/project-memory-no-adapter-20261008-r1.md)、[使用说明](../project-conversation-company-memory.md)。
- 私有证据 .artifacts/project-memory-no-adapter-20261008/；不提交凭据、原始配置或员工正文。

## 2026-10-08 AGENTS 默认模板精简

用户反馈初始化的项目 AGENTS.md 过于复杂。已新增 v3 精简模板：约 639 UTF-8 字节/8 行，保留项目 UUID、项目约定与验证、company-memory 授权提交、隐私与停止记录；协议细节交给 company-memory 插件。已有项目文件不覆盖。API 新镜像 SHA `35f4ea73cf9c2956cd843b7c009a01a33706da33fcb0ea1bf71ae0577f078eb3` 已部署；生产 readiness、真实 PG 新项目创建回滚验证、141 个旧文件保持通过。首次候选因覆盖文件权限为 0600 未切换，已保留失败证据并修正为 Docker `COPY --chmod=0644`。

## 13:00 当前终态

备份修复完成，唯一新 online 批次 20261008T033252Z 成功且 36 文件 SHA 通过；timer enabled、无活动备份作业。API/MCP/前端和插件包已上线，旧下载均410，页面模块/检测退出。真实合成成员提交/重复/权限/Wiki统计和浏览器上传下载通过，验收令牌/会话/账号已关闭。

新项目及归档触发器两个遗留故障已修复，真实 PG 回滚验证通过。既有141个 AGENTS 文件、899个无关容器配置/代际保持；908容器/38运行。准确回退 dry-run 及三镜像/源码/私有证据归档完成，没有实际回退或真实模型调用。

使用者须升级/重新连接插件；已有项目负责人确认并更新提交规则。没有全会话自动采集，也未完成整机冻结恢复/原17项维护门禁。后续不重跑本轮缓存清理、备份、迁移、发布、fixture或归档runner。

以下为各阶段历史，遇到冲突以上述13:00终态和实际发布记录为准。

## 已实现

- 专用 record_project_conversation：明确项目 UUID、认证成员、可用账户与写权限、wiki:propose scope；拒绝伪造身份/时间/用量字段、秘密、控制字符、system/developer/tool 消息；最多 200 条选定消息/200000 UTF-8 字节。
- canonical 与 Wiki/版本/来源统一写入；submission_id + 内容 hash 幂等，相同内容重试不重复，不同内容冲突；Wiki 失败保留正文，可重试；已删除页面的重复回执不假称 published，而是恢复关联页面。
- 模型为 client_declared 或 unknown，无可信 Token 时 status=unknown/total_tokens=null；上传时间是提交时间，非模型完成时间。整数 0 只为兼容占位，内部 mcp 引用不是模型 request_id。
- 新迁移仅加 provenance 字段/约束与幂等索引，保留旧记录、AGENTS 和 RLS，只在隔离测试库执行。
- AGENTS 默认模板 v3 与仓库插件指引更新，已有文件不覆盖；无工具或失败时明确未完成记录。仓库插件 0.2.0 候选不代表已安装插件升级。
- 前端适配器模块、检测、端口、启动器/helper 删除；三个公开脚本、活动工具脚本及专用旧测试删除，Git 历史保留。AGENTS 初始化/上传/下载保留。
- 编译后的前端对四个退休地址 GET/HEAD 返回 410/no-store；准备了 Nginx 精确 location 退休片段，尚未安装。

## 实际运行源码合并

主 API project_agents 基线与线上字节相同。MCP 比工作树多资料检索接口且 search 带跨项目结果校验，不能用旧本地文件覆盖。已从实际服务同步 server/operations/materials，再合并本次变更；原 operations 42 和 server 36 callable AST 保持。原 30 工具保留，新清单 31；候选服务版本 1.4.0。资料工具实现并非本轮新设计，未冒称其全部生产闭环重新验收。

MCP overlay 与 API overlay 只复制本次必要文件并继承当时确切活动镜像。通用 MCP Dockerfile 也改为以已核对运行镜像为基底，避免旧 API 父镜像丢掉已有资料/鉴权能力。没有生产镜像构建、导入或业务重启。

## 验证及局限

- 后端专项 44：其中真实 PG 12、纯提交校验 16、AGENTS 9、操作层 7。Wiki/MCP 回归 26；合计 70 项。
- 真 PG 使用独立 sb_memory_no_adapter_test_r1 和合成成员/项目，原 pilot DB/生产 DB 不迁移；并发、跨成员、禁用/封禁/匿名/只读/非成员、内容冲突、Wiki 失败、真实 ledger/stats 路由体及受限角色 RLS通过。
- 实际 MCP 库在独立内存进程加载候选、连接隔离 PG，通过发现/提交/重试/scope/额外字段拒绝和原工具清单保持。使用合成认证 identity，并非公网 Token/Cookie 鉴权闭环。
- 前端 40 文件/177 passed，tsc、Next build、实际组件浏览器负责人/成员预览、8 项编译产物下载 HTTP 检查通过。
- 既有分类按钮测试在身份异步加载前读取引发一次全量失败，受控 pending-profile 实验复现；修正为 findByRole 等待后全量通过。原失败日志保留。原 PersonalApiKeys hooks lint 警告未由本任务产生，仍保留。
- Nginx 片段仅临时配置语法校验，通过后临时文件退出清理，未 reload 或修改活动配置。

证据：backend-green.log、backend-regression.log、frontend-tests.log、frontend-tests-before-timing-fix.log、frontend-timing-red.log、frontend-build.log、typecheck.log、mcp-runtime.log、preview-*.png、preview-result.json、download-http-result.json、nginx-syntax.log、runtime-source-comparison.json、production-final-readonly.json、source-manifest.json。

## 当前生产与下一步

10:50:54 只读复核仍 902 容器/38运行。Docker 可用 34,370,764,800 字节（约32.01 GiB），低于确认计划的40 GiB；backup failed/exit-code、MainPID=0、Job空。生产三个下载 URL 仍200；线上网页和 MCP 仍旧版本。不得宣称已经撤下或新工具已上线。

先处置容量/备份门槛，保留旧资源；不自行清理旧容器、镜像、证据或重跑备份。之后核对所有实际前端来源闭包与云端/edge配置，再构建固定 Linux 候选，按发布记录做专项备份/恢复验证、加法迁移、MCP/API→前端/插件顺序切换和真实入口验收。

公网脚本 hash 与主前端文件一致，反向隧道分别提供主前端和 edge。edge 的根入口仍指向旧 workday 前端，而 /admin 指向主前端，不能只删一个入口或按钮就称全站完成。旧 relay 仓库配置不能直接覆盖线上。

## 不可重跑动作及收尾

- 已在 pilot PG 创建隔离测试 DB/合成 role、应用候选迁移、写入合成测试记录；保留该库和私有连接配置，不能把它当生产业务数据。测试可以在该明确测试库继续，禁止把 DSN 换成生产库。
- 没有生产 Key/Token 签发、模型调用、生产 DDL、备份启动、路由切换或服务重启；旧 Monitor 保持退休。
- 本地依赖安装、构建和测试已终态；本轮本地预览/Next服务器及临时 SSH PG tunnel 已停止并核对无遗留监听。隔离 DB 保留，无新 worker/timer/自动任务/子代理。
- Git 变更均为本任务候选及必要运行源码合并，未自动提交；接续先读 CURRENT、计划、任务及发布记录，重新核对运行版本/门槛，不重放历史发布器。

门槛处置问题已提交给用户：先修复备份/容量，或明确豁免本次容量门槛并保留专项备份恢复及回退验证。尚未收到该问题答复，不能据已确认实施计划推断门槛豁免。

## 生产磁盘核查接续

用户询问生产 3 TB 是否占满、有什么可以清理。本轮只读核查确认：1 TB cold 与 2 TB backups 分别仍有约 253/586 GiB 可用；Docker 是 256 GB SSD 上约 98 GiB 的独立 LV，文件系统约 95.9 GiB，可用约 32 GiB。没有整机磁盘占满。Docker 与 containerd 的 du 是同一份 bind mount 存储，不能相加。

Docker 报可回收构建缓存 11.24 GB（约 10.47 GiB）、镜像 13.61 GB；停止容器可写层仅 405.2 MB。大盘另外有 ClickHouse 备份暂存约 483 GiB、失败备份约 150 GiB、旧备份约 357 GiB、恢复测试/失败恢复目录约 231 GiB，均为待核对保留规则的候选，不能认定可全部删除。详见 [磁盘核查](../ops/disk-capacity-20261008.md)。

没有执行删除/prune、磁盘迁移、扩容、备份重跑或生产发布；此前候选包和测试状态保留。本次问询没有豁免发布门槛或授权删除历史资源。优先处理构建缓存的建议不意味着已经实际释放空间；后续需明确清理范围并核对物理释放量。

## 用户授权缓存清理与历史目录整理

接续用户“先处理构建缓存，再整理历史备份和恢复目录”。11:11:52 持备份→维护双锁执行一次 `docker builder prune --all --force --filter until=168h`，exit0。实际 Docker 分区可用 34,277,556,224→45,529,014,272 字节，约释放10.48 GiB，剩余42.40 GiB，容量门槛恢复。全902容器/38运行、全部 Config/HostConfig/Image hash与启动代际、镜像清单保持；严格TLS公开页面/ready200、匿名Key/model401。

历史目录已整理73个批次、60个暂存、81个旧备份子目录、16个恢复对象的清单。49个暂存找到对应归档；29个旧目录与新盘记录清单相同，尚不称完整数据迁移验证。旧20260829T183050Z备份仍有bind mount，Sep10一failed内部complete，最近online/frozen和恢复基线均列为保留。只读暂存核验首次因锁竞争拒绝，实际确认空闲后继续核验；无历史归档/恢复目录删除。详见[清理与整理](../ops/disk-cleanup-20261008.md)，私有生产证据目录`/srv/smartbrain-backups/backups/docker-cache-cleanup-20261008-r1`，本地`disk-cleanup-20261008/`。

不要重复缓存清理runner（既有intent/result已终态），不要将生产变更继续描述为“全程只读”。应用候选未发布，备份failed/专项恢复门槛仍待，不重跑旧备份、不绕开保留规则或直接删除旧恢复目录。

11:18:13 首批暂存核验完成：Sep24在线批次clickhouse压缩包实际SHA与记录相同，全部994文件/11,051,543,654字节与其暂存逐文件一致，无缺失/多余；源/归档未删除，不称完整DB恢复通过。其他48有归档暂存仍待同标准验证。核验进程已终态，无需重跑既有完整性核验或缓存prune。

## 备份失败诊断

用户问失败原因及处理方式。11:22–11:23只读核查02:45日志及活动源码：容量两次passed，实际终止为service-state检测ai-worklog-worker配置hash不一致，发生在数据备份前。9/24实际worker加载外部worklog-hotfix override，backup-20260923登记只加载单Compose，遗漏environment/volumes补丁；镜像身份通过，Compose版本同5.5.0。只读渲染加入确切原override后，登记20个运行非relay服务hash全部匹配。没有生产配置变更、备份启动或恢复；不能将此20服务验证冒充全38运行容器/writer完整覆盖。[根因与处理建议](../ops/backup-failure-diagnosis-20261008.md)，私有drift-report.json。下一步须补完整可恢复配置/外部脚本来源，保留校验门禁，核对全writer后新批次备份和隔离恢复，不能只reset-failed或绕过guard。

## 备份修复与发布准备（11:52）

用户明确授权修复并部署。11:32:35持双锁安装worklog配置与外部源码归档修复，20登记服务hash/镜像通过，902容器配置和代际保持；未关闭漂移校验。11:32:52只启动一次online批次20261008T033252Z，Invocation0326a849cecd433e8d35567e31545b07/PID52141。当前仅观察此批，不重复start或安装。数据库/ClickHouse/上传归档已完成，模型归档进行中，不能先称备份成功。

生产相关两表目前各0行，11:48独立dump已在pilot隔离sb_memory_release_restore_20261008_r1恢复，行数保持，加法迁移只在该隔离库验证；FK依赖为stub，不能称整库恢复。候选源码已上传未构建。另准备严格旧MCP容器归档选择规则，7项单测/20服务真实只读配置验证通过，尚未安装。应用未发布、无生产DDL/模型调用。
