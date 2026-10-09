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
