# 智慧大脑2026-10-09夜间运维

## 任务身份与范围

- 编号：overnight-operations-20261009；负责人：Codex。
- 创建：2026-10-09 17:18（Asia/Shanghai）；阶段：运维进行中。部署范围：有限时只读采样；17:49已新增CH合并资源配置窄修复，具体见发布。
- 本轮用户授权设计、自审并开始一晚运维；截止2026-10-10 08:30北京时间。
- 方案及自审：[夜间方案](../plans/2026-10-09-overnight-operations.md)。验收：首轮现场、实际collector启动与证据、heartbeat保存/读回、次日覆盖及异常总结，不能提前称整夜完成。

## 代码与版本

- 权威工作树：C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端；codex/project-memory-no-adapter，基线431022ba5fe5169aa6be97a5e602f5995692ab91。已有dirty修改保留，不整体提交。
- 本轮仅任务/计划/CURRENT和.artifacts/overnight-operations-20261009；E盘镜像本轮文档。不覆盖个人API或其他线上源码。
- 线上期望70583b47/image6c9a5779为17:00历史，本轮完整身份待首轮采样核对。
- Git提交/推送：未执行；没有生产源码发布。

## 已完成与未完成

- 17:16只读核对：personal current service active/running、backup inactive/success/PID0/Job空；backup timer active/waiting，计划次日02:58:03；Windows9000监听PID24744。
- 方案已自审通过；collector边界11项在Linux实际通过（本地10通过/1 Linux锁跳过）。17:22真实只读首轮和17:23service采样通过，个人70583b47/image6c9a5779、edge双视图c22e68d9、39运行、公网200/匿名401与8/24/DB3预算保持。1执行/0排队/DB0、PG14 idle/1当前诊断active/锁等待0；MemAvailable约6.36GiB、无新OOM。
- 17:22 Docker42915684352字节（约39.97GiB）低于40GiB发布储备，进入预警，停止本轮新build/业务部署/大归档；其他盘通过既有门槛。17:27只读日志清单：951文件合计665354182字节，主API约156MiB且没有轮转；不能将其当磁盘增长主因或删除依据。
- 17:27直接ClickHouse内部err.log仍有实时Code241；r1仅Docker日志采样漏了此信号。r2增加固定UTC窗口/256KiB尾部采样，测试11通过并17:29实际采到28处Code241文本（尾部计数，不是完整故障数）；仍未修改CH业务配置/重启或删除数据。
- r1 observer停止后临时unit被systemd回收，旧update脚本start返回5；失败保留。17:29仅按新r2 SHA重新创建本次observer，样本序列继续，生产业务服务不改。今后只观察原r2，禁止重跑install/start/update/resume。
- 同对话夜间heartbeat已创建并17:30更新为r2，ID `10-10-08-30`，目标对话01a11a9d-f4bd-7b61-9b09-b1439da4fe7c，每30分钟，截止10-10 08:30；实际配置已读回ACTIVE。安静巡检，重要异常/完成才通知。采样进行中，不代表整夜完成。

## 运行中的任务

- 现有backup未运行，次日02:58 timer正常计划待观察；不得手动重放。
- 本次collector：smartbrain-overnight-observe-20261009.service，当前r2 Invocation95565b7dce3e4b7db335aa756022a466/PID872681，17:29核对active/running，约16MiB，内存上限192MiB/CPU15%/Restart=no/临时unit不enable；截止00:30Z，硬RuntimeMax带180秒收尾保险。
- 服务器证据：/srv/smartbrain/acceptance/overnight-operations-20261009，目录0700/文件0600；当前源码SHA419fe2b09d12890f3f04ddad9cab9db50d4ed50a2a17766bf287f4e68f744c5b。baseline/samples/runs/collector-r2-verified及旧r1保留；每5分钟、220轮/16MiB上限，无监听/模型/生产DB写入。
- 只读观察：权威工作树内 `.artifacts/overnight-operations-20261009/observe.py`，使用固定Python运行；读取确切原unit、样本、窗口错误/空间及本机Windows9000脱敏事件，不重新创建采样器。到期允许unit自动回收，以runs.jsonl的deadline终态及无活进程佐证，不把not-found视为业务服务失败。
- 旧流式修复runner均终态，不重跑旧发布/模型批次/归档。

## 下一步

