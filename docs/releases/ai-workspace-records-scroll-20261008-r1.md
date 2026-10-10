# AI 工作台记录与管理工作台滚动修复发布

- 发布：ai-workspace-records-scroll-20261008-r1；[任务](../tasks/2026-10-08-ai-workspace-records-scroll.md)。
- 负责人：当前 Codex；用户已有修复部署授权及明确接续。
- 状态：已发布，操作 r2 成功；完整发布验收核对 2026-10-08 17:02，归档及服务/公网入口窄核对 17:16（Asia/Shanghai）。
- 结果：记录页单一滚动根，个人正文隐藏运行时环境及 speaker 包装，负责人项目成员/审批区域取消嵌套滚动。
- 无 schema 迁移、Key 变更、模型请求或备份重跑；原库正文保留，新旧数据兼容。

## 固定版本与入口

| 组件 | 原 CID / Image ID 前缀 | 实际 CID | 镜像 |
|---|---|---|---|
| 主 API | 5ac584daa636 / 35f4ea73cf9c | 1d971f710b7b54cbffb10b254b78a4a50124c9e8d62c18ee4318d8d783b90b07 | smartbrain-scroll-api:2026.10.08-r1 |
| 主前端 | cf85e07c0b98 / a0b5f09c955a | 3a82c90e5583662ab23f2608c6651fcd9f6e90c41d239b8b8a21e42671892696 | smartbrain-scroll-frontend:2026.10.08-r2 |
| 独立 read | d530e777d9b3 / ff715afd9da1 | 5c07fd2651605a93ad8c2e6d63675c485e5d3b73b7687c113d30c261b6a16083 | smartbrain-scroll-read:2026.10.08-r2 |

核对17:02。固定 Image ID：

- API：sha256:878ec68ec20e8f112a4e8a9681f8177794bdef89badac1e1852d0923b5dee2e3
- 前端：sha256:a78a41ab4a3901a7381c30891f8a3bd262667ff3207a464438591c6ed8a51ed3
- read：sha256:985176d5cbf54b6f868a1eef856489fad0be827feac6e0e0a65fc1831838d617

原对话的主前端/主API候选不能覆盖实际公网入口：/workday 仍走旧 workday 前端，records 走独立 read。本次增加精确 /workday 位置指向主前端原IP，/admin 保持；独立 read 仅补清理 helper 和消息挂接，其他 AST 保持。/leaderboard、/worklogs 独立旧入口未纳入切换。

前端 r2 只在已验证 r1 产物加入上一版缺失的7个静态文件，没有重跑成功的Next编译或覆盖现行文件。源码见 source-manifest-final.json；read runtime SHA 4e4971d232108d1671eeea5bffdecb0e80206c6a977e02683ee8312c4db2c138。

## 发布与恢复实际记录

| 时间 | 操作 | 结果/证据 |
|---|---|---|
| 15:19 原对话 | build/candidate ready | verified.json passed；本次先观察，未重放 |
| 16:32 | 双锁/现行身份/backup/容量/edge | resumed-preflight.json passed；Docker >40GiB，登记20服务 |
| 16:37–16:48 | read窄overlay/旧资源/语法/private mount/浏览器 | read8项、前端41项及角色/滚轮通过 |
| 16:49 | 实际发布操作r1 | systemd异步启动等待误判，触发三容器实际回退；read恢复初次检查同样提前报错 |
| 16:54 | 独立恢复确认/等待红→绿 | 原三CID/完整配置/网络/unit/ready正常；promote-rollback-confirmed-r1.json；等待2项通过 |
| 16:55 | 操作r2 | 三容器和read unit切换；edge仅test/reload，无容器重启；promoted-resumed-r2.json |
| 16:59–17:00 | 公网/部署后浏览器 | 权限/资源/正文/滚轮/两角色通过 |
| 17:02 | 关闭fixture/候选/保留核对 | final-observation-r2.json passed |

环境、网络/IP、端口、卷、restart policy 保持。旧三容器改名为 -rollback-scroll-20261008-r2，停止/no、脱离原网络并保留。read unit ExecStart/ExecStop改绑新CID，未新建timer。edge宿主/活动SHA同为 f68aec199bb2f6801c44198d6c77d845ef8a3cc54b81d0b6e0e1982b76c3570a，活动bind仍ro。r1失败及检查错误全部保留，不改写成成功。

