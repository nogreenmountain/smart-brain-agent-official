# 智慧大脑2026-10-09夜间运维

## 任务身份与范围

- 编号：overnight-operations-20261009；负责人：Codex。
- 创建：2026-10-09 17:18（Asia/Shanghai）；阶段：已结束（2026-10-10 08:30业务授权到期，08:49收尾核对）。部署范围：本晚有限时只读采样、17:49 CH限并行及18:50目标宽表缓冲修复；详见早间报告与发布。
- 本轮用户授权设计、自审并开始一晚运维；截止2026-10-10 08:30北京时间。
- 方案及自审：[夜间方案](../plans/2026-10-09-overnight-operations.md)。验收：首轮现场、实际collector启动与证据、heartbeat保存/读回、次日覆盖及异常总结，不能提前称整夜完成。

## 最新接续状态（2026-10-10 08:49）

已生成[早间报告](../ops/overnight-operations-20261009.md)，observer自然deadline终态、heartbeat PAUSED，原定时online备份success；无本任务仍运行的collector/候选/发布/备份runner。生产业务与原正常backup timer仍运行。下文初始运行状态/下一步仅为带时间的历史，不能复活夜间授权；本次权威工作树和旧dirty修改保留，最终文档本地/E盘保存、未提交/push。

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

19:01再次核对：22样本/最新18:59:48，首个完整18:54:48–18:59:48窗口内部err.log Code241=0，入口200/匿名401和个人日志错误0；19:01直接计数仍7705/最后18:49:57，metric parts21/元数据行数3771309，表设置与预处理配置保持。cold271994171392字节（253.31GiB）/Docker43143720960（40.18GiB）恢复一些临时合并空间，MemAvailable最近采样8341897216字节。cgroup max累计3492（18:43为2503），没有OOM/oom_kill；该增量时间未逐条定位，不能把缓存回收/limit事件称零压力。尚需第二个完全后继采样窗口和整夜趋势，继续只读观察。文档后继提交122cd8f48427ef47e6f0d55a9887ccb7df9faf02已推official/远端一致、工作树干净，main不变。

正式交付修复提交778349b18d8b00d635cf276051abd51b254a1b64已推official/远端一致，main431022b保持；XML与生产e14fd07b逐字节一致，release-lock为current-20261009-streaming-ch-r2，23部署测试及sources检查通过。5份本轮文档镜像E盘/交付树并核对字节；heartbeat补本次新SHA/不可重放/后继窗口要求，ACTIVE/名称/日程/目标/完整prompt读回一致。保存metric-buffer-stage-checkpoint.json和脚本hash，所有候选与发布runner终态，仅原collector/heartbeat继续；未做生产回退、完整恢复或实际30人容量验收。

19:05续跑：两个完整后继窗口18:54:48–18:59:48和18:59:48–19:04:48均0 Code241；直接未清零计数仍7705/最新18:49:57。r2原Invocation/PID/SHA保持，23样本、无>450秒缺口/采集错误/host OOM。19:05独立复核1025个容器完整配置与启动代际保持、39运行，23业务对象结构/UUID/元数据行数和metric原UUID、新XMLe14fd07b、8公网入口、personal current精确绑定/8/24/DB3、edge双视图及backup20登记通过。没有本轮生产变更或测试重放。

CH metric active parts21/text_log16，当前无活动合并；跟踪内存267346197字节、cgroup约2.60GB（不同口径，不能相减当精确缓存数）。19:01→19:05 memory.events.max均3492，5秒CPU节流0/50、无OOM/oom_kill；18:43→19:01的历史增量时刻仍未定位，不把整段当零压力。MemAvailable最近8362524672字节、SwapFree291627008字节，未见新增host OOM。空间Docker43143774208（40.18GiB）/cold271992659968（253.31GiB）/runtime34295930880/backup554074771456字节，仍薄储备，不继续大测试/归档。

个人完成仍35×200/1×499/3×502，18:00之后无自然完成；最近窗口0排队/DB0、PG14 idle/1诊断active/无idle-in-transaction，日志超时/连接/落库失败0；Windows脱敏事件无新增。timer仍次日02:58:03，backup inactive/success/PID0/Job空，仅观察原计划。此次已满足两窗口效果验证，整夜与30真实成员容量仍待；继续原有限observer/heartbeat。

19:30例行核对：observer原r2/Invocation/PID/SHA保持，28样本/最新19:29:48，无>450秒缺口/采集错误/host OOM。CH累计Code241仍7705/最后18:49:57，窗口0，metric parts19/text_log20，cgroup max仍3492/0 OOM，5秒节流0/49。1025容器配置和代际、23业务对象/原metric UUID/实际XMLe14fd07b、8公网/个人current/edge/backup20再度只读核对通过。

Docker43133288448（40.17GiB）/cold272098820096（253.41GiB）/runtime34295361536/backup554074771456字节，仍薄储备；MemAvailable最近8407027712字节。19:04→19:29新增换入131页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some0.13/full0.12。个人仍35/1/3，19:29采样0执行/19:30即时1执行、排队0/DB0，没有新完成请求或窗口错误；Windows9000/PID24744与脱敏事件保持。backup inactive/success/PID0/Job空、timer原02:58:03、无maintenance.pending。本轮无生产处置；证据observation-20261009T113043Z.json、ch-metric-buffer-r2-verified.json、ch-pressure-20261009T113043.json与cycle-20261009T1130.json保留，继续原有限巡检。

20:00续跑：observer原r2/Invocation/PID/SHA保持，34样本/最新19:59:48、无缺口/采集错误/host OOM。累计个人60×200/1×499/4×502；恢复自然流量，19:29–19:59新增gpt-6-sol 25×200，最长140030ms，content_complete/usage_missing聚合分别全部完整/无未知；另1×502、不完整/未知保持，19:45:18的24453ms与Windows同秒上游24419ms、HTTP200内failed/server_is_overloaded/capacity对应，耗时差34ms。没有主动模型测试、人工重试/切模型；不是网关旧120秒超时或CH短停。仅聚合只读SQL、statement5s/lock2s，未输出员工正文。

CH仍Code2417705/最后18:49:57，最近窗口0、metric parts18/text_log16、cgroup max3492不增/0 OOM，5秒节流0/49。1025容器配置代际、23业务对象/原metric UUID/XMLe14fd07b、8公网/个人current/edge/backup20独立核对通过。最近gateway0执行/即时1执行、排队0/DB0，PG14 idle/1诊断active、无idle-in-transaction，窗口连接/超时/落库失败0。Docker43121872896（40.16GiB）/cold272150245376（253.46GiB）/runtime34294558720/backup554074771456字节；MemAvailable8028725248。backup inactive/success/PID0/Job空、timer原02:58:03保持，原Windows9000/PID24744；无本轮生产变更。证据observation-20261009T120047Z.json、natural-traffic-20261009T120204.json、ch-pressure-20261009T120047.json、cycle-20261009T1200.json及远端独立复核保留。


20:30例行核对（实际20:33–20:35）：observer原r2/Invocation95565b7d/PID872681/SHA保持，40样本、最新20:29:48，无>450秒缺口/采集错误/host OOM；证据约10.34MB，原到期08:30保持。20:00–20:29新增自然gpt-6-sol 15×200，最长67972ms，完成标记/已知用量标记全部保存；另2×502/不完整/用量未知，累计75×200/1×499/6×502。20:06:37的35118ms与Windows同秒capacity/server_is_overloaded35108ms对应（差10ms），20:08:37的35499ms与同秒35463ms对应（差36ms）。上游HTTP200内部failed，与网关旧120秒截断或连接故障无对应证据；未主动调用模型、重试或切换模型。

CH直接累计Code241仍7705/最后18:49:57，最近窗口内部错误0，metric parts约21–22/text_log20，当前无活动merge；原CID/image/17:49启动/PID930830及XML e14fd07b、metric UUID保持。cgroup max仍3492/0 OOM/oom_kill，5秒CPU节流0/50。1025容器完整配置及启动代际、23业务对象结构/UUID/元数据行数、8公网200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图及backup20独立只读核对通过。最近与即时网关均0执行/排队0/DB0，PG14 idle/1诊断active、无idle-in-transaction，最近窗口超时/连接/落库失败0。

20:29样本MemAvailable8448860160字节；19:59→20:29换入687页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some0.14/full0.13，未据此称历史Swap已释放。20:33即时空闲Docker43130281984（40.17GiB）/cold272144814080（253.45GiB）/runtime34293747712/backup554074771456字节，仍薄储备，不新增测试/配置/大归档。backup inactive/success/PID0/Job空、timer原次日02:58:03、无maintenance.pending；Windows9000/PID24744保持。本轮无生产处置；同类别供应商capacity事件继续观察，不盲重启。任务及证据仅本地/E盘更新，CURRENT无新阶段变化、交付分支沿用20:03 b8a46712；早间或重要变化再同步。证据cycle-20261009T1230.json、observation-20261009T123353Z.json、natural-traffic-20261009T123425.json、ch-pressure-20261009T123353.json及本轮不可变独立核验保留；整夜/真实30人容量/完整PG及全writer冻结恢复仍未验。