1. 每次先observe原r2、新样本和备份状态。结合最近窗口聚合及Windows时间戳，区分供应商过载/客户端499/网关超时；缺口和日志尾部上限如实记录。
2. 重点看Docker储备的趋势、CH Code241与共享盘压力；确认根因再设计具体最小候选，不为通过门槛执行prune或清空历史。02:58只观察原定时备份。
3. 明早08:30之后写ops早间报告、更新任务/CURRENT，暂停并读回本次heartbeat。若observer尚活着只核对原Invocation后停止observer；不新开业务变更，不把尚未验收的全库恢复/全writer/30真实成员容量称通过。

## 本轮验证与Git状态

证据 `.artifacts/overnight-operations-20261009/{tests-red,tests-red-2,tests-red-3,tests-green-3,prepared,start-verified,storage-diagnosis,collector-r2-verified}.log/json`；完整Linux11项与现场保留远端。17:30旧业务个人/edge/其他39容器没有本轮重启，生产DB写入/主动模型调用0。本轮新collector与任务文档未Git提交或push，旧dirty保留。

17:32只读回看：r2原Invocation/PID与源码SHA一致，4个样本、无>450秒缺口/采集错误，已有15次200/1次499/1次502。17:29:41的50214784ms与Windows上游server_is_overloaded14760ms对应，无新ReadTimeout或persistence failed；不是网关旧120秒问题。r2最新Docker43911176192字节（约40.90GiB）回到储备线上方，但波动来源未核对，不能称容量问题修好，继续预警观察。内存最小约6.17GiB、OOM增量0。心跳ACTIVE/有限截止、r2身份和E盘文档实际字节核对通过（setup-verified.json）。

17:51后继：[CH方案](../plans/2026-10-09-overnight-clickhouse.md)和[实际发布](../releases/overnight-clickhouse-20261009-r1.md)。已确认系统日志合并16×2产生25后台任务/2核全部节流/内部3.6GiB超限；同版本隔离2/1及阈值、20000行/测试重启读回通过。双锁与四盘/备份20登记通过后，仅CH原CID f0a0f6eb配置SHA改ecf3efd2并短停启动；StartedAt09:49:40.337495161Z/PID930830。1022无关容器完整配置代际保持、39运行、原4业务表元数据行数保持、公网8入口/个人网关/edge/备份通过，真实模型/DDL0。效果待两个后续窗口，不宣称长期问题解决。

17:45:37自然个人请求902086ms的502与Windows上游request_timeout/stream_incomplete902061ms对应，仍非网关120秒；原17:49模型调用超时与CH短停前发生，不能误归CH调整。继续区分上游capacity与其他上游失败。

17:57 CH效果：后台任务2、5秒CPU节流1/50（原50/50），text_log parts88→25并仍推进；但新Code241持续，单次合并峰值尚待下一阶段实验，不能称已修好全部内存错误。原CID/image与新配置SHA不变，暂保持2/1，不循环重启或扩大内存。部署分支新增固定XML SHA核验，23项工具回归/source manifest通过，准备official分支交付，非原dirty整体提交。

18:01首个运维续跑收尾：10个样本/无>450秒缺口、采集错误0、host OOM增量0；35个个人200/1个499/3个502，网关0排队/DB0/无ReadTimeout或落库失败。CH两个后续窗口仍有Code241，CPU和parts改善属于局部效果，不能称彻底修复。cold空闲采样256352428032（238.75GiB），18:01单次260042219520（242.18GiB）低于250GiB储备；system.parts见新6.77GB活动合并结果及待清理inactive parts，空间仍波动，未确认全部差额来源。停止进一步生产调整/大型测试及归档，观察正常旧parts回收，不手工删除或恢复高并行。

正式交付分支codex/overnight-operations-20261009提交8430aa6a25ade34adb36a84af8bd555e5839c410已推official且远端一致，main431022b保持；未创建PR/未合并。新XML实际SHA与生产一致，23工具测试及sources通过。后续仅诊断单次合并block/缓冲与空间趋势；生产变更须容量门槛恢复及新候选验证。两个隔离CH测试容器停止保留，不重放。

