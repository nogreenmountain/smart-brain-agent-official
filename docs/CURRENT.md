# 智慧大脑开发与发布状态入口

## 2026-10-10 17:25 AGENTS 模板重新初始化已发布生产并通过公网/终态/归档验收（agents-template-release-20261010-r1）

核对时间：17:09–17:16 实际执行、17:25 文档复核（Asia/Shanghai）。按用户"提交，推送，部署成产"指示及容量处置方案 A 完成发布，[实际发布记录](releases/agents-template-release-20261010-r1.md)。主 API 容器现为 `621935d93b37fe1a6a9245307686ee1e0fd4ca8afc4497b914cf4085e3c46227`（镜像 `smartbrain-agents-template-api:2026.10.10-r1`／`sha256:aa31ae74b5ef…`，仅叠加替换 `project_agents.py` 候选 SHA `6b7d17f0…`），主前端容器现为 `85f21545e254d0d6ee85fd03f4ff3c3bed898f32a118e7227dfe8d7007846006`（镜像 `smartbrain-agents-template-frontend:2026.10.10-r1`／`sha256:743d5093f6c4…`，源码整体重编译，含管理工作台紧凑布局）；两旧容器改名 `-rollback-agents-20261010-r1` 停止断网保留。新功能：已有 AGENTS.md 的项目管理员可预览模板差异并 CAS 重置为最新模板（identical 不写库），旧版本归档可列表/下载；匿名访问四条新路由 401（旧 API 为 404 前后对照）。验收：公网 `/admin` `/wiki` `/login` `/workday` `/health/ready` 200、匿名 Key/records 401、退休下载 410；16 个页面脚本公网与容器逐字节一致，新文案 chunk（9,669 字节 SHA `fe505dc8…`）公网可获；45 个旧静态资产保留可访问；edge 双视图 SHA `c22e68d9…` 不变；AGENTS 函数/指纹/版本数三次核对一致；终态 1030 容器/39 运行/1023 无关容器代际保持；backup inactive/success/登记 20/timer enabled；四盘 docker 40.07GiB／根 31.6GiB／backups 486GiB／cold 253GiB、内存 7.65GiB 达标。容量处置如实记录：删 2 个无引用悬空镜像（释放≈0）；运行中候选容器 310,146,177 字节无轮转日志先归档到 backups 的 log-rotation/（0600，活动写入致源/副本 hash 不一致，如实保留）再截断；`docker builder prune -f` 清 89.2MB 可再生缓存；未删任何证据镜像/容器/卷。归档 `/srv/smartbrain-backups/backups/agents-template-release-20261010-r1/`：api-runtime.tar 192,728,576 字节 SHA `87e8ac4c…`、frontend-runtime.tar 72,407,040 字节 SHA `3915b1f9…`、evidence.private.tar.gz 1,038,650 字节 SHA `549b614d…`（OCI 描述符逐项复核，非冻结备份/恢复验收点）。真实管理员会话的功能闭环（预览→CAS 重置→历史下载）未执行（本轮未授权员工侧操作）；生产实际回退未触发（dry-run 通过）。无迁移、无业务表写入、无模型调用、无 Key/路由变更。本条随文档提交推送后核对远端一致并镜像 E 盘。


## 2026-10-10 16:52 分组提交完成（推送随本条文档提交后核对，部署待 Docker 容量门槛）