20:37窗口补核（20:30续跑）：本轮六个完整后继5分钟样本分别20:04/09/14/19/24/29:48，全部入口符合200/401、内部CH错误及个人超时/连接/落库错误0、无采集错误/个人身份漂移/pending；采样峰值执行0/排队0/DB0（仅离散采样峰值，不等于窗口真实峰值），MemAvailable最小8066314240字节。cycle-windows-20261009T1230.json及cycle追加证据，两端任务镜像一致。


21:00例行核对（实际21:00–21:02）：observer原r2/Invocation95565b7d/PID872681/SHA保持，46样本、最新20:59:48，无>450秒缺口/采集错误/host OOM，证据约10.57MB。20:29:48–20:59:48六个完整5分钟样本全部入口200/匿名401、内部CH错误及网关超时/连接/落库错误0，个人身份/8执行24等待DB3预算与edge双视图保持，无maintenance.pending。新增自然gpt-6-sol 4×200、最长54379ms，全部完成标记/已知用量标记保存；无新失败或Windows脱敏上游错误，累计79×200/1×499/6×502，不是主动模型测试。

21:01独立核对1025容器完整配置与启动代际、23业务对象结构/UUID/元数据行数、8公网入口/个人current精确绑定/edge/backup20通过。CH仍原CID/image/17:49启动/PID930830、XML e14fd07b与原metric UUID，Code241未清零计数7705/最后18:49:57；metric parts22/text_log19、当前无活动merge，cgroup max3492保持/0 OOM/oom_kill、5秒CPU节流0/49。六样本采样峰值执行0/排队0/DB0（离散采样不代表区间真实峰值），PG14 idle/1诊断active、无idle-in-transaction。

最近MemAvailable8429568000字节/本轮最小8231821312字节；20:29→20:59换入46页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some/full0.11。即时空闲Docker43128659968（40.17GiB）/cold272087273472（253.40GiB）/runtime34292940800/backup554074771456字节，仍薄储备，继续门禁；backup inactive/success/PID0/Job空，timer原次日02:58:03，Windows9000/PID24744保持。本轮无生产变更/测试重放，原collector和heartbeat继续至08:30。证据cycle-20261009T1300.json及五份本轮只读证据保留，任务镜像E盘；CURRENT无新重要阶段变化、交付分支沿用b8a46712，例行记录尚未追加push。整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。


21:30例行核对（现场21:30–21:32）：observer原r2/Invocation95565b7d/PID872681/SHA保持，52样本、最新21:29:48，无>450秒缺口/采集错误/host OOM，证据约10.79MB。20:59:48–21:29:48六个完整5分钟样本均入口200/匿名401、内部CH错误及个人超时/连接/落库错误0、个人身份/current精确绑定/8执行24等待DB3预算及edge双视图保持，无maintenance.pending。聚合SQL同窗没有新增personal_api完成或失败，累计仍79×200/1×499/6×502，无真实模型主动测试。

本机Windows上游21:15:21.964出现一条/v1/messages、HTTP200内upstream_error/type=server_error、reason=unclassified、code为空、63769ms；同窗personal_api无对应记录，调用来源和具体根因未核对，不能归为供应商capacity或个人网关故障，不盲重启/切模型/重试。脱敏字段保存在observation及cycle，未读取或输出正文。

21:32独立核对1025容器完整配置与启动代际、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过。CH原CID/image/17:49启动/PID930830、XML e14fd07b及原metric UUID保持，Code241累计7705/最后18:49:57未增；metric parts22/text_log20，当前无活动merge；cgroup max3492保持/0 OOM/oom_kill，5秒CPU节流0/50。六样本采样峰值执行0/排队0/DB0（非区间真实峰值），PG采样最大14 idle/1诊断active、idle-in-transaction0。

最近MemAvailable8441925632字节/本轮最小8010706944字节；20:59→21:29换入630页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some/full0.13。即时空闲Docker43116597248（40.16GiB）/cold272027467776（253.35GiB）/runtime34292109312/backup554074771456字节，仍薄储备；backup inactive/success/PID0/Job空，timer原次日02:58:03，Windows9000/PID24744保持。本轮无生产处置/测试重放，继续原collector/heartbeat至08:30。证据cycle-20261009T1330.json及五份本轮只读证据保留，任务镜像E盘；CURRENT无重要阶段变化、交付分支沿用b8a46712，例行记录未追加push。整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。


22:00例行核对（现场22:00–22:02）：observer原r2/Invocation95565b7d/PID872681/SHA保持，58样本、最新21:59:48，无>450秒缺口/采集错误/host OOM，证据约11.02MB。21:29:48–21:59:48六个完整5分钟样本全部入口200/匿名401、内部CH错误及个人超时/连接/落库错误0，current精确绑定/8执行24等待DB3预算/个人身份/edge双视图保持，无maintenance.pending。聚合SQL同窗personal_api无新增完成或失败，累计仍79×200/1×499/6×502；Windows脱敏上游错误无新增，21:15未分类/v1/messages事件归属仍未核对，不补称已确认原因。

22:01独立核对1025容器完整配置与启动代际、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过。CH原CID/image/17:49启动/PID930830、XML e14fd07b及原metric UUID保持，Code241累计7705/最后18:49:57未增；metric parts22/text_log20，当前无活动merge；cgroup max3492保持/0 OOM/oom_kill，5秒CPU节流0/50。六样本采样峰值执行0/排队0/DB0（非区间真实峰值），PG采样最大14 idle/1诊断active、idle-in-transaction0。

最近MemAvailable8321982464字节/本轮最小8149417984字节；21:29→21:59换入184页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some0.14/full0.13。即时空闲Docker43104952320（40.14GiB）/cold272049827840（253.37GiB）/runtime34291310592/backup554074771456字节，储备仍薄，不新增build/发布/大归档；backup inactive/success/PID0/Job空，timer原次日02:58:03，Windows9000/PID24744保持。本轮无生产处置/主动模型/测试重放，原collector/heartbeat继续至08:30。证据cycle-20261009T1400.json及五份本轮只读证据保留，任务镜像E盘；CURRENT无新重要变化，交付分支沿用b8a46712，例行记录未追加push。整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。


22:30续跑（现场22:31–22:34）：observer原r2/Invocation95565b7d/PID872681/SHA保持，64样本、最新22:29:48，无>450秒缺口/采集错误/host OOM，证据约11.25MB。21:59:48–22:29:48六个完整5分钟样本入口均200/匿名401，个人超时/连接/落库错误0、current精确绑定/8执行24等待DB3预算/个人身份/edge双视图保持，无maintenance.pending。聚合SQL同窗personal_api无新增完成或失败，累计仍79×200/1×499/6×502。

Windows9000上游/v1/messages出现新连续限流类别：完整采样区间内22:25:31一条HTTP200内capacity/service_unavailable_error（40024ms），22:28:28/22:29:05/22:29:43三条HTTP429、kind=rate_limit/type=rate_limit_error（38752/36580/36436ms）；同窗无personal_api对应完成或失败。采样截止后22:30:21/22:31:01另两条429（36493/36717ms），其后继采样覆盖尚待下轮。调用来源和限额类型未核对，不把所有上游调用归到个人网关，也不自动重试、切模型、修改OAuth或盲重启。脱敏时间/状态/分类/耗时保留，未输出正文。21:15未分类server_error仍保留原结论。

22:32独立核对1025容器完整配置与启动代际、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过。CH原CID/image/17:49启动/PID930830、XML e14fd07b及原metric UUID保持，Code241累计7705/最后18:49:57未增；metric parts19/text_log19，短暂asynchronous_metric_log两part Horizontal合并progress0.16/跟踪16.5MB，未见新错误；cgroup max3492保持/0 OOM/oom_kill，5秒CPU节流0/50。六样本采样峰值执行0/排队0/DB0（非区间真实峰值），PG采样最大14 idle/1诊断active、idle-in-transaction0。

最近MemAvailable8321134592字节/本轮最小8065159168字节；21:59→22:29换入63页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some0.14/full0.13。即时空闲Docker43093344256（40.13GiB）/cold272092278784（253.41GiB）/runtime34282086400/backup554074771456字节，储备仍薄，不新增build/发布/大归档；backup inactive/success/PID0/Job空，timer原次日02:58:03，Windows9000/PID24744保持。本轮无生产处置/主动模型/测试重放，继续原collector/heartbeat至08:30。证据cycle-20261009T1430.json及五份本轮只读证据保留，任务镜像E盘；新上游限流类别追加CURRENT并准备仅本任务文档同步official分支，不整体提交dirty树。整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。

22:40:19文档收尾：本阶段仅CURRENT/本任务两份文档提交2f783d33c8ef0716a9519033054d27ada2c420c8并push official/codex/overnight-operations-20261009，远端SHA读回一致、交付工作树干净，未改main；权威/E/交付CURRENT字节一致，保留原dirty源码。本条实际push读回补充仅本地/E盘，见docs-stage-20261009T1430.json；原collector/heartbeat与02:58备份继续，不重跑本轮测试/发布。