18:08再核对：cold271892676608字节（253.22GiB）重新超过250GiB，先前text_log inactive大parts已从只读前8清单消失；本轮没有手工清理。正常回收支持临时合并副本占空间的解释，但其他增长来源仍需趋势核对。Docker43683471360字节（40.68GiB）；CH重启后Code241累计1621/最新18:08仍新增。保持局部并行改善，下一阶段仅先查单次合并block/宽表和隔离候选，不直接继续改生产。交付工作树当前official新分支14ad3d028d1634cf456c304f09733f4c5da0a9e5（18:04远端一致，干净），无PR/main改动。心跳已补本轮现场和禁止重放步骤，ACTIVE读回，observer原r2继续。

18:09心跳读回ACTIVE并补充最新现场。为容纳模型/调度延迟，日程增加到次日09:30的**仅收尾**窗口；业务处置与collector硬截止仍08:30。首次08:30或之后唤醒只能写报告/核对终态/暂停本心跳，不新开生产调整。官方分支后继6ab33fc93f6c111500f0d8130e7c0ec0ea5996c7已核对；本轮测试/候选/发布runner终态，唯原observer/heartbeat继续。

18:30–18:36后继：observer原r2/SHA保持，16样本/无缺口/采集错误/host OOM；个人仍35个200/1个499/3个502，18:00后无新个人完成记录，不能将无流量窗口称实际模型成功验收。公网/edge/备份保持；cold253.21GiB、Docker40.54GiB。CH Code241继续，18:36累计5738；已核对metric_log1136列/多数Compact、32–33-part Horizontal输出在WriterWide创建流时分配失败，实际版本源码与默认压缩buffer1MiB相符。

18:42–18:47新隔离r3/r4通过：r3默认复现Code241，仅表级max_compress_block_size64KiB后12800行/1132数值列聚合保持；r4两个32part宽表同时合并、合计跟踪内存约966MB/0 Code241，真实system.metric_log ALTER/配置重载/重启和测试回退保持UUID/行数、无自动更名。测试无网络/端口，足迹66.8/145.7MB，全部停止保留。方案和自审：[宽表buffer](../plans/2026-10-09-clickhouse-wide-buffer.md)。

18:50生产窄发布：[记录](../releases/overnight-clickhouse-buffer-20261009-r2.md)。双锁/backup20/最新四盘和内存通过，仅system.metric_log表级max_compress_block_size65536及原inodeXML同步/重载，SHA **e14fd07b4f175eccaab22c1dfde8d5bb08ea377fdfceb8828e06db7dd56643cd**；无生产容器重启、日志删除或业务表修改。CH同CID/image/17:49启动/PID930830，metric UUID157524f1保持。18:51独立核对全部1025容器配置代际、23业务对象UUID/结构hash和元数据行数、8公网/个人current预算/edge/备份通过。

18:51短效果：Code241仍7705/最后18:49:57，metric parts约323→38，大合并推进；两个完整后继窗口及整夜待观察。Docker40.19GiB/cold252.22GiB，储备薄，保持门禁。r3/r4/promote_ch_metric_buffer_r2全部终态，禁止重放；只观察原observer、ch_merge_space/verify和后继样本。交付XML/hash同步待本轮提交，不改原包/镜像。

18:58本阶段收尾核对：18:57 Code241仍7705、最后18:49:57，无新错误；新大metric合并完成，cold270586347520字节（约252.00GiB）/Docker43146698752（40.18GiB）。observer原r2/SHA与PID872681保持，21样本/无缺口/采集错误/host OOM；18:54样本覆盖18:49–18:54，尾部27处Code241属于18:49:57的**发布前**旧错误，不能归为新设置失败。首个完全后继窗口从18:54开始，两个完整窗口尚待下次续跑核对。个人仍35/1/3，无新自然完成请求，Windows9000仍PID24744。

正式交付修复提交778349b18d8b00d635cf276051abd51b254a1b64已推official/远端一致，main431022b保持；XML与生产e14fd07b逐字节一致，release-lock为current-20261009-streaming-ch-r2，23部署测试及sources检查通过。5份本轮文档镜像E盘/交付树并核对字节；heartbeat补本次新SHA/不可重放/后继窗口要求，ACTIVE/名称/日程/目标/完整prompt读回一致。保存metric-buffer-stage-checkpoint.json和脚本hash，所有候选与发布runner终态，仅原collector/heartbeat继续；未做生产回退、完整恢复或实际30人容量验收。
