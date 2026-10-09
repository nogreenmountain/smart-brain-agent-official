# 个人代理连接生命周期与并发排队发布

关联任务[personal-proxy-concurrency-20261009](../tasks/2026-10-09-personal-proxy-concurrency.md)，负责人Codex。2026-10-09 12:02准备中；用户明确授权先修连接占用和并发排队，10–30同时使用，本轮窄范围发布沿用该授权。

## 版本与范围

旧活动个人代理CID b3caf14b214aff42077849e47d1892f8f50806305db82f10262151b60ff641dc，image sha256:8e25962f559c443f10a62e9bdf12185be96f2320263f43a81bd1a599e7314588；current unit active/enabled精确绑定。候选为该镜像上的三源overlay：personal_gateway_proxy.py、gateway_admission.py、personal_gateway_scope.py，实际hash见.artifacts/personal-proxy-concurrency-20261009/source-manifest.json。无依赖升级、迁移、Key操作、真实模型请求或其他服务调整。

每个认证/授权/保存操作在线程中完整创建、使用、关闭Session；模型和排队等待不持数据库连接。数据库并发3、池仍1+3；单进程8执行/24等待/60秒等候，有界FIFO，满/超时503+Retry-After。16MiB单请求限制；共享HTTP客户端最多8连接。排队后重验Key、账号、项目；断连取消上游并记录499/未知用量，总模型deadline120秒。保持既有项目归属、消息过滤和JSON/SSE缓冲语义。

12:00独立PG+真实loopback HTTP和实际scope共33项通过，阶梯5/10/20/30全部完成；等待模型时checkedout0、idle-in-transaction0，65阶梯记录及2额外成功记录独立ID/正确项目/3夹具Token/正文130条。撤销、禁用/封禁/匿名/删除账号、队列满/超时、真实断连499及超时502通过。模型为合成HTTP服务，最小PG schema和leaderboard refresh stub，不称生产聚合压力或真实模型峰值通过。实际构建镜像专项仍待完成。

## 发布与恢复步骤

1. 固定三源manifest，在backup→maintenance双锁下重核backup终态、登记20和四盘40/20/250/250GiB门槛；只用本轮新build runner，local-base固定旧Image，无网络构建。
2. 实际镜像重跑33项HTTP+PG及代理回归；源码与镜像一致后，保存完整私有配置、已有unit和已有supplemental writer inventory。
3. clone候选ready验证health/member_count26、限额和匿名401。停止候选并保留。systemd stop原current unit排空旧代理（原150秒），保留旧容器和镜像；释放原三网络IP、改名本轮rollback；新容器保留原Env/HostConfig/Cmd/三IP及edge字节。
4. 更新既有current unit精确CID并启动，Docker Running后检查readiness。新unit停止窗口210秒、TimeoutStopSec240秒，覆盖60秒排队+120秒模型及保存。更新既有supplemental writer inventory，保留原文件备份；不是新增完整冻结协调器登记。
5. 核对实际三源hash、26成员、匿名入口、生产项目/账号SQL只读与合成上游/保存边界，既有其他容器配置/代际及edge双视图不变。失败保存现场、停新容器、恢复旧三IP/名称/unit/inventory并核对旧readiness；不恢复数据库或撤销新数据。
6. 归档确切旧/新镜像及受控证据，独立核对SHA/OCI配置层、当前unit与入口，更新任务/CURRENT及E盘文档镜像。

2026-10-09 12:03 r1已切换至CIDfb1a63de…/imageaf95e645…，26成员/匿名401/限额readiness通过。后继只读合成验收暴露instant-response disconnect observer取消被吞造成收尾等待，新增Red精确复现，12:10已实际恢复原b3caf14b/image8e25962f/原unit和writer inventory；rollback-executed.json通过，失败容器改名failed-concurrency-r1并停止保留。没有生产DB写入或模型请求，r1未归档为成功版本。数据库格式未改变，应用恢复无需数据库恢复。

修正采用显式stop事件停止observer，gather两任务完整收尾；12:11 r3真实HTTP/PG及回归34项通过。后继候选/实际镜像/发布在独立远端personal-proxy-concurrency-20261009-r2记录，不重跑r1。本文件保留r1失败与实际回退历史。

## 局限

队列预算按进程，新增worker/副本须重算或引入共享协调器。工作记录保存失败仍记服务日志并返回上游结果，本轮没有持久补偿队列；不称平台全故障闭环。ClickHouse Code241/机械盘、Docker/data储备不足余量及原完整冻结PG恢复/四模型验收仍是独立待办，本轮未修改。真实员工同时任务峰值未压测。