23:00续跑（现场23:01–23:03）：observer原r2/Invocation95565b7d/PID872681/SHA保持，70样本、最新22:59:48，无>450秒缺口/采集错误/host OOM，证据约11.49MB。22:29:48–22:59:48六个完整5分钟样本入口均200/匿名401，内部CH错误及个人超时/连接/落库错误0，current精确绑定/8执行24等待DB3预算/个人身份/edge双视图保持，无maintenance.pending。新增自然gpt-6-sol 29×200，最长64404ms，完成及已知用量标记全部保存；另2×502/不完整/用量未知，样本累计108×200/1×499/8×502。22:42:16的46842ms与Windows同秒/v1/responses capacity/server_is_overloaded46835ms对应（差7ms），22:55:01的28573ms与28540ms对应（差33ms），没有证据将其归为网关120秒截断或连接占用。

22:59:48–23:01:08补查另1×502，22:59:50的24764ms与同秒上游24714ms/capacity对应（差50ms），失败完整/用量状态保持；该尾段会进入下一常规窗口，整夜汇总禁止重复加计。Windows/v1/messages本轮采样区间内7条429，其中22:30/22:31两条属于上轮尾段、本轮已获得采样覆盖，其余5条在22:33–22:34为新事件；具体调用来源/限额类型仍未核对，未直接归为个人网关失败。另两条/v1/messages capacity保留未关联状态，未主动重试/切模型/改OAuth或重启。

23:01独立核对1025容器完整配置与启动代际、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过。CH原CID/image/17:49启动/PID930830、XML e14fd07b与原metric UUID保持，Code241累计7705/最后18:49:57未增，metric parts19/text_log18、当前无活动merge；cgroup max3492保持/0 OOM/oom_kill、5秒CPU节流0/50。最近采样个人1执行/即时0执行，六样本采样峰值执行1/排队0/DB0（非真实峰值）；PG采样最大14 idle/2 active（含诊断）、最长事务0.235395秒、idle-in-transaction0。

最近MemAvailable8421343232字节/本轮最小8042278912字节；22:29→22:59换入262页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some0.22/full0.21。即时空闲Docker43091427328（40.13GiB）/cold272051658752（253.37GiB）/runtime34281275392/backup554074771456字节，储备仍薄；backup inactive/success/PID0/Job空，timer原次日02:58:03，Windows9000/PID24744保持。本轮无生产处置/主动模型/测试重放，原collector/heartbeat继续至08:30；证据cycle-20261009T1500.json及六份本轮只读证据保留，任务镜像E盘。CURRENT无新阶段变化，official交付仍2f783d33/干净，例行记录仅本地/E，早间或重要变化再push。整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。

23:07:20后继记录：上述CURRENT不更新决定已由本条覆盖；为关闭22:30两个尾段限流未覆盖状态，以及明确新增自然流量/三次供应商过载关联，已将23:01核对结论追加CURRENT。本阶段只同步CURRENT与本任务两份文档至official分支，不改生产或main。cold按实际272051658752字节折合253.37GiB。

23:09:03文档收尾：本阶段仅CURRENT/本任务两文档提交fa10875a3bc5ed964eef0062801e0b518a669fd3并push official/codex/overnight-operations-20261009，远端SHA读回一致、交付工作树干净、main未改；三处CURRENT字节一致。此实际push补充仅权威/E盘，证据docs-stage-20261009T1500.json；原collector/heartbeat、02:58计划备份与08:30截止继续。


23:30例行核对（现场23:31–23:32:58，本条23:38:37整理既有证据）：observer原r2/Invocation95565b7d/PID872681/SHA保持，76样本、最新23:29:48，无>450秒缺口/采集错误/host OOM，证据11716958字节（约11.72MB）。22:59:48–23:29:48六个完整5分钟样本入口均200/匿名401，内部CH错误及个人超时/连接/落库错误0，current精确绑定/8执行24等待DB3预算/个人身份及edge双视图保持，无maintenance.pending。新增自然gpt-6-sol 28×200，最长96459ms，完成及已知用量标记全部保存，样本累计136×200/1×499/9×502；区间唯一502为22:59:50、24764ms，与Windows同秒/v1/responses capacity/server_is_overloaded24714ms对应（差50ms）。它正是上轮23:00尾段已经记录的同一失败，整夜汇总不得重复加计，本轮没有新首次观察的物理失败。

23:01:08以后至本轮Windows有界只读观察没有新增脱敏上游错误；既有/v1/messages调用来源与具体限额类型仍未核对，不能据无新增错误称上游问题已解决。23:32独立核对1025容器完整配置与启动代际、39运行、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过，范围仍不是全库checksum。CH原CID/image/17:49启动/PID930830、XML e14fd07b及原metric UUID保持，Code241未清零计数7705/最后18:49:57未增；metric parts22/text_log16、当前无活动merge，cgroup max3492保持/0 OOM/oom_kill、5秒CPU节流0/49。最近采样个人0执行/DB0，即时独立健康1执行/DB1/等待0，符合8/24/3预算；六样本采样峰值执行1/排队0/DB0仅为离散采样峰值，PG采样最大14 idle/1诊断active，idle-in-transaction0、最长事务0.0秒。

最近MemAvailable8406970368字节/六窗口最小8020795392字节；22:59→23:29换入323页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some/full0.15。即时空闲Docker43099451392（40.14GiB）/cold272053100544（253.37GiB）/runtime34280431616/backup554074771456字节，储备仍薄，继续门禁。backup inactive/success/MainPID0/ControlPID0/Job空、Invocation6508042bb54b49a5b26cd27a4a461796，timer原次日02:58:03；Windows9000/PID24744保持。本轮无生产处置/主动模型/测试重放，仅整理已经完成的只读证据，原collector/heartbeat继续至08:30。证据cycle-20261009T1530.json及六份本轮只读证据保留，任务镜像E盘；无新重要阶段结论，CURRENT不更新，本轮例行记录不追加push。整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。


10-10 00:00例行核对（现场00:01–00:03:34）：observer原r2/Invocation95565b7d/PID872681/SHA保持，82样本、最新10-09 23:59:48，无>450秒缺口/采集错误/host OOM，证据11957295字节（约11.96MB）。23:29:48–23:59:48六个完整5分钟样本入口均200/匿名401，内部CH错误及个人超时/连接/落库错误0，current精确绑定/8执行24等待DB3预算/个人身份及edge双视图保持，无maintenance.pending。新增自然gpt-6-sol 36×200，最长120299ms，完成及已知用量标记全部保存，无区间失败；累计172×200/1×499/9×502。Windows有界脱敏观察没有新增上游错误，既有/v1/messages调用来源与具体限额类型仍未核对，不能据无新增错误宣布上游问题解决；本机9000监听仍PID24744。没有主动模型测试、切模型或重试。

00:02独立核对1025容器完整配置与启动代际、39运行、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过，范围不是全库checksum。CH原CID/image/17:49启动/PID930830、XML e14fd07b及原metric UUID保持，Code241未清零计数7705/最后10-09 18:49:57未增，metric parts19/text_log20、当前无活动merge；cgroup max3492保持/0 OOM/oom_kill、5秒CPU节流0/50；两轮探针末点之间累计新增2个节流周期，不能将短探针称整个半小时零节流。已知currentQueryID诊断查询仍exit46，属于此版本只读诊断限制，未据此认定生产故障。最近及即时个人均0执行/等待0/DB0；六样本采样峰值执行1/等待0/DB0仅为离散采样峰值，PG采样最大14 idle/1诊断active、idle-in-transaction0、最长事务0.0秒。

最近MemAvailable8391139328字节/六窗口最小8023584768字节；23:29→23:59换入177页/换出0/OOM0，memory PSI avg10/60/300均0，IO avg300 some0.22/full0.21。即时空闲Docker43087568896（40.13GiB，仅比40GiB线多137895936字节、约131.5MiB）/cold272007520256（253.33GiB）/runtime34279587840/backup554074771456字节，储备仍薄，继续暂停新build/发布/大归档，不清理历史。backup inactive/success/MainPID0/ControlPID0/Job空、Invocation6508042bb54b49a5b26cd27a4a461796，timer原今日02:58:03，无maintenance.pending。原计划启动后只跟踪其实际新Invocation/PID/Job，不开启第二批。本轮无生产处置/主动模型/测试重放；证据cycle-20261009T1600.json及六份本轮只读证据保留，任务镜像E盘；无重要新阶段结论，CURRENT不更新、例行记录不追加push。原collector/heartbeat继续，业务与collector截止今日08:30；整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。


00:30例行核对（现场00:30–00:36:26）：observer原r2/Invocation95565b7d/PID872681/SHA保持，88样本、最新00:29:48，无>450秒缺口/采集错误/host OOM，证据12185012字节（约11.62MiB）。23:59:48–00:29:48六个完整5分钟样本入口均200/匿名401，内部CH错误及个人超时/连接/落库错误0，current精确绑定/8执行24等待DB3预算/个人身份及edge双视图保持，无maintenance.pending。该半小时没有personal_api完成或失败记录，累计仍172×200/1×499/9×502；Windows有界脱敏观察没有新增上游错误，不把无流量窗口称真实模型容量验收。本机9000监听核对仍PID24744，无主动模型测试、切模型或重试。