## 验收

- 前端专项41项、后端专项8项、发布等待2项通过；Python编译、diff whitespace通过，未称平台全量目录全绿。
- 合成12会话/24条user+assistant；单滚动根，617→1337；环境块隐藏；负责人成员区域内部滚动0、审批原限高容器0，普通成员只读，JS error0。
- 浏览器经loopback SSH连接实际部署容器和合成数据。公网HTML、script及已登记成员真实cookie HTTP另行严格TLS验证；26人白名单保持，未加入合成账号。
- 公网login/workday/admin/ready200；匿名records/Key401；未登记合成成员records403；登记成员options/records200。20次新script字节验证、7旧文件SHA通过。
- 两合成账号停用、两项目结项、12记录标记并保留；session和Windows代理/SSH关闭。没有公开真实员工正文。
- 17:02：921容器/39运行；911个其余既有容器配置/代际保持，4候选停止/no。Docker可用43477643264字节，约40.49GiB；其他盘门槛保持。
- backup inactive、MainPID/ControlPID0、Job空、Result success、timer enabled；20服务登记验证。沿用此前online备份，不称冻结/全writer恢复合格点。

## 当前回退方案与核对

触发条件为本次页面/读取回归、ready或权限异常。仅恢复应用、read unit和新增/workday路由，保留数据库及新业务写入。

1. 持backup→maintenance双锁，核对promoted-resumed-r2.json三CID、edge双视图SHA、unit Exec CID和backup终态，保存新现场。
2. 停止/脱网新容器，保留失败版本；旧三CID恢复原名、原网络/IP/alias/restart policy。read恢复workday-read-unit-before.service，reload/start，等待实际启动再检查health。
3. 以edge-before-resumed.conf同步宿主/活动inode，nginx test/reload；不用历史发布器或单次atomic replace代替双视图处理。
4. 核对三项ready、公网页面/权限、20项备份登记；无数据库down migration或数据恢复。

17:02旧三容器完整Config/HostConfig/Image（除明确退役restart policy）、原IP及镜像核对通过。r1实际回退已独立验证；r2仅目标核对，未实际回退，不混称r2恢复演练。

## 证据与收尾

本地 .artifacts/ai-workspace-records-scroll-20261008/；远端 /srv/smartbrain/releases/ai-workspace-records-scroll-20261008-r1/evidence。完整inspect、cookie和原运行配置只置于私有位置。修改未提交/未推送，不整体提交混合脏工作树。

17:02上线验收完成；临时候选/会话/代理终态。接续先观察，不重放build、promote或fixture。

17:09:56归档完成，目录为 /srv/smartbrain-backups/backups/ai-workspace-records-scroll-20261008-r1；17:16独立重新计算哈希、核对tar目录和镜像身份通过。归档文件及清单权限为0600：

| 文件 | 字节 | SHA256 |
|---|---|---|
| runtime-images.tar | 322698240 | f72200a9ef08aff0715972db00a235eb6d578e9a611a6cf38ff63bc6dad322e9 |
| evidence.private.tar.gz | 58092535 | c7e0bde4174cce4c55e0d325102879445d054afd8f5c4eb20af28471d28f40b9 |

镜像归档含三个当前版本，按OCI index digest→linux/amd64 manifest→config及layer引用核对；证据归档含发布、验收及r1回退原始记录。初次独立脚本误将Docker Image ID与config哈希直接比较，检查失败；诊断确认Image ID是OCI index digest，修正检查后通过。保留archive-verification-r1-failed.log、verify_archive_closeout_r1_failed.py及archive-format-diagnosis.json，未修改镜像或归档。

归档不含生产数据库快照，没有执行恢复；属于镜像和私有发布证据归档，不是生产冻结备份或恢复合格点。archive-manifest.json已保存本地；独立核对证据为archive-closeout-verification.json。原tar保留生成时文档版本，收尾文档另行同步到release目录，不重写tar。

17:16窄只读核对：三个当前CID/Image/Running与发布记录一致，read unit绑定通过；edge宿主/活动SHA保持且bind只读；backup inactive/PID0/Job空/Result success、timer enabled；严格TLS ready/login/workday/admin 200、匿名records 401。本次未重复17:02的全容器、角色浏览器或登记成员业务验收。
