# 新注册账号个人 API 准入修复

## 身份、范围与版本

- 任务：personal-api-registration-20261019；负责人：Codex；核对时间：2026-10-19 15:07（Asia/Shanghai）。
- 用户报告新号无法创建 API；目标为有效注册账号可查看名额、创建并使用自己的个人 Key，保留配额、跨账号边界与禁用/封禁/删除/匿名拒绝。
- 权威目录：`C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端`；分支 `codex/project-memory-no-adapter`，基线 `d7861a5cd39ff7f860ea489888e9b1e254ee0bc2`。
- 阶段：调查/候选开发；部署范围：未部署。方案见 [实施方案](../plans/2026-10-19-personal-api-registration.md)。
- 原 dirty：relay-auth-20261017 发布记录、ai-work-record-projection-20261012 任务及未跟踪发布记录；保留且不归入本次提交。

## 已核对

- 15:07 当前个人容器仍 `052676a8caaf…` / image `28cd0714…`，StartedAt `2026-10-18T14:43:13.86527095Z`，current unit active/running/enabled，Invocation `c1554993c4ba4e9c85ce6fa887082f5e`。
- 实际 scope 在查询实时账号状态前要求用户位于固定名单。名单26人；当前25个有效账号中3个不在名单。截图账号auth/public各1、有效、名单不包含。服务器仅定向聚合查询，不导出账号列表/Key/正文。
- 原45条Key聚合指纹 `61a5646cfd1c1119890ac23233fda77a`，当时3执行/0等待/DB0，8/24/DB3保持。本任务未签发/撤销/轮换Key。
- Docker空闲42,832,199,680 bytes，低于40GiB门槛117,473,280 bytes；root/backup/cold达标。backup Invocation `2f043103ee9e4af7a4ccc62cbeebb2d0` failed/exit1/PID0，登记20，原因待查。不能使用昨晚成功状态作为今天门禁通过。
- 证据：`.artifacts/personal-api-registration-20261019/initial-readonly.json` 和只读源码副本；初次本地取证脚本字符串嵌套错误在SSH前失败，修正后实际只读成功。

## 后续与边界

1. 先以生产相同scope复现固定名单拒绝，补新账号及失效账号测试；保留异步代理/长流和公开唯一入口。
2. 注册模式按当前auth/public实时判定，旧名单模式仅供明确隔离/灰度调用，不默认为正式个人入口。
3. 查当前工作记录路由是否也受同一名单约束；有证据再确定最小变更范围。
4. 完成隔离PG和HTTP验证；门槛未恢复不构建/发布，不清理历史容器、日志或备份来掩盖。
5. 新发布需独立身份、实际备份/容量/维护门禁、无在途流排空及回退证据；旧发布/Windows边界/已终态清理不重跑。

运行任务：本任务取证已终态；其他进程状态仅以上述核对为准。Git未提交/推送；生产未变更。

## 2026-10-19 15:37 接续：候选通过、储备恢复、唯一备份运行中

- 本地旧入口明确复现新账号403；候选20项scope回归及路由静态合并22 passed/1 deselected。生产镜像＋只读挂载候选＋独立PG/真实HTTP组合测试1 passed；覆盖首Key、默认额度1、6并发仅1成功、跨账号404、旧/新Key认证、禁用/封禁/删除/匿名拒绝、撤销401及再次创建、8/24/DB3。浏览器session解码和模型响应为合成，不冒充真实登录或模型闭环。
- 15:20测试r3成功终态，test05dfa373/PGc0aa4e2c均停止；PG128MiB tmpfs随停止释放，无生产Key签发。r1日志驱动参数错误、r2runner替换范围错误均保留，不再启动；r3不重跑。发布状态机17项成功/故障/单次回退/准入健康测试通过。
- 15:29用户明确批准“允许增加2GiB，继续上线”；15:29:51仅将 `/dev/ubuntu-vg/smartbrain-docker` 从105226698752增至107374182400 bytes，并完成ext4在线扩展，free44945653760 bytes。原业务重启0。证据`storage-extended.json`及远端`personal-api-registration-storage-20261019-r1/stage.json=complete`，禁止重跑lvextend。
- 15:34完成9月15/16/17三个新目标的正式archive SHA及各1133文件逐一比对，相同；15:36 review、15:37执行前复核双锁/无活动backup/无pending/无容器与进程引用/元数据未变/无外部硬链接，移除的仅对应clickhouse-staging副本。释放33165008896 bytes（30.887GiB），正式备份归档/清单全部保持。今日目标与昨天已清理三目标不同；两批都不可重跑。
- 15:37:39动态容量checker通过后，仅启动一次新的online备份：Invocation `68dcec4071f04a6c806763d4d72a40d7`，初始Job11324206/ControlPID2135364/start-pre。**仍在运行，未验收成功；后续只观察此Invocation，不重启或启动第二批。** start-intent/started位于`/srv/smartbrain/acceptance/personal-api-registration-20261019-backup-r1/`。
- 实际proxy原始字节SHA仍`075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe`；initial-readonly里`5b57721c…`是stdout文本换行规范化后的SHA，不是生产漂移。原始字节证据在`gates-readonly.json.source_bytes_sha256`。
- 公网ai-gateway/个人模型路由均指当前个人容器；独立workday读入口仍有自己的部署，当前任务不改变该服务或Windows。现有生产业务代码尚未切换，新账号问题仍待发布后用户验证。
- 下一步：核对上述唯一备份终态/归档清单和容量→构建两文件叠加镜像→实际镜像独立测试→无在途流时单次发布/核对。`deploy/personal-api-registration/release.py`为新发布入口，仅复用旧库的Docker/systemd原语，不执行旧promote/Windows脚本。
