## 2026-10-19 16:53 实际终态补充

r1候选检查通过后因60秒未排空在切换前退出，原生产未变；r2延长等待后同样在切换前退出。镜像构建及实际镜像PG/HTTP测试已通过。最新终态见[r2发布记录](personal-api-registration-20261019-r2.md)及[任务](../tasks/2026-10-19-personal-api-registration.md)。下面的“未构建”等描述保留为15:37历史状态，r1不可重跑。

# 新账号个人 API 准入发布准备

- 发布编号：personal-api-registration-20261019-r1；关联[任务](../tasks/2026-10-19-personal-api-registration.md)。
- 状态：候选已验证，未构建/未发布；更新时间：2026-10-19 15:37（Asia/Shanghai）。
- 当前生产：个人 CID `052676a8caaff02578b73a25f10258da0d11350f164e4a94469d7912f2dae35e`，image `sha256:28cd0714f8ebdb214ad259444e4a9123b1d5d6ec4b89bf93fd48a40bd19e1cb1`，current unit `smartbrain-personal-gateway-current.service`。15:07核对active/running/enabled，Invocation `c1554993c4ba4e9c85ce6fa887082f5e`。
- 预期：正式个人入口使用当前有效注册账号，而不依赖发布时26人名单。保留显式名单调用模式；当前账号可用性、Key归属、配额、管理员和项目权限保持。

## 候选与证据

仅个人服务叠加两个文件：`deploy/personal-proxy-concurrency/personal_gateway_scope.py` 与 `personal_gateway_app.py`。权威旧同步scope中只同步名单逻辑，部署采用当前异步版本，禁止整体用旧scope覆盖生产。

- Windows回归22 passed / 1与本改动无关的optional daily模块测试deselected；原故障入口Red明确名单外账号403，候选Green通过。
- 当前生产镜像＋只读挂载两候选文件＋独立PG＋真实loopback HTTP：1组合测试通过。真实创建/列表/默认额度1、6并发仅1成功、跨用户404、禁用/封禁/删除/匿名拒绝、原Key认证、新Key认证、撤销401、再创建、8/24/DB3均通过。
- 浏览器会话解码和响应处理使用合成替身；Key hash、账号SQL、创建SQL、路由、异步scope与socket HTTP是真实代码。未使用真实员工Cookie/Key或调用模型，不称真实员工领取成功。
- 测试r1因Docker local日志压缩不支持max-file=1而无法启动；r2因runner替换范围过宽，在启动前找错名称失败；修正runner后新r3通过。旧失败保留，不重跑任何已终态批次。
- r3测试CID `05dfa373…`、PG `c0aa4e2c…` 已停止/exit0；PG位于128MiB tmpfs，随停止消失，未创建生产库或备份盘测试数据。r1 Created容器 `ac025771…` 保留。全部测试runner已终态。
- 证据 `.artifacts/personal-api-registration-20261019/{red-scope,green-scope,regression,isolated-pg-r3}.log`；远端 `/srv/smartbrain/acceptance/personal-api-registration-20261019-r3/`。

## 发布门槛与操作计划

1. 生产只读确认：Docker少于40GiB门槛约112MiB；今日backup Invocation `2f043103…` failed/exit1，备份盘free345756135424、required371561439232 bytes，动态容量不足。不得把昨晚成功替代今日门槛。
2. 用户明确批准后，15:29:51将ext4 `/dev/ubuntu-vg/smartbrain-docker` 从105226698752增加2147483648至107374182400 bytes，online resize完成；空闲44945653760 bytes，无业务重启。终态`storage-extended.json`，不重跑。
3. 15:34已完成9月15/16/17三份ClickHouse staging与正式归档的SHA和各1133文件全量相同比较；15:37双锁/无活动备份/无maintenance pending/无引用/元数据未变检查通过，仅清理三份重复staging，释放33165008896 bytes。正式归档与清单保持。目标及SHA详见`cleanup-executed.json`；禁止重跑。
4. 15:37:39动态容量通过，新的唯一online备份Invocation `68dcec4071f04a6c806763d4d72a40d7`已启动、尚未终态；只观察该批次。成功并核验归档后才构建两文件叠加镜像及实际镜像隔离测试。当前生产代码尚未变更。
5. 固定Config/HostConfig/network/Key聚合与edge双视图；确认无在途请求后单次替换当前个人服务，保留旧容器与镜像。current unit及writer inventory精确绑定新CID，不更改Windows relay/业务库/员工Key。
6. 验证公开login/health200、匿名Key与模型401、实际`membership_policy=registered_active`、8/24/DB3、原Key数据及无关容器保持；真实用户创建/模型使用单独标记，不能冒充通过。

## 兼容与回退

无数据库迁移、Key轮换、历史回写或项目绑定变化。回退恢复此次旧镜像、原容器网络/服务绑定；保留新期间产生的Key、撤销与记录，不恢复旧数据库。旧白名单在应用回退后会再次限制新账号，须明确报告，不能称业务问题仍已解决。

生产实际发布、生产实际回退、最终新账号用户侧验收：均未执行。空间调整和备份完成后仍需重新核对现场，不沿用本条旧时间。