核对时间：16:35–16:52（Asia/Shanghai）。按用户"提交，推送，部署成产"指示，本轮工作树改动分三组提交：`d043b76`（10-08/09 已发布九个发布的源码/迁移/deploy/记录同步，含退役 codex adapter 交付物移除）、`e44d2ff`（管理工作台紧凑布局）、`422a157`（AGENTS 模板重新初始化后端四端点＋前端面板）；本条随 releases/README 登记行作第四组文档提交；16:58 已推送 official，`codex/project-memory-no-adapter` 远端 tip 与本地 HEAD 一致（首次推送因邮箱隐私限制被拒，已按基线惯例改用 noreply 署名重写本地四提交后推送成功；最终 SHA 以 git 记录为准），`main` 保持 `431022b` 未动。**部署阻塞**：16:35 生产实时核对 Docker 盘可用 42,886,754,304 字节（39.94 GiB），低于 40 GiB 门槛约 60 MiB，构建还将再耗约 0.2–0.3 GiB；其余门槛全过（/srv/smartbrain 34.2GB、backups 522GB、cold 271.9GB、mem 8.4GB），1025 容器/39 运行、backup inactive/success/登记待构建前复核、无 maintenance.pending、目标容器身份与发布记录预检段一致。可清理空间已测量：build cache 仅 4.47MB；dangling 镜像 2 个共 279MB（09-11/09-14，无容器引用）单独删除仍不过线；13.61GB "reclaimable" 为历史发布/测试证据镜像，按纪律须用户明确授权方可删除（10-08 清理曾单独授权且当时保住全部 185 镜像）。生产 schema 兼容性已于 09:54 只读确认（归档触发器实际存在且启用，新代码沿用 upload_agents 显式归档模式，无迁移）。AST 函数级 diff：project_agents.py 仅新增 6 函数、build_default_agents/wiki_upload_stats 随既有模板版本推进变化、无函数移除。敏感扫描通过（4 处 sk- 命中均为路径误报或合成测试夹具）。构建脚本沿用 conversation-summary-stats-20261008-r1 机制；新路由匿名 401（旧 404）为部署信号。

## 2026-10-10 15:56 已有 AGENTS.md 重新初始化候选已实施并本地验证（未部署生产）

核对时间：15:40–15:56（Asia/Shanghai）。在 09:54 复现与方案基础上按用户确认完成本地候选实施，详见[任务](tasks/2026-10-10-agents-template-reinitialize.md)与[方案](plans/2026-10-10-agents-template-reinitialize.md)。后端新增管理员模板预览 `GET /agents/template-preview`、CAS 确认 `POST /agents/reset-to-template`（模板或文件版本不符 409，内容一致返回 unchanged 不写库）以及成员可读的 `GET /agents/versions` 与归档下载；重置锁当前 files 行（无行时锁 projects 父行），显式 INSERT 归档旧字节，新修订号取 max(当前 version, 历史最大 version)+1，全新文件版本=模板版本4；归档不依赖迁移中无 CREATE TRIGGER 且引用不存在列的函数。前端已有文件时显示"重新初始化为最新模板"（无文件才显示初始化），预览弹窗对比版本/摘要，identical 不提供覆盖键，409 自动重取最新预览，新增版本历史列表与逐版本下载；GET/download/context/项目创建的共用补缺语义未动。验证：后端 pytest 21 passed（venv 见 manifest）、前端全量 40 files／205 passed、tsc exit0、Next build exit0；同时修复管理工作台布局任务遗留的 project-memory 兼容路由测试（创建项目改按需弹窗后旧断言常驻表单），页面源码未动。生产未部署、未提交/推送，发布需单独授权并核对容量门禁；真实 PG 并发/HTTP/完整鉴权验收未执行。证据：`.artifacts/agents-template-reinitialize-20261010/implementation-manifest.json` 及候选 SHA 表。

## 2026-10-10 14:48 管理工作台布局候选最终验证完成（未部署）

