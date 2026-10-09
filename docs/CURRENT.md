# 智慧大脑开发与发布状态入口

## 2026-10-09 17:57夜间ClickHouse限并行已发布（内存问题仍待）

核对时间：2026-10-09 17:51/17:57（Asia/Shanghai）。[实际发布](releases/overnight-clickhouse-20261009-r1.md)／[具体自审](plans/2026-10-09-overnight-clickhouse.md)：CH原CIDf0a0f6eb/imagecd450891仅配置改pool2/ratio1及三个阈值1，SHAecf3efd2；原单文件bind inode保持，17:49:40Z精确CH短停启动一次。双锁/备份20登记/四盘门槛通过，隔离同版本20000行及restart读回通过；1022无关完整容器配置代际保持、39运行、4原业务表元数据行数/8公网入口/个人/edge通过，无DDL或主动模型。

17:57后台任务2、CPU节流1/50周期（原50/50）、text_log parts88→25持续推进，**Code241仍有新增**，单次合并内存峰值待后续实验，不能称完全修好。原observer95565b7d继续，无需重建；baseline里的CH启动告警对应本次受控变更，新StartedAt2026-10-09T09:49:40.337495161Z/PID930830。旧test/发布均终态不重跑；回退尚未实际执行。23部署工具/source检查通过，official新交付分支准备中。

## 2026-10-09 16:56个人API截断修复上线，上游过载仍存在

核对时间：2026-10-09 16:44（Asia/Shanghai）。[任务](tasks/2026-10-09-personal-api-disconnect.md)／[实际发布](releases/personal-api-streaming-20261009-r2.md)：17次502全部120秒，原代理缓冲SSE+总截止机制复现，16:39流式r2上线70583b47/image6c9a5779。120秒idle/1800秒max、8/24/DB3与短事务保持，失败正文不标完成。实际镜像41项HTTP/独立PG及130.12秒合成流通过、首包55ms；16:40公网/实际源码/生产SQL只读验收，1018其他容器配置代际保持/39运行；16:44自然26用户请求均200。新镜像与私有证据归档完成，独立SHA/OCI及官方分支待收尾。失败记录和旧服务保留；不重放旧发布/模型批次。Docker仅约0.29GiB门槛余量，完整容量未放行。

后继核对16:50：新归档SHA/OCI及current21镜像全部通过，真实GPT请求627576ms成功200/完整/实报usage，当前2执行/0等待/DB0；其他1018容器配置代际/edge双视图保持。16:56剩余failed/503实际与Windows上游capacity/server_is_overloaded逐时刻对应，没有新个人代理超时；不能称所有API error消除。未改上游授权、重试或模型选择。官方新修复分支待push收尾，所有本轮runner已终态。

