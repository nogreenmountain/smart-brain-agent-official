# 智慧大脑夜间运维早间报告

任务：overnight-operations-20261009。核对时间：2026-10-10 08:30–08:46（Asia/Shanghai）。本晚业务处置授权已在08:30结束；此后只核验原任务终态、汇总证据、写报告并暂停心跳。

## 结论与实际处置

样本内入口和个人网关身份保持，未发现新的主机OOM或个人代理超时/连接/落库失败类别。18:50宽表缓冲修复后，包括最初两窗口的全部163个完整发布后窗口的有界ClickHouse内部日志分类均没有新增Code241；当前启动世代的system.errors计数仍为7705，最后时间为10-09 18:49:57 CST。原定时online备份于03:58:46自然成功。磁盘储备仍薄，备份期间有新增换页与CH cgroup max事件，不能称所有资源或恢复能力通过。

本晚仅执行两次已授权生产处置，具体方案、自审与验收保留在原发布记录：

| 时间（北京时间） | 已执行动作 | 核验结果与边界 |
|---|---|---|
| 10-09 17:49:40 | CH后台pool2/ratio1及三个阈值1；对确切原CH容器短停/启动一次 | 原CID/image保持，新StartedAt为09:49:40.337495161Z/PID930830；其他业务容器没有重启。局部CPU/parts改善后仍有Code241 |
| 10-09 18:49:58–18:50:00 | system.metric_log表级max_compress_block_size=65536、原inode XML同步及SYSTEM RELOAD CONFIG | 无第二次生产CH重启，原metric UUID保持；同版本r3/r4实际候选、重启及测试回退验证已通过，生产回退未执行 |

当前宿主/实际XML SHA为e14fd07b4f175eccaab22c1dfde8d5bb08ea377fdfceb8828e06db7dd56643cd，metric UUID为157524f1-02f8-4e4b-a5b2-5a9c0d0ce335。18:51及08:31:32独立复核1025容器完整配置/启动代际、39运行、23业务对象UUID/结构/元数据行数、8公网入口、个人current绑定、edge双视图和backup20登记通过。这是元数据与身份核验，不是全库checksum。

本次运维未执行业务数据写入；生产DDL仅上述目标表设置。无主动模型批次、Key签发/撤销、OAuth或项目Key绑定修改、历史删除或业务API/个人/edge重启。隔离候选和已终态发布没有重放，adapter/Monitor/Langfuse/reconcile保持原停用范围。

## Collector覆盖与到期终态

总184条样本，包括once1条、r1两条与r2共181条；主机/入口现场覆盖10-09 17:22:44.497599至10-10 08:29:48.884186 CST。相邻最大间隔300.000406秒，无大于450秒的缺口；database窗口连续，collector collection_errors为空。早段r1没有CH内部err.log分类，r2自17:29:48首个实际样本补256KiB尾部。不能将184条全部叫r2，或把r1当完整CH内部错误覆盖。

r2原Invocation为95565b7dce3e4b7db335aa756022a466、历史PID872681，watch.py SHA保持419fe2b09d12890f3f04ddad9cab9db50d4ed50a2a17766bf287f4e68f744c5b。runs.jsonl记录在2026-10-10T00:30:00.000125Z以reason=deadline自然退出，本运行samples_this_run=181。08:37独立检查systemd为LoadState=not-found/inactive/dead/MainPID0，旧PID及确切watch.py进程不存在，无需停止或重建observer。

末样本到08:30硬截止前尚有11.115814秒，没有下一条主机/入口样本；自然请求SQL另补到08:30，没有新增完成记录。此边界不能写成连续已观察。sample文件6331458 bytes，SHA为5a88bf6b4752adcebbfb0a9b1ecde88102420d065966722584b3d7b76c9a51dd；08:30观察时证据目录15800062 bytes，后继只读核验输出保存后08:42目录15820088 bytes，均低于16MiB。

全部184份样本的4项HTTP检查都符合login/ready200、匿名模型/records401；personal身份/current精确绑定、edge宿主与实际挂载SHA c22e68d972aeb997dbf5328dd00ca1de968fabe7455e4b8eb23037d28ed78626保持。8执行/24等待/DB3预算不变，离散采样峰值为1执行/0等待/DB0；即时独立核验曾见DB1，不代表真实区间峰值或30成员容量。

原baseline故意保留CH旧启动身份，177条container_changed:smartbrain-clickhouse-1对应17:49受控变更，未重建baseline掩盖。其他运行容器身份与完整配置指纹保持；最终1025全容器复核范围另见验收证据。

## 自然流量与Windows错误对应

业务聚合按完成时间读取personal_api，实际统计范围为10-09 17:17:44.497599至10-10 08:30 CST，包含首个现场样本前5分钟回溯。只读SQL有statement5秒/lock2秒上限，仅输出模型/状态/耗时/完整与用量标记等聚合：

