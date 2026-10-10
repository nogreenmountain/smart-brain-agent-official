# 个人代理短事务与有界排队发布 r2

任务[personal-proxy-concurrency-20261009](../tasks/2026-10-09-personal-proxy-concurrency.md)，负责人Codex。2026-10-09 12:17生产验收与归档独立复核完成。授权为用户明确要求先修连接占用和并发排队，预计10–30同时使用。实际镜像和窄范围发布，既有共享工作树不整体提交或推送。

## 版本清单

| 对象 | 旧版本 | 候选 | 实际状态 |
|---|---|---|---|
| 个人代理 | b3caf14b…/image8e25962f…；12:10已实际恢复并核对 | image08f24c57…，原镜像上的三源overlay | 12:14 CIDacbab2fc…/image08f24c57…实际运行 |
| current unit | 原CID绑定active/enabled | 更新同一unit精确CID；210秒stop/240秒TimeoutStopSec | 12:14 active/enabled，新CID精确绑定 |
| writer inventory | 原request-project-attribution文件，supplemental writer | 更新确切CID/image；原字节备份 | 12:14新CID/image已读回；不是完整冻结登记 |

源hash见.artifacts/personal-proxy-concurrency-20261009/source-manifest-r2.json。仅personal_gateway_proxy.py、gateway_admission.py、personal_gateway_scope.py；app/原ORM/数据库池/Env/HostConfig/3IP/edge保持。

## 数据与验收

无DDL、Key操作、生产数据库写入或真实模型请求。旧新数据格式兼容，恢复应用无需恢复数据库；历史撤销、对话和项目归属保持。

独立HTTP+PG及代理回归34项通过（http-pg-r3及image-r2）。阶梯5/10/20/30请求全部完成，等待模型/排队时DB checkedout0和idle-in-transaction0；67成功记录独立ID/项目/3夹具Token正确，另499断连和502超时均保留unknown用量。实际scope hash鉴权、禁用/封禁/删除/匿名/范围外账号、队列满503、60秒策略的缩短超时夹具及排队后撤销通过。新增instant-response Red捕获observer取消吞掉，Green改显式stop事件并完整gather收尾；保留[r1实际失败与恢复](personal-proxy-concurrency-20261009-r1.md)。模型合成、schema最小化和leaderboard refresh stub明确，不称真实员工峰值或生产聚合函数压力通过。

## 发布与回退

按本轮promote_r2.py在backup→maintenance双锁内重核backup终态/登记20/四盘40、20、250、250GiB门槛；候选health/member_count26/匿名401。systemd排空旧代理并保留，detach旧三IP后改名rollback-concurrency-20261009-r2；clone新容器，更新同一current unit，等Docker Running后readiness。保持Env/HostConfig/Cmd/IP及edge，更新既有writer inventory。失败按本轮保存的old配置/unit/inventory重连旧IP、恢复名称和服务，不改数据库，保留失败容器及日志。

12:14实际切换与验收通过：新CID acbab2fcb677f0c3399aae43808dec00380c1ebb111ae6b228b46a3ff4a9c4b5，Image sha256:08f24c57fdb61d198eca4c2033ef0d6b125d506ad1df8fcc7bc4cb64acb19d9f。实际proxy SHA9215042e…、admission24ecdaab…、scopec438c04b…，与manifest一致。原Env/HostConfig/Cmd/三IP保持，current unit及writer inventory绑定正确；26成员health返回8/24/60秒、DB3、body16MiB，active/waiting/database_in_use均0。8公网入口按预期200/匿名401；部署代码+真实智慧脑成员/账号/项目SQL只读验证头/AGENTS归属、规则不投影、缺上下文未归属、错误400/404/403及3独立请求，0生产写入/真实模型。实际pool_size1/max_overflow3保持。

12:14 999容器/39运行，996无关基线容器Config/HostConfig/Image/启动停止时间/RestartCount一致；旧及候选停止保留，所有本任务测试容器运行0。edge宿主/实际挂载统一c22e68d972ae…并与基线相同；backup inactive/PID0/Job空/success/登记20，无maintenance pending。四盘门槛通过：Docker43345358848、root34341453824、backups560853405696、data271014440960字节；Docker余量仍小。证据promoted-r2.json、release-verified-r2.json及远端同名r2/evidence。

12:16镜像及受控证据归档完成，12:17独立SHA/0600权限/导出旧新镜像OCI配置及层核对通过。归档根/srv/smartbrain-backups/backups/personal-proxy-concurrency-20261009-r2，images.oci.tar.gz 193000251字节/SHA59e007ef4fa1ce10955b4c29e09cc79f313afac3a63c837f2a52e6c07fa379d3，evidence.private.tar.gz 1332465字节/SHA8bbd19ceb04c280fba3cd30ee5ebaef7562735b40808cc933eabf53a21338ed7。包含r1失败与恢复、r2源码/runner/单测/真实HTTP+PG/生产验收/原unit及writer清单；不含生产DB dump，不是冻结backup/restore合格点。

12:17新CID/image/unit、health8/24/60/DB3且idle0、公网ready200/匿名401、edge双视图、996无关配置代际、999/39运行、backup登记20及测试全终态再次核对通过。四盘剩余字节Docker43318575104/root34341138432/backups560659058688/data270731489280均过原门槛，Docker门槛余量仅约0.34GiB，不能称硬盘容量充裕。证据closeout-verified-r2.json、archive-manifest-r2.json；所有本轮runner已终态，不重跑发布、恢复或归档。r2生产实际回退尚未执行；r1回退通过不替代r2发布后验证。

## 运行边界

单进程8执行、24等待、60秒队列timeout；满/超时503+Retry-After3/no-store；16MiB单请求上限；共享HTTP客户端连接8；数据库操作并发3且Session不跨线程；120秒模型deadline；断连释放资格。预算按进程，扩worker/副本须重算或共享协调。保存失败仍返回上游结果并记日志，本期无持久补偿队列。CH Code241/共机械盘、磁盘门槛余量、完整冻结PG恢复与真实模型G1仍是后续事项，本轮未调整。