核对时间：12:02–12:24验证、14:40读回、14:42–14:48最终审阅修复与复核（Asia/Shanghai）。已按用户选择完成紧凑“左侧项目列表＋右侧详情”：列表卡不再被右侧长内容拉伸留白（桌面左卡676.5px/原1531.5px，列表下34px为计数边框区），创建按需弹窗，概览/成员/AGENTS 分区；补齐筛选、跨分类创建、异步项目切换、删除/迁移/恢复护栏和弹窗键盘焦点。14:42独立审阅发现删除在途+创建成功+目录刷新失败时旧闭包会复活已删项目，已最小修复（函数式更新+快速入口同步移除）并新增交错回归；独立审阅随后capacity中断，未声明完整独立审阅通过，其余由主代理基线diff自审（`final-review.md`）。最终管理页42项、相关组件/API合计6 files 57项、TypeScript exit0、Next生产构建exit0（Build ID `bEv5Zbzl7T8Tu_7JqqN8j`）；构建产物静态浏览器验收14:48 passed：1440/1024/375无横向溢出、无JS错误，搜索/筛选/弹窗/跨分类创建/单项目自然高度/30项目滚动/空分类全项目审批通过。最终候选SHA：page `CDB176B8…`、测试 `A8BBFEF2…`。生产未部署，未提交/推送，既有dirty保留。详见[任务](tasks/2026-10-10-management-workspace-layout.md)与`.artifacts/management-workspace-layout-20261010/`。一次本地生产模式监听启动被自动审批策略拒绝，已用构建产物静态浏览器复核替代。

## 2026-10-10 10:03 管理工作台布局优化进行中

核对时间：10:03（Asia/Shanghai）。用户选择紧凑侧栏＋详情，要求减少项目列表留白、创建按需打开、概览/成员/规则分区。[任务与设计](tasks/2026-10-10-management-workspace-layout.md)。正在以合成本地数据复现与调整；生产未部署，旧dirty修改和权限边界保留。

## 2026-10-10 09:54 已有 AGENTS 初始化问题已复现／方案完成

核对时间：09:47–09:54（Asia/Shanghai）。[任务](tasks/2026-10-10-agents-template-reinitialize.md)／[解决方案](plans/2026-10-10-agents-template-reinitialize.md)：当前实际API源码SHA与隔离复现相同，initialize使用ON CONFLICT DO NOTHING；已有旧模板/自定义文件不更新，UI仍提示已初始化。内存SQL三场景及当前组件点击复现通过，前端原专项7项通过；真实PG并发/HTTP尚未测，backend pytest因本地依赖缺失未启动。方案保留补缺，新增管理员预览＋版本/hash确认的重置，归档完整旧字节、递增revision并分开模板版本，提供历史下载。仅调查与方案交付，未修改业务源码/生产文件或发布。


## 2026-10-10 09:27 模拟项目与模拟用户已停用/封存

核对时间：09:12–09:27（Asia/Shanghai）。本次仅处理证据明确的8个模拟/灰度账号和11个验收/灰度测试项目：账号已停用并封禁，认证/Redis会话为0，2把活动个人网关测试Key已撤销，11个项目标记完成；12条测试项目成员关系、10条测试组织成员关系解除。账单、用量事件、对话、审计与正文保留，未删除项目或账号行。非目标真实用户/项目/Key/成员关系前后指纹一致，公网入口读回200/401边界通过，无模型请求。详见[任务记录](tasks/2026-10-10-synthetic-fixture-cleanup.md)和`.artifacts/synthetic-fixture-cleanup-20261010/`。账号和项目为停用/封存，管理员历史列表仍可能显示；永久删除尚未执行。

## 2026-10-10 08:49 夜间运维已到期收尾

核对时间：08:30–08:46（Asia/Shanghai）。[早间报告](ops/overnight-operations-20261009.md)／[任务与证据](tasks/2026-10-09-overnight-operations.md)：业务处置授权08:30结束；原collector r2自然deadline退出，184条once/r1/r2样本（r2 181轮）至08:29:48.884，无>450秒缺口/采集错误/新host OOM，末11.116秒未有下一条主机/入口样本。旧PID872681及确切watch进程不存在，临时unit已回收，未重建。心跳10-10-08-30已PAUSED、原UTF-8 name/prompt恢复并读回。