17:00仓库核对：[codex/personal-api-streaming-20261009](https://github.com/nogreenmountain/smart-brain-agent-official/tree/codex/personal-api-streaming-20261009)修复提交b105937f60df956b32fc040ebe23974633c64f77已push，official远端SHA一致、main431022b不变；22项部署工具及源码清单、Compose静态通过。误推旧origin的临时同名分支已清理，正式副本保持。最终记录随后追加，所有现场/测试/构建/发布/归档runner终态，旧与失败/测试容器保留，不重跑。

## 2026-10-09 14:24正式仓库分支交付

核对时间：2026-10-09 14:24（Asia/Shanghai）。[源码分支](https://github.com/nogreenmountain/smart-brain-agent-official/tree/codex/current-source-20261009)363715c、[部署分支](https://github.com/nogreenmountain/smart-brain-agent-official/tree/codex/reproducible-deployment-20261009)f170d97已push并远端SHA核对，main431022b不变。入口[AI-DEPLOY](deployment/AI-DEPLOY.md)，[交付任务](tasks/2026-10-09-reproducible-repository.md)和[验收](releases/reproducible-repository-20261009.md)已镜像保存；源码继续在独立worktree及Github分支，不覆盖此工作树。

受控21镜像/私有配置包已准备，完整业务数据恢复与新机冷启动尚未验收。原业务服务重启0，6测试容器停止，39运行。所有本轮runner已终态，不重放归档、迁移或发布。


入口更新时间：2026-10-09 12:17（Asia/Shanghai）。连接生命周期与并发排队r2已生产验收及归档独立复核完成；r1实际恢复历史保留。用户手测闭环与11:20容量核查为历史；规则10:43网页更新、10:44实际摘要读回、10:49只读收尾及七历史调用10:25读回保持。维护人：当前集成负责人；本次由 Codex 整理。

这里集中链接任务、发布和证据。每条状态必须附核对时间；文档更新时间不能代替生产核对时间。

## 先读这些

1. [项目规则](../AGENTS.md)：授权、禁用功能及历史边界。
2. [记录维护流程](development/README.md)：开始、交接、发布时的更新顺序。
3. 下方对应任务的接续记录，再按记录读取相关源码和证据。

## 连接占用与并发排队（2026-10-09 12:17）

- [任务](tasks/2026-10-09-personal-proxy-concurrency.md)／[r2发布](releases/personal-proxy-concurrency-20261009-r2.md)：现个人代理CIDacbab2fc…/image08f24c57…，同一current unit active/enabled绑定，supplemental writer inventory已更新。短事务在线程中完整创建/使用/关闭Session；模型及排队等待不持连接，池仍1+3/DB并发3。单进程8执行/24等待/60秒、503可重试、16MiB请求上限、共享客户端8连接，取消/撤销/超时释放。
- 真实HTTP+独立PG及实际镜像34项通过，5/10/20/30并发全部完成、等待期间checkedout0/idle-in-transaction0；67成功独立记录正确归属/夹具Token和消息保存，499断连/502超时保留未知用量。r1极快响应observer收尾Red已修正，12:10实际回退通过；r2生产只读账号/项目SQL、8公网入口及源码hash通过，0生产写入/真实模型。
- 12:17 999容器/39运行、996无关基线配置代际/edge双视图保持；backup inactive/success/PID0/Job空/登记20、无pending，四盘原门槛通过但Docker仅约0.34GiB门槛余量。旧/失败/测试容器停止保留；镜像59e007ef…及私有证据8bbd19ce…归档/独立SHA/0600/旧新OCI配置层通过，本轮runner全终态。队列非持久且按进程预算；生产完整聚合/真实员工峰值、保存失败补偿、CH/完整冻结恢复/G1仍待，不称全平台最终容量通过。

## 10–30人同时使用的容量核查（2026-10-09 11:20，历史）

后继[连接生命周期与并发排队](tasks/2026-10-09-personal-proxy-concurrency.md)12:14已生产验收；具体方案和验收见[实施计划](plans/2026-10-09-personal-proxy-concurrency.md)。以下保留修复前的容量核查历史。

- [任务](tasks/2026-10-09-hardware-capacity.md)／[报告](ops/hardware-capacity-20261009.md)：用户手测闭环与本人新增1条智慧脑published元数据一致；多人稳定性未验收。16GB/6核12线程，内存约6.60GiB可用；Swap近满但短采样无新换页/OOM，整机CPU约30–31%。
- 活动个人代理单进程、数据库池1+3/30秒，等待120秒模型时仍占连接；同一活动源码+内存SQLite假模型夹具4并发全200，第5出现1个500。夹具缩短等待至0.25秒，只证明机制，不宣布线上最多4人。PG当前其他client14，池改造优先于单纯扩内存。
- CH仍Code241、内部3.6GiB/容器4GiB；2核配额8秒80/80周期节流，与PG共机械盘。Docker可用约40.8GiB、数据约251.8GiB、备份约522.6GiB，前两仅略高于40/250运维储备。建议先短事务/并发预算、CH后台压力及保存失败补偿，再规划32GB/独立NVMe数据盘；没有执行调整、清理或扩容。
- 11:20关键容器启动代际保持，runner全终态；真实模型/生产DB写入0。安全证据两端保留，新脚本不重放；不替代原完整PG/整机恢复和四模型验收。

## 自定义AGENTS初始化后的归错项目（2026-10-09 11:20用户手测接续）

- [任务](tasks/2026-10-09-agents-reinitialize-project-mismatch.md)／[规则更新](releases/smartbrain-handoff-rules-20261009-r1.md)：10:26本人摘要和三调用实际在科研；10:47用户确认原CLI会话继续，仍沿用启动时科研上下文。网页/文件更新不替换旧会话；本轮用户报告另一台手测闭环，11:20本人新增智慧脑published元数据一致，当前个人代理新版保持。
- 用户完整自定义规则和智慧脑服务器v1规范字节相同，但没有项目注释，只要求propose_memory交接页；initialize实际DO NOTHING不会重置已有文件。仅为智慧脑保留全部原文，新增项目标记/显式工具UUID和短对话入口，10:43现有认证upload保存v2 SHA dcc0fd43…/20116字节，download及再initialize保留通过；原v1原字节备份保留，其他项目/服务/Key/Token保持。
- 完整规则真实CLI首请求+当前部署helper识别通过，0真实模型。10:44《AGENTS项目归属核查与修复》实际通过Company Memory保存发布在智慧脑，Wiki8b457085…/v1、上传者唐伟翔，正文及近期更新读回一致。
- [新交付](deliverables/smartbrain-wiki-handoff-rules/README.md)保留原九部分交接；另一台需重新下载并新开CLI，override/实际目录待核对。10:49智慧脑v2/hash、原v1备份及已发布摘要只读复核通过；交付和本轮文档已镜像E盘。旧10:26科研记录和三个账单未移动或重发；本轮runner终态，不重跑规则/MCP写入，不代表整个平台闭环。

## 无适配器个人请求归属（2026-10-09 10:25，10:29收尾）

- [任务](tasks/2026-10-09-request-project-attribution.md)／[发布](releases/request-project-attribution-20261009-r1.md)：用户确认的七条历史调用已归智慧大脑agent，实际认证公网records返回正确项目，7账单hash和124584存储Token保持，1用量未知保留；不重跑历史写回。
- 当前个人代理CIDb3caf14b…/image8e25962f…，仅三源文件；每次显式头或Codex正式AGENTS的UUID经成员验证归属，缺失不猜。个人Key不绑项目、无适配器；个人API不触发全量Wiki，只由Company Memory提交短摘要。
- 新current personal unit active/enabled且精确绑定，旧gray unit保持。实际镜像23项、隔离PG18项、真实Codex封装及生产成员SQL只读/8公网入口通过；972无关容器配置代际保持，975/39运行。原Env/HostConfig/26成员/3IP、edge双视图保持；backup登记20/inactive/success，reconcile disabled/无gate/无pending，四盘门槛10:24通过。切换r1失败后10:23实际恢复，r2发布成功，失败证据保留。
- 原Compose备份20范围保持，当前个人代理新增精确writer补充清单但未进入完整冻结协调器。10:26两镜像/私有证据归档完成，10:29两SHA/OCI配置层/当前unit与入口/四盘门槛独立通过；所有runner终态，不重跑归档或发布，不称完整备份恢复通过。另一台电脑仍需[替换正确UUID规则](deliverables/smartbrain-conversation-rules/README.md)，没有上下文的审核不保证归属；原科研Wiki记录未移动。

## 全面验收及最新用户病例（2026-10-09 09:43，历史）

- [全面验收报告](ops/full-system-acceptance-20261008.md)／[修复发布](releases/full-system-acceptance-fixes-20261008-r1.md)／[任务](tasks/2026-10-08-full-system-acceptance.md)：本轮测试和清理已结束，三处业务缺陷已发布。前端181项；后端初始67文件中61通过/6失败，后继环境及实际镜像专项补验，过时会议.doc拒绝测试仍失败。业务22/资料18生产复验通过；不称全系统全绿。
- 09:31 API e6a1a794…/image8eac1584…、MCP a2db22b0…/image74415450…运行；963容器/39运行，933基线中931无关容器配置/代际保持，edge宿主/活动c22e68d972ae保持。3合成用户禁用、4Token撤销、7会话关闭、3合成项目completed，测试/恢复容器运行0；不重放fixture/发布/审批创建/backup/restore/cleanup。
- online36 SHA与Redis隔离恢复通过；PG完整恢复未通过，7关键表仅行数通过；全writer冻结/整机/四模型G1及真实员工Key未验。ClickHouse仍Code241，09:31Docker42680668160字节<40GiB，新发布须先重新满足容量门槛；真实tunnel unit failed、Docker隧道正常。
- [09:17对话归属与七次调用](tasks/2026-10-09-conversation-receipt-work-records.md)：另一台电脑AGENTS的UUID指科研项目、正文写智慧脑，原记录已在科研项目published；六次Terra和一次自动审核是七个不同底层请求，未伪造任务合并。客户端自报GPT-5不是实报模型。
- 正确智慧脑UUID dfaefd9a-8e5e-4775-bc18-e3d551c651e4；[修正版AGENTS](deliverables/smartbrain-conversation-rules/AGENTS.md)／[替换说明](deliverables/smartbrain-conversation-rules/README.md)已交付。本机无法直接替换另一台电脑；客户端复验未完成，原真实记录/Token/Key不改。09:38智慧脑服务器旧AGENTS v1没有UUID注释，现有文件不会因插件升级自动更新。

## 对话上传统计与简短提交（2026-10-08 20:13，历史发布）

- [任务](tasks/2026-10-08-conversation-summary-stats.md)／[发布](releases/conversation-summary-stats-20261008-r1.md)：PROJECT PROFILE按已保存对话计数；短请求/最终结果、已识别内部封装及超长拒绝。API/MCP/前端上线，新项目默认AGENTS v4，既有文件和历史正文保持。
- MCP1.4.1、Company Memory0.2.1+codex.20261008，本机已升级且原Token保持。Wiki已有独立更新入口，刷新网页；新建Codex聊天加载新版技能。
- 63后端（真实PG14项）/51前端/tsc、实际MCP库及生产认证工具发现、公网11管理页脚本/下载包/35旧资源、部署前端加合成API浏览器通过。r1失败恢复保留，r2成功；本轮无员工正文提交或模型调用。
- 20:10最终933容器/39运行，920原无关容器配置/代际保持，edge宿主/活动c22e68d972ae、ro；backup success/timer enabled/登记20服务。候选停止/no，临时代理与隧道关闭，四监听归零。20:13四归档SHA及运行入口复核通过，Docker43894509568字节≥40GiB。全部runner终态，禁止重放发布/函数安装/升级/归档；归档不是冻结备份/恢复合格点。

## Company Memory更新入口（2026-10-08 18:21，历史）

- [任务](tasks/2026-10-08-company-memory-updater.md)／[发布](releases/company-memory-updater-20261008-r1.md)：独立“更新 Company Memory”入口与保留Token更新器已发布；本机实际启用0.2.0，新聊天加载新版技能。
- 18:18完整现场：主前端7366d9d631ac/image5721eff53b7d，edge宿主/活动c22e68d972ae；923容器/39运行，920其他既有容器配置/代际保持。候选停止/no、QA代理关闭、原退休410保持，backup success/timer enabled/登记20服务。
- 18:21三归档SHA、OCI身份与公网入口独立核对通过，Docker43001249792字节≥40GiB。17项专项/tsc、真实CLI升级与失败恢复、部署前端+合成API浏览器及严格TLS资源通过。没有DDL/生产Token/模型/备份重跑；所有runner终态，不重放发布。权威源码在原C盘工作树，E盘源码不覆盖。

## 本次已核对的范围

- 17:02接续发布：921容器/39运行；本任务主API/主前端/实际read新版本生效，/workday精确入口接修复前端；911其余既有容器配置/代际保持、4候选停止/no、临时会话与代理关闭。41前端/8后端、两角色浏览器、严格TLS资源/权限通过；backup success/登记20，Docker约40.49GiB。详见[发布记录](releases/ai-workspace-records-scroll-20261008-r1.md)。无DDL/Key/模型/备份重跑，不代表原17项完成。
- 17:09:56该发布镜像/私有证据归档完成；17:16哈希及OCI身份独立核对通过，三个运行版本、read unit、edge双视图、backup终态和公网200/匿名401保持。详见同一发布记录及archive-closeout-verification.json；归档不含生产数据库，不是冻结备份/恢复合格点，不重写原tar。

- 原开发工作区基线：`main` / `8280adda3846`。本次归档其后端、前端、迁移、部署候选和文档；[本地开发快照](ops/local-workspace-state-20261008.md)列出范围和验证限制。
- 指定正式仓库与原仓库历史独立；本次基于正式仓库 `5a94286b993b` 整理提交，保留原开发工作区和原仓库历史。
- 13:00生产908个容器/38运行。本任务API/MCP/主前端已切换为2026.10.08-r1，MCP服务1.4.0；899个无关容器配置/代际及原141个AGENTS文件保持。见[实际发布记录](releases/project-memory-no-adapter-20261008-r1.md)。[09:30生产快照](ops/server-state-20261008.md)和[原版本基线](releases/server-baseline-20261008.md)保留为历史。
- 公网页面/ready200、匿名个人Key/模型401；真实合成成员记录/重试/权限/统计及浏览器AGENTS上传下载通过，旧适配器模块/检测/下载退出。验收会话与Token已关闭，真实模型请求0；不代表所有旧业务重新完整验收。
- 本地源码与若干活动服务的源码 hash 不一致，不能将本次 Git 同步称为部署或宣称全链路通过。

## 任务索引

开发阶段与部署范围分别记录。历史线索不自动成为已接管的活动任务。

| 任务 | 负责人 | 开发阶段 | 部署范围 | 最近核对 | 下一步和交接 |
|---|---|---|---|---|---|
| 连接占用与并发排队 | Codex，本任务 | 已结束、生产及归档独立复核通过 | 个人代理r2三源/current unit/既有writer补充清单 | 2026-10-09 12:17 | [任务](tasks/2026-10-09-personal-proxy-concurrency.md)／[发布](releases/personal-proxy-concurrency-20261009-r2.md)；34项实际镜像+真实HTTP/PG通过，r1实际恢复保留，不重放发布 |
| 10–30人多人容量 | Codex，本任务 | 本轮只读/隔离边界核查已结束；多人容量未验收 | 无生产修复/扩容；活动源码假上游+内存SQLite边界复现 | 2026-10-09 11:20 | [任务](tasks/2026-10-09-hardware-capacity.md)／[报告](ops/hardware-capacity-20261009.md)；先连接生命周期/CH/失败补偿，再硬件与阶梯压测 |
| 自定义AGENTS与初始化归错项目 | Codex，本任务 | 服务器规则/实际写入已验证；用户客户端手测通过 | 智慧脑AGENTS v2和1条短摘要；无代码/服务部署 | 2026-10-09 11:20（新增本人元数据）/本轮用户确认 | [任务](tasks/2026-10-09-agents-reinitialize-project-mismatch.md)／[更新](releases/smartbrain-handoff-rules-20261009-r1.md)；不迁移旧记录，多人容量见上行 |
| 无适配器个人请求项目归属 | Codex，本任务 | 已结束、已验证 | 七历史已修正；当前个人代理三文件生产发布 | 2026-10-09 10:29（现场）/10:25（认证读回） | [任务](tasks/2026-10-09-request-project-attribution.md)／[发布](releases/request-project-attribution-20261009-r1.md)；runner全终态不重放，另一台电脑需正确AGENTS |
| 对话项目归属/七次请求诊断 | Codex，本任务 | 原因已验证，本地规则已交付，历史诊断保留 | 后继七调用修正与代理发布见上行，原科研Wiki保持 | 2026-10-09 10:25（后继）/09:38（旧） | [病例](tasks/2026-10-09-conversation-receipt-work-records.md)；另一台电脑待替换复验 |
| 智慧大脑全面测试验收 | Codex，本任务 | 本轮测试已结束，全系统未通过 | 三处业务修复生产已发布；隔离恢复限定通过 | 2026-10-09 09:31/09:36 | [任务](tasks/2026-10-08-full-system-acceptance.md)／[报告](ops/full-system-acceptance-20261008.md)／[发布](releases/full-system-acceptance-fixes-20261008-r1.md)；CH容量/完整PG恢复/生命周期/G1仍待，不重放历史runner |
| 对话上传统计与简短提交 | Codex，本任务 | 已结束、已验收 | 生产API/MCP/主前端/默认函数v4；本机插件0.2.1 | 2026-10-08 20:13 | [任务](tasks/2026-10-08-conversation-summary-stats.md)／[发布](releases/conversation-summary-stats-20261008-r1.md)；新聊天加载，既有AGENTS保持，不重放runner |
| Company Memory独立更新入口 | Codex，本任务 | 已结束、已验收 | 生产主前端与精确PS1路由；本机0.2.0升级 | 2026-10-08 18:21 | [任务](tasks/2026-10-08-company-memory-updater.md)／[发布](releases/company-memory-updater-20261008-r1.md)；原Token保持，新建Codex聊天加载；不重放发布或升级 |
| 开发状态记录机制 | Codex，本轮 | 文档结构建立并检查 | 本地文档 | 2026-10-08 | [本轮接续记录](tasks/2026-10-08-development-records.md)；下次真实任务使用模板 |
| AGENTS.md + company-memory，退出适配器 | Codex，本任务 | 验证和收尾完成 | 生产API/MCP/主前端/插件包/加法迁移已发布；备份修复成功 | 2026-10-08 13:00 | [接续记录](tasks/2026-10-08-project-memory-no-adapter.md)及[发布记录](releases/project-memory-no-adapter-20261008-r1.md)；客户端升级/重新连接，已有项目负责人确认提交规则；新项目默认内容约639字节/8行，既有项目不覆盖；不重跑发布runner |
| 服务器与工作区 Git 同步 | Codex，本轮 | 源码和状态快照整理，限定验证 | Git 快照；生产只读 | 2026-10-08 09:30 | [接续记录](tasks/2026-10-08-state-sync.md) |
| AI 工作台记录与管理工作台滚动修复 | Codex，接续 | 已验证 | 生产主API/主前端/实际read及精确workday入口 | 2026-10-08 17:02 | [接续记录](tasks/2026-10-08-ai-workspace-records-scroll.md)及[发布记录](releases/ai-workspace-records-scroll-20261008-r1.md)；滚轮/正文/两角色/权限通过，r1实际回退后r2成功；不重跑发布或fixture |

## 当前待处理事项

| 事项 | 实测状态 | 接续边界 |
|---|---|---|
| 备份/恢复 | 10-09 09:31backup success/inactive、timer enabled，登记20；online36 SHA、Redis恢复通过，PG完整恢复失败，7关键表仅行数通过 | [全面报告](ops/full-system-acceptance-20261008.md)：不是全部writer冻结恢复，保留原完整门禁，不重跑原恢复r3 |
| ClickHouse与部署磁盘门槛 | 11:14仍Code241/后台merge，11:20Docker43813408768字节>40GiB、数据270358450176字节>250GiB，分别仅约0.8/1.8GiB门槛余量 | [容量报告](ops/hardware-capacity-20261009.md)：CH/PG共享机械盘、连接生命周期和保留策略待实施；不重复prune/搬日志，不把当前过门槛称容量充足 |
| systemd 与活动容器绑定 | 12:14 personal-gateway-current active/enabled绑定acbab2fc r2；原gray unit保持，仍绑定旧灰度容器。tunnel最后09:33failed/Docker正常，本轮未重测其unit | 以actual unit清单为准，不把gray active当公网代理受管理证据；完整生命周期/整机恢复未通过 |
| Key 状态机 worker | reconcile timer disabled，feature gate 文件不存在 | 不自动启用，不宣称管理闭环正式可用 |
| 代码和环境一致性 | E 盘、D 盘部分模块及线上镜像源码不同 | 按具体任务选择权威源码；本轮不互相覆盖 |

这些事项是待核实或待修复线索，本次同步不自动启动修复任务。

## 生产与待接续事项的历史线索

| 范围 | 最后引用的核对日期 | 历史记录 | 接续前需要确认 |
|---|---|---|---|
| 工作记录、页面滚动、网关情况 | 2026-09-22 13:45 | [版本状态快照](ops/current-version-status-20260922.md) | 当前入口版本、第二轮补丁是否发布、问题是否仍存在 |
| 个人单 Key 发布与回退 | 2026-09-20 | [发布记录](ops/personal-one-api-key-release-20260920.md) | 现有镜像、容器、绑定和数据兼容性；旧记录不是今天可执行的回退指令 |
| 隔离网关接续 | 2026-09-18 | [历史交接](plans/2026-09-18-phase6-g1-isolated-gateway-repair-approved-handoff.md) | 其中临时授权已到期，不能从旧交接推导新的执行授权 |

## 发布索引

[发布记录目录](releases/README.md)。本任务已完成[项目记录/退出适配器实际发布](releases/project-memory-no-adapter-20261008-r1.md)，回退dry-run通过，未实际回退；原只读版本基线仍是历史证据。

## 更新约定

- 任务开始：创建接续记录，在任务索引登记负责人和范围。
- 阶段完成或中断：先更新任务记录及证据，再更新本页摘要。
- 发布或回退：先写对应发布记录和实际结果，再更新任务和本页的部署范围。
- 当前入口由集成负责人维护；各任务负责人维护自己的记录，避免并行覆盖。
- 冲突按目标范围、核对时间和原始证据判断，保留被替代的历史记录。