00:31独立核对1025容器完整配置与启动代际、39运行、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过，范围不是全库checksum。CH原CID/image/17:49启动/PID930830、XML e14fd07b及原metric UUID保持，Code241未清零计数7705/最后10-09 18:49:57未增，metric parts22/text_log16、当前无活动merge；cgroup max3492保持/0 OOM/oom_kill，独立5秒探针节流0/50，两轮末点间累计新增2个节流周期，不称整个半小时零节流。currentQueryID诊断查询继续exit46，属于此版本诊断限制。六样本离散峰值执行/等待/DB均0，PG最大14 idle/1 active、idle-in-transaction0、最长事务0.0秒。

六窗口MemAvailable最低8217378816字节，换入260页/换出0/OOM0，memory PSI全0；即时空闲Docker43075481600（40.12GiB，仅比40GiB线多125808640字节、约120MiB）/cold271930200064（253.25GiB）/runtime34281672704/backup554074771456字节，储备继续薄，停止新build/发布/大归档，不清理历史。00:36只读统计当前运行容器Docker LogPath当前文件302549529字节、数字轮转.1–.10合计320001254字节；最大当前文件为smartbrain-api-agents-short-ready-20261008-r1约207.9MB。该统计不读取正文且不是完整历史扫描，作为后续增长来源线索保存，尚不能归因本轮全部磁盘增量。backup inactive/success/PID0/Job空、Invocation6508042bb54b49a5b26cd27a4a461796，timer今日02:58:03，无maintenance.pending；启动后仅跟踪原批次新Invocation/PID/Job。本轮无生产处置/主动模型/测试重放；cycle-20261009T1630.json及八份只读证据保留，任务镜像E盘；无重要新阶段结论，CURRENT不更新、例行记录不追加push。原collector/heartbeat继续，业务与collector截止今日08:30；整夜/30真实成员容量/完整PG与全writer冻结恢复仍未验。


01:00例行核对（现场01:00–01:02:56）：observer原r2/Invocation95565b7d/PID872681/SHA保持，94样本、最新00:59:48，无>450秒缺口/采集错误/host OOM，证据12412560字节。00:29:48–00:59:48六个完整5分钟样本入口200/匿名401、内部CH及个人超时/连接/落库错误0，个人身份/current精确绑定/8执行24等待DB3预算及edge双视图保持，无maintenance.pending。半小时没有personal_api完成或失败记录，累计仍172×200/1×499/9×502；Windows有界脱敏观察无新增上游错误，9000仍PID24744。不把无流量窗口称真实模型容量验收，无主动模型测试、切模型或重试。

01:02独立核对1025容器完整配置及启动代际、39运行、23业务对象结构/UUID/元数据行数、8公网入口/个人current/edge/backup20通过，范围不是全库checksum。CH原CID/image/17:49启动/PID930830、XMLe14fd07b及原metric UUID保持，Code241未清零累计7705/最后10-09 18:49:57未增，metric parts22/text_log20，无当前merge；cgroup max3492保持、OOM/oom_kill0，5秒探针CPU节流0/49，两轮末点间累计新增2个节流周期。currentQueryID诊断查询仍exit46，仅为版本诊断限制。六样本离散执行/等待/DB峰值0，PG最大14 idle/1 active、idle-in-transaction0、最长事务0.0秒。

六窗口MemAvailable最小8236556288字节，换入201页/换出0/OOM0，memory PSI全0、IO avg300 some/full0.15。即时空闲Docker43073187840（40.12GiB，储备线余量123514880字节、约117.8MiB）/cold271983030272（253.30GiB）/runtime34280910848/backup554074771456字节，继续暂停新build/发布/大归档，不清理历史。01:02只读LogPath元数据：当前运行容器当前日志300900607字节、数字轮转.1–.10合计320001242字节，比00:36合计减少1648934字节；该有界日志集合不等于磁盘增长，不能据此归因全部空间差额。匹配容器较大日志增量为edge3159157字节和api-agents-short2754065字节，未读正文，未扫全部历史。backup仍inactive/success/PID0/Job空、Invocation6508042bb54b49a5b26cd27a4a461796，timer今日02:58:03；只跟踪原计划的新Invocation/PID/Job，不开第二批。新增本地log_footprint.py仅单次只读元数据工具，不安装远端服务。本轮无生产处置/主动模型/测试重放；cycle-20261009T1700.json及八份只读证据保留，任务镜像E盘，CURRENT不更新、不追加push。原collector/heartbeat继续至08:30；整夜/真实30成员/完整PG与全writer冻结恢复仍未验。


01:30例行核对（现场01:31–01:32:37）：observer原r2/Invocation95565b7d/PID872681/SHA保持，100样本、最新01:29:48，无>450秒缺口/采集错误/host OOM，证据12640107字节。00:59:48–01:29:48六个完整5分钟样本入口200/匿名401、内部CH及个人超时/连接/落库错误0，个人身份/current精确绑定/8执行24等待DB3预算、edge双视图保持，无maintenance.pending。半小时没有personal_api完成或失败记录，累计仍172×200/1×499/9×502；Windows有界脱敏观察无新增错误，9000仍PID24744，不把无流量窗口称真实模型容量验收。01:32再度独立核对1025全部容器配置与启动代际、39运行、23业务对象UUID/结构/元数据行数、8公网入口/个人current/edge/backup20通过，不是全库checksum。

CH同CID/image/17:49启动/PID930830、XMLe14fd07b和原metric UUID保持，Code241未清零累计7705/最后10-09 18:49:57未增，metric parts23/text_log18，无当前merge；cgroup max3492保持、OOM/oom_kill0，5秒探针节流0/50，两轮探针末点间累计新增1个节流周期。currentQueryID诊断查询exit46仍是版本限制。六样本离散执行/等待/DB峰值0，PG14 idle/1 active、无idle-in-transaction、事务max0.0秒。MemAvailable六窗口最低8228126720字节，换入165页/换出0/OOM0，memory PSI0，IO avg300 some0.12/full0.09。

即时空闲Docker43061342208（40.10GiB，储备线余量111669248字节、约106.5MiB）/cold271975452672（253.30GiB）/runtime34280034304/backup554074771456字节，继续暂停新build/发布/大归档，不清理历史。只读当前运行容器LogPath及数字轮转.1–.10共增加9429140字节，主要匹配增量edge3618200、api-agents-short3084128、protocol-trusted2436352字节；当前文件310329747、轮转320001242字节。统计未读正文，不是全历史或完整磁盘增长归因。backup仍inactive/success/PID0/Job空、Invocation6508042bb54b49a5b26cd27a4a461796，timer今日02:58:03，无pending；只观察原计划批次。此次无生产处置/主动模型/测试重放，cycle-20261009T1730.json及八份证据保留，任务镜像E盘，CURRENT不更新、不追加push。原collector/heartbeat继续至08:30；完整PG/全writer冻结恢复/真实30人容量和剩余整夜仍未验。


02:00例行核对（现场02:00–02:01:40）：observer原r2/Invocation95565b7d/PID872681/SHA保持，106样本、最新01:59:48，无>450秒缺口/采集错误/host OOM，证据12867655字节。01:29:48–01:59:48六个完整5分钟样本入口200/匿名401、内部CH及个人超时/连接/落库错误0，个人身份/current精确绑定/8执行24等待DB3预算、edge双视图保持，无maintenance.pending。该半小时没有personal_api完成或失败记录，累计仍172×200/1×499/9×502；Windows有界脱敏观察无新增错误、9000仍PID24744，不把无流量窗口称真实模型容量验收。02:01独立核对1025全部容器配置及启动代际、39运行、23业务对象UUID/结构/元数据行数、8公网入口/个人current/edge/backup20通过，范围不是全库checksum。

CH同CID/image/17:49启动/PID930830、XMLe14fd07b和原metric UUID保持，Code241未清零累计7705/最后10-09 18:49:57未增，metric parts20/text_log19。即时捕获asynchronous_metric_log两part Horizontal合并，进度0.926、跟踪内存17855184字节；邻近只读查询无merge，是不同采样时刻，未重放合并或改设置。cgroup max3492保持、OOM/oom_kill0，5秒探针节流0/50，两轮探针末点间新增5个节流周期。currentQueryID诊断查询exit46仍为版本限制。六样本离散执行/等待/DB峰值0，PG14 idle/1 active、无idle-in-transaction、事务max0.0秒。MemAvailable窗口最小8111403008字节，换入294页/换出0/OOM0，memory PSI0，IO avg300 some/full0.13。