自然personal_api只读完成区间17:17:44–08:30（包含首轮回溯5分钟）为172×200、1×499、9×502；8条502逐秒与Windows capacity/server_is_overloaded对应，1条约902秒为request_timeout/stream_incomplete，失败/取消不标完成且用量未知。其他上游事件来源/限额仍未核对，无主动模型批次或重试变更。

本晚生产处置为17:49一次精确CH短停/启动（pool2/ratio1）及18:50目标metric_log 64KiB缓冲/原XML重载，无第二次CH重启。7705未清零、最后18:49:57，属于仍活动的17:49启动世代；包括首两窗口的163个完整发布后窗口无新增Code241。原CID/image/PID930830/XML e14fd07b/metric UUID保持，08:31完整1025容器/23业务对象元数据/8公网/个人current/edge/backup20复核通过。本次运维未执行业务数据写入，生产DDL仅目标表设置。

原定时online备份Invocation4250cdc6于03:58:46 success/exit0，36项程序自检及31小文件独立SHA一致；5大payload独立hash/根身份、完整PG/全writer冻结恢复和真实30人容量未验。备份期间CH max3492→9939及换页/IO压力如实保留，Docker仅高于40GiB约36.16MiB；无历史清理/迁移/后继永久任务。报告/任务/CURRENT已镜像E盘，旧dirty源码保持，本轮未提交/push；后续需新授权与实时门禁。以下保留历史阶段记录，不扩展到期授权。

## 2026-10-10 04:00 原定时online备份自然完成（整夜运维继续）

核对时间：04:02–04:10（Asia/Shanghai）。原备份 Invocation `4250cdc681a24199aa79d1da71002515` 于03:58:46自然success/exit0，现PID/Job空；final `20261009T185810Z` 的backup-state complete/online、36项原Invocation SHA自检OK与完成标记1，独立小文件31项SHA一致。5个大payload未另做独立重hash，完整PG/全writer冻结恢复仍未验收。无第二批、restore或生产处置。04:03重新完整复核1025容器配置代际、23业务对象、原metric UUID/XML、8公网/个人/edge/backup20通过。

130采样截至03:59:48无缺口/采集错误/新OOM；CH Code241仍7705/最后10-09 18:49:57、max9939自03:04不增。03:30–04:00换入940页/换出0，不覆盖此前新增换页；CH约3.54GiB且有IO压力，原因未确认。Docker仅约79.5MiB高于40GiB储备，继续暂停build/部署/大归档、不清历史；原collector/heartbeat继续至08:30硬截止。详见[任务与证据](tasks/2026-10-09-overnight-operations.md)。

## 2026-10-10 03:00 原定时备份活动中 CH 压力观察（整夜运维继续）

核对时间：03:00–03:07（Asia/Shanghai）。原 timer 自然启动备份 Invocation `4250cdc681a24199aa79d1da71002515` / PID `2471121` / Job `9292938`，当前仍 `activating/start`，partial ClickHouse 归档已由约 0.34 GiB 增至 7.20 GiB；ExitTimestamp 为空，不能称备份成功。备份活动时间内 CH cgroup `max` 由 3492 增至 9939、memory.current 约 2.15→3.59 GiB，memory.peak 约 4 GiB（生命周期峰值，本批新增未证），OOM/oom_kill=0、Code241累计7705未增；file/inactive_file占多数并伴随IO压力，支持缓存/归档读取压力时间相关但未确认唯一根因。不得停止备份、drop cache、改 CH、重启或清理空间；延后完整维护/锁核验，继续只读跟踪同批终态。

## 2026-10-10 03:30 备份持续与新增换页观察（整夜运维继续）