| 模型 | 200 | 499 | 502 | 成功最长耗时 |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 32 | 0 | 3 | 74260ms |
| gpt-6-sol | 140 | 1 | 6 | 140030ms |
| 合计 | 172 | 1 | 9 | 140030ms |

172条200全部content_complete且usage_missing=false；10条失败/取消保持不完整及未知用量。499完成于17:20:31 CST、3239ms，按客户端取消分类，具体取消原因未独立确认。最后含自然完成的collector窗口为23:49:48–23:54:48，之后无新完成流量，不把空流量区间当真实模型验收。

9条502已逐秒核对Windows脱敏事件：

| 完成时间（北京时间10-09） | 网关耗时ms | 同秒Windows耗时ms | 类别 |
|---|---:|---:|---|
| 17:29:41 | 14784 | 14760 | HTTP200内failed/capacity/server_is_overloaded |
| 17:45:37 | 902086 | 902061 | request_timeout/stream_incomplete |
| 17:50:36 | 18900 | 18867 | HTTP200内failed/capacity/server_is_overloaded |
| 19:45:18 | 24453 | 24419 | HTTP200内failed/capacity/server_is_overloaded |
| 20:06:37 | 35118 | 35108 | HTTP200内failed/capacity/server_is_overloaded |
| 20:08:37 | 35499 | 35463 | HTTP200内failed/capacity/server_is_overloaded |
| 22:42:16 | 46842 | 46835 | HTTP200内failed/capacity/server_is_overloaded |
| 22:55:01 | 28573 | 28540 | HTTP200内failed/capacity/server_is_overloaded |
| 22:59:50 | 24764 | 24714 | HTTP200内failed/capacity/server_is_overloaded |

最终为8条capacity和1条约902秒上游断流，没有剩余未归因的502；17:50:36在早间新全段SQL补证后完成关联。22:59:50尾段曾在相邻两轮引用，整夜只计一次。约902秒失败早于CH短停，不能归为CH重启，也不是旧120秒总限。未因过载重启、换模型、加自动重试或改OAuth。

Windows日志只读2MiB尾部，仅保存time/status/kind/reason/code/type/elapsed_ms/endpoint。其他/v1/messages的capacity、10条429/rate_limit和21:15未分类server_error未与personal_api记录建立归属；调用来源/具体限额仍未核对，不把所有上游事件都算成个人网关失败。08:42监听9000仍为node/PID24744，启动时间10-09 10:04:46；无正文或凭据输出。

## ClickHouse与资源压力

两个最初完整后继窗口18:54:48–18:59:48及18:59:48–19:04:48在19:05核对为0 Code241。全部163个完整发布后窗口（从18:54:48开始至末样本）内部三类均0，最终直接计数7705/最后18:49:57仍未增加。跨发布的18:49:48–18:54:48窗口包含旧错误，不算修复后失败。内部尾部18个窗口合计503处Code241/MEMORY_LIMIT_EXCEEDED文本是有界出现数，不是唯一故障总数；collector clickhouse_log字段取Docker与内部分类的较大值，不能把它当独立Docker日志计数。

CH CPU/cgroup计数按StartedAt分代际。旧世代样本nr_throttled/nr_periods增量13228/13246，部分窗口100%；17:49新世代至末样本为7024/523501，约1.34%，最后08:31五秒探针0/50。旧世代memory.current样本最大4294881280 bytes；新世代样本最大4031893504，另17:57实际pressure点4294529024 bytes，均为有限观测点。生命周期memory.peak4294971392 bytes不能称本批备份新峰，CPU占比也不等于持续吞吐能力。

新CH cgroup max在18:54:48已3492，02:59:48仍3492，03:03:10探针已9939，增加6447；至08:31未再增长。旧世代max累计百万量级与新值不得首尾相减。备份读取/归档期间file/inactive_file占多数且伴随IO压力，支持时间相关，唯一根因未确认。所有观测的CH oom/oom_kill和主机OOM增量为0，但max事件与换页不能写成无内存压力。

主机MemAvailable首6834081792、样本最低6625697792（6.171GiB）、末8767066112 bytes。SwapFree首253952、样本最低49152、末48263168 bytes；vmstat换入增57276页/换出增84242页，既有Swap近满并未解除。03:00–03:30已记录换入16704/换出81674页，后继无新增换出不覆盖前段。

主机相邻采样区间最高busy约30.74%，最高iowait约21.30%；这是区间平均，不能推成全时峰值。PG样本最多16个client连接、idle-in-transaction/Lock等待0；02:59:48见14idle/2active、最长事务98.925971秒，包含诊断但该长事务归属未独立核对，不能称整夜全部事务0秒或全部是个人网关事务。

## 磁盘增量与备份