即时空闲Docker43069820928（40.11GiB，储备线余量120147968字节、约114.6MiB）/cold271960608768（253.28GiB）/runtime34279223296/backup554074771456字节，继续暂停新build/发布/大归档，不清理历史。当前运行容器LogPath及数字轮转.1–.10合计变化-10822884字节（当前299506737、轮转320001368）；api-agents-short增3035115、protocol-trusted增2398196字节，部分其他文件统计下降，不能把有界日志集合当磁盘整体增长归因。未读日志正文/未扫全部历史。backup仍inactive/success/PID0/Job空、Invocation6508042bb54b49a5b26cd27a4a461796，timer今日02:58:03，无pending；后继先观察原计划的新Invocation/PID/Job，活动时延后冲突核验，不能启动第二批。本轮无生产处置/主动模型/测试重放；cycle-20261009T1800.json及八份证据保留，任务镜像E盘，CURRENT不更新、不追加push。原collector/heartbeat继续至08:30，完整PG/全writer冻结恢复/真实30人容量和剩余整夜仍未验。

## 2026-10-10 02:30（Asia/Shanghai）例行续跑

核对时间：02:34–02:41（18:34–18:41Z）。原有限 observer 继续使用 Invocation `95565b7dce3e4b7db335aa756022a466`、PID `872681`、`watch.py` SHA `419fe2b09d12890f3f04ddad9cab9db50d4ed50a2a17766bf287f4e68f744c5b`。读回 112 samples，最新样本 `2026-10-09T18:29:48.875968Z`（北京时间 02:29:48），无缺口、采集错误或新增 host OOM；证据约 13.10MB。

02:00–02:30 对应六个完整 5 分钟窗口（17:59:48.875260Z–18:29:48.875968Z）：公网入口 200/匿名 401、个人 current 精确绑定及 8/24/DB3 预算、edge 双视图均保持；个人 API 本半小时无新完成/失败，累计仍 `172×200 / 1×499 / 9×502`。只读聚合查询返回空摘要；本机 Windows 9000 仍由 PID `24744` 监听；本轮没有主动模型、切模型或自动重试。自上次 observation 未发现新的脱敏上游事件。六窗口个人超时/连接/落库六类错误均 0，离散执行/等待/DB采样峰值均 0；PG 最大 14 idle/1 active，idle-in-transaction 0、最长事务 0.0 秒，采样峰值不替代真实区间峰值。

ClickHouse 只读核验 `verify_ch_metric_buffer_r2.py` 为 passed：1025 容器、39 running，原 CH CID/image/StartedAt/PID 与 XML SHA `e14fd07b4f175eccaab22c1dfde8d5bb08ea377fdfceb8828e06db7dd56643cd`、metric UUID `157524f1-02f8-4e4b-a5b2-5a9c0d0ce335` 保持；Code 241 未清零累计仍 `7705`、最后时间 `2026-10-09 10:49:57`（UTC，18:49:57 CST），本六窗口内部 Code241/`MEMORY_LIMIT_EXCEEDED`/`Cannot allocate memory` 均为 0，当前无 merge。cgroup `max=3492`、OOM/oom_kill=0；有界 5 秒压力探针节流增量 0/49 周期；与前轮探针末点之间累计新增 4/20083 节流周期，不能把短探针称整半小时零节流。`currentQueryID` 只读诊断仍返回版本限制 exit 46，未据此认定生产故障。

资源窗口最低 MemAvailable `8215011328` bytes；换入增量 250 页、换出 0、OOM 0；最新 memory PSI avg10/60/300 均 0、IO avg300 some/full 均 0.14。即时可用空间 `/var/lib/docker=43056664576` bytes（约 40.10 GiB，储备余量 106991616 bytes、约 102.0 MiB）、`/srv/smartbrain=34278363136`、`/srv/smartbrain-cold=271936655360`（约 253.26 GiB）、`/srv/smartbrain-backups=554074771456`；储备仍薄，继续停止新 build/部署/大归档，不 prune、删日志/parts/历史容器或迁移数据。当前运行容器 LogPath 与 `.1–.10` 轮转有界统计：当前日志 310099893、轮转 320001368 bytes；从 02:01:40 上轮到 02:35:15 本轮合计增加 `10593156` bytes，主要匹配增长为 smartbrain-edge-1 `4011789`、smartbrain-api-agents-short-ready-20261008-r1 `3488241`、smartbrain-protocol-trusted-r1 `2770506` bytes。额外相邻 14 秒只读复核的 +67932 bytes 单独保留，不能当半小时增长。未读取正文，不能据此归因整盘变化。

备份边界保持：`smartbrain-backup.service` 仍 inactive/success、PID/Job 空，旧 Invocation `6508042bb54b49a5b26cd27a4a461796` 不能代替今晚新批次；timer 仍等待 `2026-10-10 02:58:03 CST`，无 maintenance.pending。02:58 后只跟踪 timer 实际产生的新 Invocation/PID/Job、只读进度与终态，不启动第二批或做冲突变更。本轮无生产变更、业务重启、Key/OAuth/项目绑定修改或测试重放。

证据：`.artifacts/overnight-operations-20261009/cycle-20261009T1830.json`（SHA `71a9c536ad95f8eb22610f36d7f362f755b9c0a47fab89f2970a1665f13602aa`）、`cycle-windows-20261009T1830.json`、`observation-20261009T183439Z.json`、`natural-traffic-20261009T184016.json`、`ch-pressure-20261009T183509.json`、`ch-merge-space-20261009T183515Z.json`、`ch-metric-buffer-r2-verified-20261009T183454Z.json`、`docker-log-footprint-20261009T183515Z.json`、`windows-listener-20261009T1830.json`。CURRENT 不更新；原 collector 与 heartbeat 继续至 08:30，整夜趋势、完整 PG/全 writer 冻结恢复及真实 30 人容量仍未验收。

本轮本地只读 runner 参数/记录整理失败单独保留在 `local-runner-errors-20261009T1830.json`：误把 `--help` 当日期导致 SQL 拒绝、窗口摘要先假定错误字段结构、cycle 构建缺本地时间戳快照；均按实际源/证据修正后通过，不混入 collector collection_errors，也不认定为生产故障。额外 CH/LogPath 读取未改生产配置、服务或数据；无生产处置。

02:47 本地独立审阅：cycle SHA、9份引用证据、六窗口与累计值、短探针与累计节流、LogPath区间增量、Docker储备余量及备份边界对应通过。deb4仍为既有 dirty 工作树 `codex/project-memory-no-adapter`，旧修改保留；本轮只追加本任务与 artifacts，不操作正式交付分支或远端。


## 2026-10-10 03:00（Asia/Shanghai）原定时备份活动中续跑

核对时间：03:00–03:07（19:00–19:07Z）。observer 原 r2 Invocation `95565b7dce3e4b7db335aa756022a466`、PID `872681`、watch.py SHA `419fe2b09d12890f3f04ddad9cab9db50d4ed50a2a17766bf287f4e68f744c5b` 保持；读回 118 samples，最新 `2026-10-09T18:59:48.876632Z`，无缺口、采集错误或 host OOM。18:29:48–18:59:48Z 六个完整窗口入口/匿名鉴权、个人 current/8/24/DB3、edge 双视图通过；个人半小时聚合为空，累计仍 `172×200 / 1×499 / 9×502`，六窗口代理超时/连接/落库错误和 CH 错误均 0，离散执行/等待/DB采样峰值均0；Windows 9000 仍 PID `24744`，无主动模型或重试。PG 采样最高 14 idle/2 active，最长事务 `98.925971s` 出现在备份启动交界；无 idle-in-transaction/lock 等待，03:03:11 后续只读聚合为 14 idle/1诊断 active、事务 max0.0s，无 pg_dump 类当前会话；该采样未提供之前事务的历史来源，不能归为网关或已证实 pg_dump 长事务。

02:58:09 CST 原 timer 自然启动当前唯一备份：Invocation `4250cdc681a24199aa79d1da71002515`、PID `2471121`、Job `9292938`，同一 partial `.20261009T185810Z.2471121.partial`，进程 bash→sudo→tar→sh→gzip。03:07 仍 `ActiveState=activating/SubState=start`、ExitTimestamp 为空；`Result=success/ExecMainStatus=0` 是运行中字段，不能视为备份成功。partial 内 `clickhouse.tar.gz` 从 `363593728` 到 `7734558720` bytes（增加 `7370964992` bytes），postgres.dump `1084737955` bytes；备份盘可用空间降至 `534200926208` bytes。未启动第二批、未做 restore 或完整锁/清单/哈希核验；备份活动期间延后会与其争用的维护核验。

备份活动与 CH cgroup 压力在时间上重叠：18:59:48Z 采样 `memory.current=2308382720`、`memory.events max=3492`；03:04:48Z collector 采样为 `3693170688/max=9939`；03:07 直接只读为 `3850162176/max=9939`、`memory.peak=4294971392`（cgroup 生命周期峰值，不是已经证明的本批新峰值）、OOM/oom_kill 仍 0。memory.stat 03:07 选定字段显示 file `2929532928`、inactive_file `2862391296`、anon `836788224`；memory PSI avg10/60/300 为 0，但 IO PSI avg300 some/full `8.74/8.62`，说明存在 IO 压力。Code241 累计仍 `7705`、最后时间 `2026-10-09 10:49:57`，当前有界查询未见活动 merge。该时间重叠支持缓存/归档读取压力等假设，未确认唯一根因；不 drop cache、停备份、改 CH 配置、重启或扩大内存。