核对时间：03:30–03:32（Asia/Shanghai）。同一原备份 Invocation `4250cdc681a24199aa79d1da71002515` / PID `2471121` / Job `9292938` 仍 activating/start，partial 已进入 models 归档，`clickhouse.tar.gz=9078287763`、`models.tar.gz=3785097216` bytes，未终态。03:00–03:30 主机 SwapFree 减少 `285614080` bytes（约272MiB），pswpin +16704/pswpout +81674、OOM=0；当前运行容器 cgroup swap 快照合计约 +284839936 bytes（CH +97144832），归因覆盖不完整。03:32短后继swap-out增0/再换入49页，不能据此称整段压力消失。CH max=9939自03:04保持、OOM/oom_kill=0、Code241=7705未增；memory.current约3.50GiB，file/inactive_file占多数并伴随IO压力，原因未确认。继续只读跟踪，不停止备份、不drop cache、不改CH、不重启；完整复核待备份终态。

## 2026-10-09 18:51 ClickHouse宽表输出缓冲修复已发布（整夜观察继续）

核对时间：18:50执行/18:51独立复核。[诊断与自审](plans/2026-10-09-clickhouse-wide-buffer.md)／[窄发布r2](releases/overnight-clickhouse-buffer-20261009-r2.md)：实际1136列metric_log Horizontal输出创建全部列缓冲触发Code241，同版本r3复现/单改64KiB通过、r4两路合并0 Code241及真实系统表配置/重启/测试回退保持UUID。生产仅表级max_compress_block_size65536、backup-disk.xml原inode同步重载，SHAe14fd07b；pool2/ratio1保持，**本次没有重启生产容器**，CH仍17:49启动/PID930830。

全部1025容器完整配置及代际、23业务对象UUID/结构hash/元数据行数、8公网/个人current预算/edge/backup20通过；metric UUID保持，无历史表更名。Code2417705/最后18:49:57，18:51未增，metric parts约323→38且合并推进；两个完整后继窗口和整夜仍待。Docker40.19GiB/cold252.22GiB储备薄，继续实时门禁。r3/r4/发布均终态不重放，原observer95565b7d和有限heartbeat继续；无真实模型主动调用/删除历史/生产回退，完整PG/冻结恢复/30人真实容量仍未验。

19:01后继：首个完整18:54–18:59窗口Code241=0，累计仍7705/最后18:49:57；metric parts21。22样本无缺口/采集错误/host OOM，cold253.31GiB/Docker40.18GiB，储备仍薄；cgroup max事件有所增加、时间未定位，不称资源压力全部解决。第二个完整后继窗口和整夜继续核对。修复778349b与收尾122cd8f已推official/远端一致，23部署测试/sources通过，main保持。

19:05：两个完整后继5分钟窗口均0 Code241，累计仍7705/最后18:49:57；metric parts21/无当前merge，cgroup max自19:01保持3492、5秒节流0/50及0 OOM。23采样无缺口/采集错误；再度核对1025容器配置代际、23业务对象和原metric UUID/新XML、8公网/个人/edge/backup20通过。两窗口效果门槛通过，长期和真实多人容量仍未验；Docker40.18GiB/cold253.31GiB仍需观察，夜间授权/原collector/备份计划保持。

20:00后继：19:29–19:59新增25个自然gpt-6-sol请求200/完成标记及用量标记已保存，最长140秒；1个502与19:45:18 Windows上游server_is_overloaded/capacity逐秒及耗时对应，未知用量/不完整保持。无新网关超时/连接/落库错误，CH仍7705/最后18:49:57、cgroup max3492未增。34样本无缺口/新OOM/采集错误，容器/业务元数据/公网/个人/edge/备份身份保持；Docker40.16GiB/cold253.46GiB仍薄。此次是自然流量聚合核对，不是主动模型批次或30人容量验收；夜间巡检继续。

22:31–22:34后继：Windows9000上游/v1/messages新增1个capacity及5个HTTP429/rate_limit_error，其中2个429在最新22:29采样截止后；完整六窗口personal_api无新增完成或失败，调用来源/具体限额类型未核对，后继覆盖待观察，不自动调整重试/模型/OAuth。64样本无缺口/采集错误/新OOM，CH仍7705/最后18:49:57及max3492，容器/公网/个人/edge/backup身份保持。Docker40.13GiB/cold253.41GiB仍薄；仅文档更新，原02:58备份与08:30期限保持。

