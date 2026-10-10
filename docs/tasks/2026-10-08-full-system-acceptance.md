# 智慧大脑全面测试验收接续

- 任务full-system-acceptance-20261008，负责人Codex；用户本对话明确要求全面测试验收。2026-10-09 09:43记录：本轮测试和清理已结束，三处业务修复已发布，全系统尚未通过。范围：生产只读/合成数据与隔离演练、限定API/MCP修复。
- 权威工作树C:/Users/test/.codex/worktrees/deb4/智慧大脑agent - 服务器端，分支codex/project-memory-no-adapter、基线431022b；共享脏树保留，不整体提交/推送，E盘源码不覆盖。
- [执行计划](../plans/2026-10-08-full-system-acceptance.md)；新证据目录.artifacts/full-system-acceptance-20261008，远端/srv/smartbrain/acceptance/full-system-20261008-r1。先核对intent/result，再执行下一步。
- 上轮20:13三服务/933容器39运行、MCP1.4.1/插件0.2.1、backup20等仅为历史线索，本轮生产状态未核对。历史17项仍未完成。
- 不触碰真实员工正文/原Key/Token，不启用灰度timer，不重启生产整机/冻结writer，不恢复到生产数据库。真实模型请求须单独写本轮明确限额/身份证据，避免重试和重复调用。
- 21:23新基线已捕获：933容器/39运行，三主服务、个人代理、read、edge双视图和备份20登记已核对，主要页面200/匿名受限接口401。
- 21:34已创建3合成账号、2项目、4个2小时MCP Token，另经正常API新建1项目；真实密码登录和角色权限已验。身份仍活动，必须主动撤销和关闭会话，勿重复创建。
- 前端40文件181项通过。后端完整67文件在实际主API依赖隔离容器跑完，61文件通过；原记录误记60，按67减6纠正。6失败文件分别含未配置PG、打包资源缺失、模块未在主API镜像存在、会议格式测试预期过时与主API非流量代理实现差异。原失败保留，不称全绿。
- 21:40线上业务第一批75通过/7失败；识别真实缺口为`[analysis]`封装漏拒绝，已保存一条合成复现，故该项目统计3而非原预期2。新增4边界Red保留；本地43通过/PG14未配置跳过，21:48新MCP镜像43通过及实际模块导入通过，尚未切换。
- 21:47资料/会议扩展验收上传及权限通过；审批实际返回202而非同步200。21:50会议任务completed，资料任务failed。21:51核对主API无mounts，文件在API层，两个worker挂共享volume且找不到此合成文件；已制定保留文件和补API共享挂载的修复，不重放审批创建。
- 21:43最新online备份36文件SHA全部通过，4小归档结构通过。隔离PG恢复r1权限问题、r2缺pg_net preload均保留；r3使用主PG实际镜像、network none、backup盘独立目录，21:58仍在COPY，runner身份`restore-created-r3.json`。不能重跑。PG测试r1在initdb磁盘同步期间超出等待、未进入测试，容器已停止，后继须新目录并确认最终postgres进程。
- 21:58当时待办（历史）：等原restore r3终态→核对修复preflight并完成API挂载/MCP过滤切换→资料重新批准并跟踪终态、会议原文/权限读回→真实PG与补齐资源复测→网页普通成员/滚动→清理临时身份、全量最终核对和报告。`business-resources.private.json`保存本轮对象；原runner意图/失败不得覆盖。后继结果如下，不重跑该历史待办。

## 最终结果与验证记录

- 完整[验收矩阵与证据](../ops/full-system-acceptance-20261008.md)和[发布记录](../releases/full-system-acceptance-fixes-20261008-r1.md)已建立；本轮不宣称原17项完成。
- 2026-10-08 22:09主API资料volume/MCP内部封装过滤发布r2通过，r1失败实际恢复保留；22:10线上业务22项/0失败。原资料审批job第6次completed，原文件hash保持。
- 22:32仅MCP旧分块读取兼容发布通过；真实PG6项、实际MCP54回归、22:33生产资料18项/0失败。权限/approved/ready/current保持，无生产DDL。
- 后继Key真实PG20、对话PG14、AGENTS资源10、实际个人代理8通过；主API镜像非活动代理的失败不用于否定实际个人入口。会议.doc拒绝测试仍为过时契约残余失败，未篡改。
- 22:36–22:36:20七关键表限定行数恢复通过，完整PG r3已700秒超时；Redis隔离RDB恢复通过。不得称完整恢复通过。恢复容器均network none/no hostport，停止/no保留。
- 2026-10-09 09:29临时3用户disabled/banned、4Token revoked、3项目completed、7会话清理、剩余会话0。验收tab关闭，09:31本轮测试/恢复容器运行0。
- 09:31完整现场963容器39运行，933基线的931无关容器保持，API/MCP为本轮明确变更；edge双视图同SHA c22e68d972ae。backup success/inactive/PID0/Job空，timer enabled、登记20。CH仍Code241，Docker42680668160<40GiB，其他盘门槛通过。
- 09:33按真实unit清单核对，旧tunnel unit failed、Docker隧道正常，read/records frontend与personal-gray API/web-r3 active/enabled；旧unit问题保持为未完成生命周期验收。
- 09:36严格TLS匿名`/v4/personal-api/v1/models`401、旧`/v4/ai-chat/device-ingest` POST410通过；原最终runner猜测`/v1/models`404保留并明确为路径错误。

## 保存、运行任务与不可重跑动作

产品改动为conversations.py/operations.py及新增test_material_chunks_compat_pg.py；本轮其他文档和安全摘要已保存，源码未整体提交/推送。E盘仅镜像本轮记录和交付文件，不覆盖源码。

09:31核对本轮运行runner/测试/恢复容器：无；fixture、两次实际发布、旧审批创建、备份启动、恢复r3、身份cleanup全部终态。先查原intent/result，不重放这些动作。受控原始证据仍在远端，私有配置/Key/正文不进入Git。

## 下一步

1. 新发布前先重新核对ClickHouse Code241根因和Docker容量，禁止以昨晚短暂通过证据放行。
2. 按失败证据重建完整PG恢复方案，再验证全部恢复内容；7表行数通过不能替代它。
3. 补实际服务生命周期/全writer维护闭包及原四模型Codex G1、真实员工Key全流程；新批次须独立身份和限额，不复活到期授权。
4. 最新用户09:17记录实际在科研项目，七个底层调用为独立ID；[病例任务](2026-10-09-conversation-receipt-work-records.md)和正确本地AGENTS已交付，另一台电脑待替换复验。