当前即时空间：Docker `/var/lib/docker=43053498368` bytes（约 40.10 GiB，储备余量 103825408 bytes、约 99.0 MiB）、`/srv/smartbrain=34277462016`、cold `272104935424`、backup `534200926208`；继续停止 build/部署/大归档，不 prune/删日志/parts/历史容器或迁移数据。备份自然活动是本轮唯一生产运行变化；无业务发布、DDL、服务重启、Key/OAuth/项目绑定修改。采样中 39 个当前运行容器的身份/完整配置 hash/启动代际与前轮保持；full1025/23业务对象/metric UUID/backup20 独立复核延后，旧通过不代替本轮重新核对。当前running39，原个人与 CH CID/image/StartedAt保持，XML实际SHA e14fd07b保持。

证据：`.artifacts/overnight-operations-20261009/cycle-20261009T1900.json`（SHA `98a3a588fc28ae24f20241601698da52f1a0e613d37fe31243044afb30f08702`）、`observation-20261009T190047Z.json`、`cycle-windows-20261009T1900.json`、`natural-traffic-20261009T190137.json`、`ch-pressure-20261009T190309.json`、`ch-merge-space-20261009T190315Z.json`、`backup-ch-memory-20261009T190459Z.json`、`backup-ch-memory-20261009T190624Z.json`、`backup-ch-memory-20261009T190723Z.json`、`original-backup-20261009T190220Z.json`、`original-backup-20261009T190616Z.json`、`original-backup-20261009T190722Z.json`、`pg-backup-window-20261009T190311Z.json`、`backup-memory-diagnosis-20261009T1900.json`。原 collector 继续至 08:30；整夜错误分类、备份终态、完整 PG/全 writer 冻结恢复及真实 30 人容量仍未验收。

03:10 记录补充：03:00六窗口 MemAvailable 最低8259117056字节，swap-in增178页/swap-out0/host OOM0；主机IO PSI avg300 some0.78/full0.73，CH cgroup03:04 IO PSI avg300 some13.34/full13.15、03:07为8.74/8.62，不能写压力已消失。5秒CH探针节流0/48，两轮探针末点之间0/16645。当前运行容器LogPath有界总量比前轮减少1183961字节（当前308915915/轮转320001385），不是全部磁盘增量归因。本轮只读检查无runner错误，不争备份/维护锁、不push；旧dirty修改保留。


## 2026-10-10 03:30（Asia/Shanghai）备份仍活动，新增换页观察

核对时间：03:30–03:32（19:30–19:32Z）。observer 原 r2 Invocation `95565b7dce3e4b7db335aa756022a466`、PID `872681`、SHA `419fe2b09d12890f3f04ddad9cab9db50d4ed50a2a17766bf287f4e68f744c5b` 保持；124 samples，最新 `2026-10-09T19:29:48.877328Z`，无缺口、采集错误或 host OOM。19:00–19:30Z 六窗口公网/匿名鉴权、个人 current/8/24/DB3、edge 双视图和代理错误均正常；无 personal_api 新完成/失败，累计仍 `172×200 / 1×499 / 9×502`，Windows 9000 PID `24744` 保持。六窗口内部 CH Code241/内存错误均 0。

同一备份 Invocation `4250cdc681a24199aa79d1da71002515`、PID `2471121`、Job `9292938` 仍 `activating/start`，partial `.20261009T185810Z.2471121.partial` 继续增长：`clickhouse.tar.gz=9078287763` bytes，`models.tar.gz=3785097216` bytes，ExitTimestamp 仍为空；不能把运行中 `Result=success/ExecMainStatus=0` 视为终态成功，未启动第二批、未 restore 或争用完整维护锁。

03:00→03:30 主机 `SwapFree` 从 `309014528` 降到 `23400448` bytes（减少 `285614080` bytes，约 272 MiB），`pswpin +16704` 页、`pswpout +81674` 页、OOM 0；MemAvailable 仍约 8.19 GiB。当前运行容器 cgroup swap 快照合计增加约 `284839936` bytes，其中 CH 约 `97144832` bytes；该集合不覆盖所有主机进程/瞬态，不能据此归因全部 swap 或认定由备份/CH单独造成。CH `memory.events max=9939`（自03:04保持）、OOM/oom_kill=0、Code241累计7705不变，`memory PSI=0`；03:30 直接 IO PSI avg300 some/full 约 `1.95/1.95`，仍有 IO 压力但较03:07降低。CH memory.current约 3.50 GiB，file/inactive_file占多数；原因仍未确认，不 drop cache、停备份、改 CH、重启或扩内存。

03:29:48 采样可用空间：Docker `/var/lib/docker=43045486592` bytes（储备余量 `95813632` bytes，约 91.4 MiB）、`/srv/smartbrain=34276171776`、backup `/srv/smartbrain-backups=527306653696`、cold `/srv/smartbrain-cold=272100233216`；继续停止 build/部署/大归档，不 prune、删日志/parts/历史容器或迁移数据。采样范围内 39 当前运行容器身份/配置代际无变化；full1025/23业务对象/metric UUID/backup20 复核待备份终态后进行。本轮已观察到的自然运行变化是原备份继续执行，主动生产变更 0。

证据：`.artifacts/overnight-operations-20261009/cycle-20261009T1930.json`（SHA `e0b6196c27a495437624cbb0fc767fce1bd64ed15bbc50c12452425c58a120a4`）、`observation-20261009T193044Z.json`、`cycle-windows-20261009T1930.json`、`natural-traffic-20261009T193138.json`、`backup-ch-memory-20261009T193056Z.json`、`original-backup-20261009T193044Z.json`、`ch-pressure-20261009T193057.json`、`ch-merge-space-20261009T193103Z.json`、`docker-log-footprint-20261009T193057Z.json`、`swap-window-20261009T1930.json`、`swap-followup-20261009T193246Z.json`。继续只读跟踪同批次，整夜备份终态、完整 PG/全 writer 冻结恢复和真实 30 人容量仍未验收。

03:32后继（19:29:48→19:32:46Z）：主机swap-in再增49页、swap-out增0、OOM0，SwapFree23703552字节（+303104）、MemAvailable8753016832；只证明这一短后继没有新增换出，不称全部压力消除。六窗口MemAvailable最低8451432448、PG14idle/1诊断active、无idle-in-transaction/Lock、事务max0.0s，离散执行/等待/DB峰值0。39当前运行容器与上一样本身份/完整配置hash/代际核对通过，范围不含停止的历史容器。5秒CH节流0/50，与前轮末点0/16342；LogPath有界增8754026字节（当前317669941/轮转320001385），未归因整个磁盘变化。记录组装的本地FileNotFound/Assert失败按实际引用修正后保留在local-runner-errors-20261009T1930.json，与collector采集错误0分开；没有额外生产动作。

## 2026-10-10 04:00（Asia/Shanghai）原定时备份自然完成

核对时间：04:02–04:10（20:02–20:10Z）。原 observer r2 Invocation `95565b7dce3e4b7db335aa756022a466`、PID `872681`、watch SHA `419fe2b09d12890f3f04ddad9cab9db50d4ed50a2a17766bf287f4e68f744c5b` 保持。130 samples，最新 `2026-10-09T19:59:48.877905Z`，无缺口、采集错误或新增 host OOM；证据总量 `13775099` bytes，尚未到 16MiB 上限。03:29:48–03:59:48 六窗口入口200/匿名401、个人 current 精确绑定及8/24/DB3、edge双视图保持，代理超时/连接/落库及内部CH三类错误均0。personal_api 无新自然完成/失败，累计仍 `172×200 / 1×499 / 9×502`；Windows脱敏尾部未见新上游事件，04:10监听9000仍PID24744。不将无流量区间称真实模型或30人容量验收。

原定时备份唯一批次 Invocation `4250cdc681a24199aa79d1da71002515`，02:58:09开始、03:58:46自然结束，现 inactive/dead、Result=success、ExecMainStatus=0、MainPID/ControlPID=0、Job空；ExecMainCode=1表示CLD_EXITED，不是exit1。final `/srv/smartbrain-backups/backups/20261009T185810Z` 存在，backup-state `status=complete / consistency=online / backup_id=20261009T185810Z`；无对应partial/failed。SHA256SUMS有36项，全部目标文件存在，清单SHA `913a715be5c01880246a552000c543cd34ab9ae669c0bbae2d30de08569d103c`、backup-state SHA `5ab601df61318346eac0d7db43f04fa01a0648729ceb851f278eb99b968a39d7`。只在确切原Invocation的有界journal内分类，36项全部OK、FAILED0、完成标记1；未保存日志正文，200行尾部不代表整批历史日志完全覆盖。