23:01后继：22:29:48–22:59:48新增29×gpt-6-sol 200及2×502，另22:59:50尾段1×502，三次均与Windows同秒/v1/responses capacity/server_is_overloaded对应；本轮personal_api无连接/落库/120秒截断错误。v1/messages 429/rate_limit事件已进入采样覆盖，但调用来源与具体限额类型仍未核对。70样本无缺口/采集错误/新OOM，CH累计7705/最后18:49:57、max3492不变；Docker约40.13GiB/cold253.37GiB仍薄，原备份与08:30期限保持。

## 2026-10-09 17:57夜间ClickHouse限并行已发布（内存问题仍待）

核对时间：2026-10-09 17:51/17:57（Asia/Shanghai）。[实际发布](releases/overnight-clickhouse-20261009-r1.md)／[具体自审](plans/2026-10-09-overnight-clickhouse.md)：CH原CIDf0a0f6eb/imagecd450891仅配置改pool2/ratio1及三个阈值1，SHAecf3efd2；原单文件bind inode保持，17:49:40Z精确CH短停启动一次。双锁/备份20登记/四盘门槛通过，隔离同版本20000行及restart读回通过；1022无关完整容器配置代际保持、39运行、4原业务表元数据行数/8公网入口/个人/edge通过，无DDL或主动模型。

17:57后台任务2、CPU节流1/50周期（原50/50）、text_log parts88→25持续推进，**Code241仍有新增**，单次合并内存峰值待后续实验，不能称完全修好。原observer95565b7d继续，无需重建；baseline里的CH启动告警对应本次受控变更，新StartedAt2026-10-09T09:49:40.337495161Z/PID930830。旧test/发布均终态不重跑；回退尚未实际执行。23部署工具/source检查通过，official新交付分支准备中。

18:01后继核对：两个5分钟窗口Code241仍新增，保持局部限并行效果；cold238.75–242.18GiB低于250GiB储备，新合并结果/inactive parts可见，差额来源尚未完全核对。暂停进一步生产变更/大型测试和归档，观察正常parts回收，不prune/删历史。原采样与heartbeat继续、10样本无缺口/新OOM/收集错误，个人网关0排队/DB0/无超时及落库失败。official分支codex/overnight-operations-20261009提交8430aa6已push/远端核对，main431022b不变；全夜尚未完成。

## 2026-10-09 17:30夜间运维已开始（进行中）

核对时间：2026-10-09 17:22–17:30（Asia/Shanghai）。[方案/自审](plans/2026-10-09-overnight-operations.md)／[任务](tasks/2026-10-09-overnight-operations.md)：用户本轮授权自行审核开始，截止10-10 08:30。服务器只读observer每5分钟，当前r2 Invocation95565b7d…/PID872681、active/running、11项Linux边界通过；同对话heartbeat `10-10-08-30` ACTIVE每30分钟，截止同上。只观察原runner，禁止重放本次install/start/update/resume或旧发布/模型/备份批次。

个人70583b47/image6c9a5779、8/24/DB3、39运行、edge双视图、公网200/匿名401保持；1执行/0排队/DB0、无锁等待/新OOM。Docker首轮39.97GiB低于40GiB发布储备，暂停新build/业务部署/大归档，跟踪趋势；CH内部日志仍实时Code241，r2已补真实错误文件采样，未修改CH业务配置。备份timer次日02:58:03，现inactive/success，仅观察原正常批次。无业务服务重启、生产DB写入/主动模型调用或历史清理。整夜尚未完成，08:30后总结/停续跑；Codex诊断依赖本机应用联网运行，远端采样可独立执行。

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