以下是collector离散样本可用空间；正增量表示空闲增加：

| 路径 | 储备线GiB | 首值GiB | 最低GiB | 末值GiB | 首末增量GiB |
|---|---:|---:|---:|---:|---:|
| /var/lib/docker | 40 | 39.968 | 39.961 | 40.036 | +0.068 |
| /srv/smartbrain | 20 | 31.952 | 31.907 | 31.907 | -0.045 |
| /srv/smartbrain-backups | 250 | 516.022 | 486.733 | 486.733 | -29.289 |
| /srv/smartbrain-cold | 250 | 251.610 | 238.747 | 253.280 | +1.670 |

Docker两样本低于40GiB，cold三样本低于250GiB（17:54–18:04左右），后续正常parts回收只观察，没有手工删除。08:31独立即时空间Docker42987589632 bytes，仅比40GiB多37916672 bytes（36.16MiB）；runtime34259492864/cold271970586624/backup522625470464。储备仍薄，继续保留build/进一步发布/大测试和额外大归档的容量门禁；此次授权已结束，不安排后继永久任务。

范围一致的39运行容器LogPath与.1–.10轮转有界集合，从00:36:26到08:31:29净增50248569 bytes，末半小时增9650876；不包含所有历史容器，不能当全夜日志或全磁盘变化归因。可用空间首末字节增量为Docker +72560640、runtime -48332800、backups -31449300992、cold +1793531904，未做完整来源归因。没有prune、历史/日志/parts/备份删除或迁数据来过线。

原timer计划02:58:03，实际触发02:58:09，唯一备份Invocation4250cdc681a24199aa79d1da71002515，于03:58:46自然终态。08:31核对inactive/dead、Result=success、ExecMainStatus=0、MainPID/ControlPID0、Job空、无partial/failed和maintenance.pending；ExecMainCode=1是CLD_EXITED，不是exit1。timer active/waiting，下一次10-11 02:39:30 CST，未修改原备份计划。

final目录为/srv/smartbrain-backups/backups/20261009T185810Z。backup-state complete/online，36项原Invocation有界journal自检OK、FAILED0及完成标记1；31项小文件独立SHA、共28220580 bytes全部一致，inode/size/mtime前后保持。5个大payload（clickhouse.tar.gz、models.tar.gz、postgres.dump、material-uploads.tar.gz、api-tmp.tar.gz）未另做独立全量重hash，backup根dev/inode未单独复核。没有启动第二批或重放restore；online自然成功不等于全writer冻结恢复验收。

## 心跳、文档与未完成限制

heartbeat 10-10-08-30已通过automation_update设为PAUSED并工具view读回；UTF-8 TOML核对原name/prompt/rrule/目标对话一致。收尾时曾因本地Python stdout编码错误把name/prompt写成乱码，已从本对话08:30前原TOML输出恢复完整原文，保持PAUSED；错误副本保留，未建立后继永久任务。这与collector采集错误0分开。

08:30后只有核验/文档/心跳收尾，没有新业务操作。原r3/r4候选、发布与备份均终态，不重放；observer已自然终态。旧dirty源码保留，报告/任务/CURRENT镜像E盘，本轮没有整体提交、切分支或push。

未验收：完整PG/全业务数据校验、全writer冻结backup-restore、新机/整机恢复、真实30成员峰值与所有模型长期能力；5大payload独立hash及备份根身份仍未核验。主机/入口末11秒未采样，r1无CH内部日志，5分钟离散样本和有界尾部不能证明连续可用性或完整历史错误/峰值。其他上游事件归属/具体限额、全盘增减与备份压力唯一根因仍未知。后续需要新的明确授权与实时容量门禁，本报告不延长夜间授权。

## 证据索引

- 观察与原终态：.artifacts/overnight-operations-20261009/observation-20261010T003039Z.json、night-summary-20261010T003720Z.json、original-observer-evidence-final.json。
- 请求与补证：natural-traffic-20261010T003733.json、night-audit-addendum-20261010T0040.json、windows-listener-final-20261010T0042.json；SQL仅聚合、Windows仅允许的脱敏字段。
- 最终身份与资源：ch-metric-buffer-r2-verified-20261010T003132Z.json、ch-pressure-20261010T003129.json、cycle-windows-20261010T0030.json、docker-log-footprint-20261010T003129Z.json。
- 原备份：original-backup-20261010T003129Z.json、completed-backup-metadata-20261009T200713Z.json；原发布见../releases/overnight-clickhouse-20261009-r1.md及overnight-clickhouse-buffer-20261009-r2.md。
- 暂停与交付：heartbeat-paused-verified-correct.json、final-doc-mirror-manifest.json、final-evidence-manifest.json；本地runner错误单独记local-runner-errors-20261010T0030-final.json，不能改写collector结论。
