# 个人代理连接生命周期与并发排队实施

2026-10-09 11:38，用户已明确要求先修连接占用和并发排队，按现有资源实施。本轮不退出计划模式或另设审批；在已有修复授权内推进候选、验证和窄范围发布。权威源码C盘deb4，既有共享脏树不整体提交/推送。

## 目标与方案

采用现有SQLAlchemy同步驱动的短会话：每次完整的认证/项目授权或保存操作在同一工作线程创建、使用、关闭Session。异步入口用独立3并发数据库限流器（池总4，留1余量），不在事件循环同步等待连接；模型等待与队列等待期间没有Session。队列采用当前单进程内有界FIFO，初始8执行/24等待/60秒等候，满或超时503+Retry-After；取消和异常释放资格。排队后重新验证Key、账号、成员权限，撤销不会穿透到模型。

HTTPX共享AsyncClient由应用lifespan创建/关闭，连接预算匹配执行预算；鉴权凭据只在入口使用，不传播个人Key。保持当前JSON/SSE缓冲兼容和事件记录语义，不自动重试上游模型。数据保存在线程短事务完成；本期不声称已有可靠持久化补偿队列。并发队列仅管理在途HTTP请求，不是持久化任务系统。

当前生产为1个代理worker，队列预算按进程；未来加worker/副本必须重新预算或升级共享协调器，不能把8当多进程全局限制。其他服务/CH/硬件不因本授权调整。

## 阶段

1. 固定当前实际代理、scope、app源码和配置身份；核对官方SQLAlchemy Session并发规则、HTTPX连接池/lifespan方案。创建本轮记录及新证据目录。
2. 写行为Red：等待模型和排队时DB checkedout为0、5/10/20/30完成与正确记录、事件循环心跳、队列满/超时、FIFO、取消/异常不泄漏、排队中撤销/成员权限仍拒绝、JSON/SSE/项目声明兼容。
3. 实现独立AdmissionQueue和短会话线程调用、共享客户端及仅代理入口scope；测试Green及现有代理/项目专项回归。保持每次事件独立ID与归属，不使用客户端ID吞并历史。
4. 在活动镜像的隔离候选上测真实HTTP/独立PG、30并发以及队列/撤销/取消；真实模型0，合成鉴权边界清楚记录。固定源/hash和测试结果后构建小overlay镜像。
5. 重新检查backup/maintenance双锁与原四盘门槛；原个人unit受控排空、保留旧容器/镜像/配置、切换精确绑定及writer清单。上线核对成员/匿名权限/现有项目SQL/共享客户端与源hash，其他容器和路由保持。任何失败保留现场并按本次原版本恢复。
6. 保存镜像/受控证据和独立复核；CURRENT、任务、发布记录及E盘文档镜像收尾。没有真实员工模型压力批次，不据隔离30并发称全系统最终容量通过。

文件：agentops_local/api/personal_gateway_proxy.py、agentops_local/api/gateway_admission.py、deploy/personal-proxy-concurrency/下实际scope/app候选、agentops_local/tests/test_personal_proxy_concurrency.py及必要既有测试调整，本轮docs和.artifacts。原计划已于2026-10-09 12:17实施、验证和生产收尾完成，实际范围见[r2发布](../releases/personal-proxy-concurrency-20261009-r2.md)；r1失败与实际恢复历史保留，不以计划替代结果。