独立有界小文件SHA核验31项、总读取 `28220580` bytes（约26.91MiB，预算32MiB）全部一致，文件inode/size/mtime前后保持；零字节 `supabase-storage-files.tsv` 与标准空文件SHA一致，是首版“全部非空”断言过严而非生产异常。5个大payload本轮不另做全量重hash：clickhouse.tar.gz `9078287763`、models.tar.gz `8005223169`、postgres.dump `1084737955`、material-uploads.tar.gz `1961415527`、api-tmp.tar.gz `236834357` bytes；原备份程序36项自检证据与本轮独立31项核验分开记录。backup-state根身份dev/inode未单独复核；没有启动第二批、停止原备份或重放restore。timer正常waiting，下一次为10-11 02:39:30 CST，无maintenance.pending。该online备份自然完成不等于完整PG/全writer冻结恢复验收。

备份终态后04:03完整只读验证恢复：1025全部容器完整配置与启动代际、39运行、23业务对象UUID/结构/元数据行数、原metric UUID、实际XML SHA e14fd07b、8公网入口/个人current/edge双视图与backup20登记通过；原CH PID930830/StartedAt09:49:40Z保持，未自动更名。Code241累计仍7705/最后UTC10-09 10:49:57；metric parts21/text_log17，当前有界查询无merge。CH max=9939自03:04保持、OOM/oom_kill=0，04:03 memory.current `3796365312` bytes（约3.54GiB）、file/inactive_file占多数，IO PSI avg300 some/full 1.83/1.82、memory PSI0；不将压力或缓存归因称已确认。5秒CPU节流0/47，两轮探针末点之间0/19073。currentQueryID诊断exit46仍为既有版本限制。

六窗口换入940页、换出0、OOM0，SwapFree从23400448到28078080 bytes（增加4677632），MemAvailable最低8431329280；只说明此半小时无新增换出，不能改写03:00–03:30已有新增换页。PG14 idle/1诊断active、无idle-in-transaction，最长事务0.0秒；离散执行/等待/DB峰值0。04:03即时空间Docker `43033038848` bytes（40.078GiB，40GiB储备余量83365888 bytes、约79.5MiB）、runtime `34266583040`、backup `522625470464`（486.73GiB）、cold `272099102720`（253.41GiB）；仍停止build/部署/大归档，不删历史、parts、日志或迁移数据。当前运行容器LogPath及.1–.10轮转有界增长10251085 bytes（当前327921026/轮转320001385），较大增量edge3888262/api-agents-short3350914/protocol-trusted2722390，不能归因整个磁盘变化。

证据：`.artifacts/overnight-operations-20261009/cycle-20261009T2000.json`（SHA `947669daf83903551335337c5e2347afc1e14ed5bdf69889cfaca82141558b92`），及其10份具名/hash引用；重点 `completed-backup-metadata-20261009T200713Z.json`、`original-backup-20261009T200232Z.json`、`ch-metric-buffer-r2-verified-20261009T200323Z.json`。本地runner的过严空文件断言、不存在的历史路径搜索及无效本地patch尝试另记 `local-runner-errors-20261009T2000.json`，与collector采集错误0分开。任务/CURRENT镜像E盘，旧dirty修改保留、不切分支或整体提交。本轮生产处置/业务重启/Key/OAuth/项目绑定修改/主动模型/测试重放均0；原collector与heartbeat继续至08:30硬截止，剩余整夜、完整恢复和真实30人容量仍未验收。


## 2026-10-10 04:30（Asia/Shanghai）备份完成后例行续跑

核对时间：04:30:35–04:30:58。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；136样本截至04:29:48，无缺口/采集错误/新host OOM，证据14000672 bytes。03:59:48–04:29:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3及edge双视图保持，代理六类及CH内部三类错误均0。自然personal_api无新完成/失败，累计172×200/1×499/9×502；Windows有界脱敏上游无新增事件，9000仍PID24744；不作为真实模型或30人容量验收。

04:30:55完整只读验证1025容器配置与代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH仍原CID/image/StartedAt/PID930830；Code241累计7705/最后UTC10-09 10:49:57未增，cgroup max9939自03:04保持、OOM/oom_kill0，当前有界查询无merge、metric parts20/text_log17。5秒CPU节流0/48，前后两探针末点间0/16368；末点memory.current=3786493952 bytes，不能说全部内存压力解决。currentQueryID诊断exit46仍是既有版本限制。六窗口MemAvailable最低8390307840，换入1213页/换出0/OOM0，SwapFree增加5328896至33406976 bytes；主机memory PSI0、IO avg300 some0.14/full0.13。PG14 idle/1诊断active，无idle-in-transaction、事务max0.0s；离散执行/等待/DB采样峰0。

04:30:55即时空间Docker43022823424 bytes（40.068GiB，储备余量73150464 bytes、约69.8MiB）/runtime34265780224/backup522625470464/cold272113623040。继续停止build/部署/大归档，不清理历史或迁数据。当前运行容器LogPath及.1–.10有界增8717143 bytes（当前336638169/轮转320001385）；主要edge3341282、api-agents-short2875111、protocol-trusted2226755，未读正文，不能归因整个磁盘变化。

同一原备份4250cdc6仍inactive/success/exit0、PID0/Job空，ExitTimestamp03:58:46；timer next10-11 02:39:30，无pending。04:00原批完整清单自检与31项独立小文件SHA结论保留并明确为前轮核验，本轮不重hash或restore、不启动第二批。证据cycle-20261009T2030.json（SHA 4e5b385f2bb039315f9099028cc6a9093ff4245e8afc6565019ee6d56ad7fac4）及8份具名hash引用保留。本轮生产处置/业务重启/主动模型/测试重放0；任务镜像E盘，CURRENT无重要变化不更新，旧dirty树保留、不切分支/整体提交/push。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复、真实30人容量仍未验收。


## 2026-10-10 05:00（Asia/Shanghai）例行续跑

核对时间：05:00:44–05:01:27。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；142样本截至04:59:48，无缺口/采集错误/新host OOM，证据14226263 bytes。04:29:48–04:59:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

05:01:24完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0。05:01:21 pressure快照见metric_log 1个活动merge（压缩输入1505127 bytes）；05:01:24完整核验独立快照已无merge、metric parts19/text_log17。两者是不同时间点，不推及整个区间。5秒CPU节流0/50，跨两探针末点0/18132；末点memory.current=3844042752 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8372461568 bytes，换入405页/换出0/OOM0，SwapFree增量1929216至35336192 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。05:01:24即时空间Docker43041153024（40.085GiB，储备余量91480064 bytes约87.2MiB）/runtime34264965120/backup522625470464/cold272065392640；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化-20354898 bytes（当前316283051/轮转320001605）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261009T2100.json（SHA ff94e1f46778c8c0da50927e9989a0cc778920e2dac6f5c882f265fa637ad68a）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。


## 2026-10-10 05:30（Asia/Shanghai）例行续跑

核对时间：05:30:38–05:33:11。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；148样本截至05:29:48，无缺口/采集错误/新host OOM，证据14451844 bytes。04:59:48–05:29:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

05:32:33完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0，05:32:33完整核验快照metric parts20/text_log19、merge=0；另05:32:30 pressure快照merge=0。两者是不同时间点，不推及整个区间。5秒CPU节流0/50，跨两探针末点1/18529；末点memory.current=3948023808 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8562638848 bytes，换入409页/换出0/OOM0，SwapFree增量2064384至37400576 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。05:32:33即时空间Docker43028561920（40.073GiB，储备余量78888960 bytes约75.2MiB）/runtime34264166400/backup522625470464/cold271981469696；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化9860036 bytes（当前326143087/轮转320001605）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261009T2130.json（SHA 3c5b930c74118b82bc2d45cdb8dec4c89809974d13f082b4afe969a397a126e7）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。

本轮本地runner目录日期曾误写20260910；11条本地命令未找到该目录，脚本未执行、未触及生产。已纠正为20261009并完成本轮核验，失败另存local-runner-errors-20261009T2130.json，与collector采集错误0分开。该文件SHA d45ece9141330b1e8caf1f4005e1f05c71b070d7d248e38a2c0264562a238602。


## 2026-10-10 06:00（Asia/Shanghai）例行续跑

核对时间：06:00:35–06:01:16。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；154样本截至05:59:48，无缺口/采集错误/新host OOM，证据14676970 bytes。05:29:48–05:59:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

06:00:51完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0，06:00:51完整核验快照metric parts20/text_log17、merge=0；另06:00:48 pressure快照merge=0。两者是不同时间点，不推及整个区间。5秒CPU节流0/49，跨两探针末点1/16858；末点memory.current=3880873984 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8374321152 bytes，换入248页/换出0/OOM0，SwapFree增量1273856至38674432 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。06:00:51即时空间Docker43017039872（40.063GiB，储备余量67366912 bytes约64.2MiB）/runtime34263531520/backup522625470464/cold272023883776；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化8928746 bytes（当前335071833/轮转320001605）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261009T2200.json（SHA 1a3ea13941bc5dc389bd6156e54cfff624dae09c3b929ba700ce5b7e627a71b4）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。

本轮本地记录脚本时间范围替换的apply_patch首次因整行匹配失败被拒，未写入、未调用生产；随后仅修正本地记录工具以取各证据及pressure末点的最晚时间，Python编译与本轮时间值核对通过。失败另记local-runner-errors-20261009T2200.json，SHA cf5f992b2505fb4fcd7839f44d43a0827b709fb1057c01a4516ddb34f1c84395，与collector采集错误0分开。


