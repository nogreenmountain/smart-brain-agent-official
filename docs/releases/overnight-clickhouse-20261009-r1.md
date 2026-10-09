# 夜间ClickHouse后台合并限并行r1

关联[夜间任务](../tasks/2026-10-09-overnight-operations.md)与[具体方案/自审](../plans/2026-10-09-overnight-clickhouse.md)。本轮用户授权自行审核开始一晚运维，截止2026-10-10 08:30。实际发布2026-10-09 17:49–17:50，独立核对17:51（Asia/Shanghai）。

## 问题与行为

CH24.12.6.70，2CPU/4GiB容器、3.6GiB内部上限；后台pool16×ratio2，17:36有25个system.metric_log/text_log后台合并任务，CPU50/50周期节流、内存max事件增234，Code241持续。主机和个人API无耗尽证据。

只将后台合并pool降为2、ratio为1，三个相关free_entries阈值改1，控制后台峰值；保留内存/CPU限额、日志配置、账号/网络/数据与备份磁盘。不删数据/日志、不设置新TTL、无DDL，不重启个人API或其他业务。

## 版本与实际动作

- 同一CH CID f0a0f6eb8827c8a84c908f89eb3fa8169e95d0bcfcf2dfe3e90882d8bffe6653，image sha256:cd450891db46cc6ffe313ca2b0fb7dbfb897a6873ca74a724cbe050a2cf62621。
- 唯一宿主XML单文件bind原SHA2783cb71d0f2c6bc7999777572b9bf46e34db573f8e5aef508d354a5ef665266；新SHA ecf3efd265105bff68ee400364c073f53e256da913b9255d418f7e253ee284b1。保留原storage_configuration/backups字节，在根末尾追加候选资源设置；原inode5374067/owner/mode保持，实际挂载及宿主同字节。
- 原配置和1023完整容器基线私有保存在 `/srv/smartbrain/acceptance/overnight-operations-20261009/`，文件0600。双锁backup→maintenance、备份20登记/inactive/PID0/Job空、无pending、40/20/250/250GiB及内存保留重新通过。
- 原版本metadata明确pool只能在线增加、ratio不能热改，因此精确停止/启动此CH一次。新StartedAt2026-10-09T09:49:40.337495161Z，PID930830；17:50实际2/1读回。没有替换容器/镜像、没有Compose整体up。

## 验证与限制

同镜像隔离r2无网络/端口，真实2/1及三个阈值读回，20000合成行计数/求和、测试restart后持久化通过，停止保留。r1误以root启动Code430与数据属主不匹配，失败原日志保留，没有改生产身份。

17:51独立验证：1022无关基线容器完整Config/HostConfig/Image/启动停止代际/RestartCount全部保持，39运行/测试运行0；4个原业务表active-parts行数前后相同（只验证元数据行数，不是完整数据checksum）。8公网入口200/匿名401、个人70583b47/8/24/DB3及edge双视图c22e68d9保持；OTel bounded日志从CH启动以来retry/failed export计数0，不能据尾部宣称遥测零丢失。备份20登记保持。

后台压力效果需观察两个窗口，本记录17:51尚未达到此条件；不能把重启清空error计数称彻底修好。collector baseline不重写，其CH启动变化是本次受控变更，后续核对本次StartedAt而不是再次重启。

实际回退未执行。原配置已保存；若新故障，核对当前CID/image和双锁/备份、将原XML写回同inode并恢复同CH，不能恢复旧数据库或盲重放整套发布脚本。

镜像包/21镜像lock不变，部署分支须同步新 `deploy/current/clickhouse/backup-disk.xml` 与配置SHA。原13:30私有包保持原始归档，不能重写或称已包含本次资源调整。完整冷恢复、30人峰值和长期CH稳定性仍未验收。

## 17:57效果核对（部分改善，内存问题未解决）

当前pool2/ratio1实际保持，后台任务2；5秒CPU节流1/50周期（原50/50），平均CPU约1核。text_log active parts由88降25且仍有合并，证明有推进。Code241重启后27累计且17:57尾部仍有新错误，cgroup max事件5秒+310、无OOM；不能把较小累计值或CPU改善称内存故障解决。下一阶段核对单次宽表/大合并的block和内存峰值，仍不得扩大内存、删系统日志或直接循环重启。

部署工具新增对固定XML的SHA校验，Red→Green及23项部署测试通过，源文件manifest通过。新交付分支codex/overnight-operations-20261009准备提交；原镜像与受控私有包保持，新机直接使用本分支Compose挂载的XML，原包先按其原manifest校验，不能被旧包覆盖本分支配置。

18:01两个后继5分钟采样仍有Code241；当前保持窄修复带来的并行/CPU改善，不重复重启。cold可用空间238.75–242.18GiB低于250GiB储备，已有大合并结果和inactive parts，正常回收在进行但差额来源未全部核对。停止进一步生产调整/大型测试或归档，不手工清理历史。official分支提交8430aa6a25ade34adb36a84af8bd555e5839c410已push/远端SHA一致，main431022b不变。后续配置必须先恢复资源门禁并验证新候选；仍不能称全部内存故障解决。

证据：本地 `.artifacts/overnight-operations-20261009/{ch-pressure-20261009T093636+0000,ch-candidate-metadata,ch-candidate-test-r2,ch-preflight,ch-promotion-result,ch-release-verified}.json`，远端同任务目录中原始私有基线、配置和每步intent。所有隔离runner终态；原observer/heartbeat继续，不重跑发布、test或旧r1失败。
