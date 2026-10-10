# 个人代理连接占用与并发排队

负责人Codex；任务personal-proxy-concurrency-20261009。2026-10-09 12:17已结束、生产验收与归档独立复核通过；用户授权“先修连接占用和并发排队，按照最好最新的方案”，10–30同时使用范围沿用。详见[计划](../plans/2026-10-09-personal-proxy-concurrency.md)及[r2发布](../releases/personal-proxy-concurrency-20261009-r2.md)。

权威C盘deb4共享工作树，分支codex/project-memory-no-adapter/基线431022b；不整体提交推送，E盘只镜像文档。沿用用户不使用子代理的接续偏好，本轮由当前任务实施。

11:36现场：实际个人代理b3caf14b…/image8e25962f…，unit active/enabled绑定正确；proxy/scope/app/orm原字节已取证。Docker43680251904字节、data270074798080字节仍高于40/250GiB但余量小，发布前重核；backup登记20。baseline完整配置仅远端private0600，不输出Env。

候选目标：短会话完整线程操作、模型/排队等待不占DB、3并发DB闸门、8执行/24等待的有界FIFO、60秒等候503可重试、取消释放、排队后重新鉴权/项目权限、lifespan共享HTTP客户端。现有摘要/项目归属/Token/Key语义保持，不恢复适配器/Key项目绑定/Monitor/Langfuse/timer，不做真实模型批次或CH/硬件修改。

本地证据.artifacts/personal-proxy-concurrency-20261009，远端/srv/smartbrain/acceptance/personal-proxy-concurrency-20261009-r1/evidence；新发布根使用对应releases路径。只有本轮新runner可执行，旧发布/模型/备份runner不重放。

2026-10-09 12:11 checkpoint：r1候选33项真实HTTP+独立PG通过且12:03切换，但生产只读合成验收暴露极快返回时断连监听吞取消导致收尾等待。新增instant-red精确复现（1 failed/32 passed），r1已在12:10实际恢复原b3caf14b/image8e25962f/既有unit及writer inventory，失败镜像/容器保留。候选改显式停止observer，不依赖取消；r3真实HTTP+PG及回归34项通过，0生产写入/真实模型。新r2构建、实际镜像验收与发布待执行。只读helper PID4164724已按exact cmdline+目标容器验证后终止，未动uvicorn；r1验证脚本IncludedRouter兼容失败也保留，后继修正仅helper。

2026-10-09 12:14 checkpoint：r2实际image08f24c57上34项通过（image-r2，12.25s），30真实HTTP并发全部完成且模型/队列期间池checkedout0、PG idle-in-transaction0；67成功记录及499/502未知用量保存，真实账号hash/范围/封禁/匿名/删除、Key排队中撤销、队列503/超时及极快响应收尾通过。只有模型/leaderboard refresh为合成边界，最小PG schema不冒充生产全部聚合压力。

12:14新CIDacbab2fc/image08f24c57及current unit active/enabled生效。8公网入口、真实生产账号/智慧脑成员/项目SQL只读+合成上游与保存边界通过，实际pool1+3、health8执行/24等待/60秒、DB3和16MiB上限正确，闲置计数0。999容器/39运行，996无关基线配置/代际保持，edge双视图保持，backup登记20/终态、四盘原门槛通过；所有测试容器停止/no，旧b3和失败r1保留。归档镜像/受控证据进行中。r2没有生产写入/真实模型、DDL、Key或其他服务修改。

尚未验证真实员工峰值及生产完整聚合压力；队列是单进程且不持久，60秒超时返回可重试503。保存失败补偿、CH Code241/机械盘、完整PG冻结恢复和四模型验收仍待，本任务不扩展实施。

12:17收尾：镜像193000251字节/59e007ef…及私有证据1332465字节/8bbd19ce…归档、独立SHA/0600/旧新OCI配置层通过。现CIDacbab2fc/image08f24c57、unit、8/24/60/DB3闲置0、公网及edge/996其他容器保持，999/39运行，所有测试和runner终态。无生产写入/真实模型；E盘仅镜像本轮文档，不覆盖源码。Docker余量约0.34GiB高于40GiB储备，后续发布须重新核对，不自动清理。

后续接续先读CURRENT及本记录，所有本轮runner不可重放；只读观察远端r2/evidence/{promoted,release-verified,archive-manifest,closeout-verified}.json。本任务无在途进程/定时任务需要接管；不整体提交或推送既有共享脏树。