## 2026-10-10 06:30（Asia/Shanghai）例行续跑

核对时间：06:30:35–06:31:01。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；160样本截至06:29:48，无缺口/采集错误/新host OOM，证据14901863 bytes。05:59:48–06:29:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

06:30:48完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0，06:30:48完整核验快照metric parts23/text_log19、merge=0；另06:30:45 pressure快照merge=0。两者是不同时间点，不推及整个区间。5秒CPU节流0/50，跨两探针末点4/17834；末点memory.current=3917475840 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8361525248 bytes，换入427页/换出0/OOM0，SwapFree增量1921024至40595456 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。06:30:48即时空间Docker43005263872（40.052GiB，储备余量55590912 bytes约53.0MiB）/runtime34262716416/backup522625470464/cold272002953216；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化9510776 bytes（当前344582609/轮转320001605）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261009T2230.json（SHA 936a8164d42eb3f917447930dc639ffaa877247f670e5ac9b9314167ebd326ba）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。


## 2026-10-10 07:00（Asia/Shanghai）例行续跑

核对时间：07:00:36–07:01:09。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；166样本截至06:59:48，无缺口/采集错误/新host OOM，证据15126521 bytes。06:29:48–06:59:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

07:00:53完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0，07:00:53完整核验快照metric parts20/text_log18、merge=0；另07:00:50 pressure快照merge=0。两者是不同时间点，不推及整个区间。5秒CPU节流0/50，跨两探针末点4/17898；末点memory.current=3924512768 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8362426368 bytes，换入422页/换出0/OOM0，SwapFree增量1847296至42442752 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。07:00:53即时空间Docker43003392000（40.050GiB，储备余量53719040 bytes约51.2MiB）/runtime34261913600/backup522625470464/cold271997009920；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化-474361 bytes（当前344108298/轮转320001555）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261009T2300.json（SHA 7b7cb5dcb8d6fcd399b3f9d2653126d6325db351a6fc375e97f6b06aad12ff1f）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。


## 2026-10-10 07:30（Asia/Shanghai）例行续跑

核对时间：07:30:45–07:31:16。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；172样本截至07:29:48，无缺口/采集错误/新host OOM，证据15350944 bytes。06:59:48–07:29:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

07:31:13完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0，07:31:13完整核验快照metric parts18/text_log19、merge=0；另07:31:10 pressure快照merge=1。两者是不同时间点，不推及整个区间。5秒CPU节流0/50，跨两探针末点6/18058；末点memory.current=3922821120 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8532000768 bytes，换入891页/换出0/OOM0，SwapFree增量3805184至46247936 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。07:31:13即时空间Docker43011444736（40.058GiB，储备余量61771776 bytes约58.9MiB）/runtime34261110784/backup522625470464/cold271993753600；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化-10461204 bytes（当前333647032/轮转320001617）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261009T2330.json（SHA b21ee8481402a9ddd8ff54dcb36be0da40bdfe8c5cad392fa7b826f61142101b）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。

本轮本地finalize提前于压力/窗口证据采集调用，被fresh evidence断言拒绝，尚未生成cycle或追加任务；补齐本轮只读采集后原断言通过。失败单独保存local-runner-errors-20261009T2330.json，SHA ba5d31ce9c6821b6d76c07e36db6f21eddc4926e5558fad151c36403dd0126e9，无生产变更，与collector采集错误0分开。


## 2026-10-10 08:00（Asia/Shanghai）例行续跑

核对时间：08:00:46–08:01:14。原collector Invocation95565b7d/PID872681/SHA419fe2b0保持；178样本截至07:59:48，无缺口/采集错误/新host OOM，证据15575617 bytes。07:29:48–07:59:48六窗口入口200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图保持；个人六类/CH内部三类错误均0，自然personal_api无新完成/失败，累计172×200/1×499/9×502，Windows有界脱敏事件无新增，9000仍PID24744。无流量区间不作为真实模型或30人容量验收。

08:01:00完整只读核验1025容器配置代际、39运行、23业务对象结构/UUID/元数据行数、原metric UUID/实际XMLe14fd07b、8公网/个人/edge/backup20通过。CH原CID/image/StartedAt/PID930830保持，Code241累计7705/最后UTC10-09 10:49:57未增；max9939自03:04保持、OOM/oom_kill0，08:01:00完整核验快照metric parts20/text_log17、merge=0；另08:00:58 pressure快照merge=0。两者是不同时间点，不推及整个区间。5秒CPU节流0/50，跨两探针末点5/17738；末点memory.current=3972575232 bytes，仍不称压力全部消失。currentQueryID诊断exit46为既有版本限制。

六窗口MemAvailable最低8382017536 bytes，换入121页/换出0/OOM0，SwapFree增量606208至46854144 bytes；PG采样idle14/active1、idle-in-transaction0、最长事务0.0秒；离散执行/等待/DB峰值0/0/0。08:01:00即时空间Docker42999644160（40.047GiB，储备余量49971200 bytes约47.7MiB）/runtime34260287488/backup522625470464/cold271965597696；继续停止build/部署/大归档，不删历史/日志/parts或迁数据。当前运行容器LogPath及.1–.10有界变化9499827 bytes（当前343146859/轮转320001617）；未读正文，下降或增长不等于完整磁盘归因。

原备份4250cdc6仍inactive/success/exit0、PID0/Job空、03:58:46终态，timer next10-11 02:39:30，无pending；04:07已有36项原程序自检/31独立小文件SHA证据作为历史核验引用，本轮不重hash、不restore、不启动第二批。证据cycle-20261010T0000.json（SHA 71fabfa88f0f37503609960cc88b9a6db2675945e029e0822c680c15e3d4218b）及8份具名hash引用，本轮所有只读runner成功。任务镜像E盘，CURRENT无重要变化不更新；生产处置/业务重启/主动模型/测试重放0，不切分支/整体提交/push、旧dirty修改保留。原collector与heartbeat继续至08:30硬截止；剩余整夜、完整PG/全writer冻结恢复及真实30人容量仍未验收。


## 2026-10-10 08:38 早间收尾（业务授权到期）

- 08:30硬截止后仅执行终态核验、报告和文档镜像；没有新生产变更、重启、测试重放、Key/OAuth/项目绑定修改或第二批备份。原r2 collector自然到期，184样本覆盖17:22:44–08:29:48 CST，间隔缺口/collection_errors/host OOM增量均为0；截止前最后样本距deadline约11.116秒。systemd observer已 not-found/inactive/dead，旧PID872681与确切watch进程不存在。
- 整夜只读聚合（首样本前5分钟回溯17:17:44 CST至08:30）为172×200、1×499、9×502；8条502按秒对应capacity/server_is_overloaded，1条902秒对应request_timeout/stream_incomplete；没有剩余未归因的502。499具体取消原因未知，失败均不标完成且usage未知。
- 实际处置仅17:49:40 CST一次受控CH短停/启动（pool2/ratio1/阈值1）和18:50 CST表级64KiB buffer配置重载；原CH身份/PID/XML e14fd07b/metric UUID保持。发布后所有完整采样窗口无新增Code241；7705未清零，属于17:49 CH启动世代且发生在18:50 buffer重载前；发布后完整窗口未新增。备份期间CH cgroup max从02:59:48的3492增至约03:03:10的9939，OOM/oom_kill=0；新增换页和IO压力如实保留。
- 原备份Invocation4250cdc6于03:58:46 CST自然success/exit0，final20261009T185810Z、36项原自检及31项独立小文件hash一致；5大payload独立全量hash、备份根身份及完整PG/全writer冻结恢复未验。磁盘门槛仍薄，未做清理或迁移。
- 心跳10-10-08-30已用automation_update暂停，名称/完整原提示文本已UTF-8恢复并读回，验证文件为 heartbeat-paused-verified-correct.json；先前乱码版本保留为编码错误证据，未作为事实使用。早间报告见 docs/ops/overnight-operations-20261009.md。详细聚合见 night-summary-20261010T003720Z.json。旧dirty源码与历史记录保留，不整体提交/push；本条需镜像到E盘。


08:49最终收尾补证：全段只读SQL已确认17:50:36 CST/18900ms，与Windows同秒17:50:36.434/18867ms的capacity/server_is_overloaded相差33ms，最终9×502全部分类为8capacity+1上游断流。无新增样本；最终总数仍184（once1/r1两条/r2 181），末采样至deadline前11.115814秒未采样。7705为仍活动17:49 CH世代在18:50缓冲重载前的累计、未清零。PG02:59:48 active事务98.925971秒已补报告，来源未独立确认，不把整夜事务叫0秒。collector空间首末字节增量Docker+72560640/runtime-48332800/backups-31449300992/cold+1793531904，日志有界集合净增50248569，不作全盘归因。原observer source/samples/runs独立SHA与无PID终态见original-observer-evidence-final.json；StandardOutput追加文件，journal Invocation查询零条不作为终态证明。本地编码/路径/脚本错误另保留local-runner-errors-20261010T0030-final.json。所有本次只读与文档runner终态，未执行新的生产变更。
