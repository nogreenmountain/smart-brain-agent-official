# 2026-10-08 备份失败诊断与修复

结论：本次失败的直接原因是备份登记未包含已部署的 2026-09-24 worklog 热补丁。不是本次磁盘容量检查失败，也不能通过清空 failed 标记、关闭配置校验或恢复旧业务配置来修复。

## 13:00 修复实际结果

11:32 已在备份→维护双锁下安装 worklog 配置及外部脚本归档修复，未重启业务容器、未关闭漂移校验。只启动一个新 online 批次 20261008T033252Z，Invocation 0326a849cecd433e8d35567e31545b07；最终 success/exit0，36 个 SHA256SUMS 文件全部通过。归档三脚本与准确来源独立逐字节核对通过。

完成目录 `/srv/smartbrain-backups/backups/20261008T033252Z`，位于本机 2 TB backups 磁盘，不是远程异地备份。服务 inactive、MainPID/ControlPID0、Job空，Result=success，timer enabled。失败历史保留，禁止重跑本次已经成功的 start runner。

本次 MCP 发布后，备份 Compose/image lock 与严格旧容器归档选择规则同步；真实20个登记服务hash/镜像再次通过，7项规则测试通过。另有发布前两张空对话表的独立隔离恢复核验，不称全数据库恢复。在线备份和发布归档不代表整机冻结或所有writer恢复门禁通过。见[生产发布记录](../releases/project-memory-no-adapter-20261008-r1.md)。

以下为安装前的诊断历史，不以早期 failed/未安装描述覆盖以上结果。

## 现场证据

2026-10-08 02:45:36–02:45:40，`smartbrain-backup.service` exit1：

- 02:45:38 两次 `backup capacity passed`，临时容量预算分别102,273,212,416和101,885,091,840字节。一次活动数据目录扫描发生临时文件消失，重试后通过，非本次终止原因。
- 02:45:40 `service-state refused: running service configuration drift: ai-worklog-worker`；随后保留`.20261007T184538Z.2875299.failed`。失败点为运行服务状态捕获，发生于实际数据备份之前；该failed目录只有约8 KiB，不是新完整备份。
- 当前服务failed、MainPID0、Job空；timer active，下一次计划2026-10-09 02:31:33。failed表示最近一次执行失败，清理缓存不会让该次备份自动成功。
- 9月25日起多次日志出现相同的worklog配置拒绝，不据此声称所有失败批次均只有这一原因。

活动worker来自原部署Compose加`/srv/smartbrain/state/worklog-hotfix-20260924/compose.override.yaml`；创建于2026-09-24 11:59:31，启动12:18:46，restart_count0。当前backup release的service-state仅加载本目录单个compose.yaml/.env，遗漏override。

镜像引用与实际镜像核对通过；唯一运行非relay配置hash不一致为ai-worklog-worker。与备份登记相比，热补丁改变environment和volumes，环境值差异涉及`AI_WORKLOG_MODEL`和`ANTHROPIC_BASE_URL`。不公开其私有值、完整配置或凭据。Compose版本与容器标签均5.5.0，未将问题猜测为版本hash算法变化。

## 判别验证

11:22–11:23，只执行Compose config渲染/hash和Docker inspect，不修改生产文件或启动容器。在现有备份配置上纳入确切热补丁override后，登记的全部20个运行非relay服务hash均与实际容器标签相同；原单文件方式仍可重现worklog拒绝。

该验证只证明这个配置差异的修复方向。它不是生产备份成功、全38个运行容器都纳入一致性备份、维护协调器完成或隔离恢复通过的证据。

## 建议处理顺序

1. 固定当前实际配置与热补丁文件的私有快照，构造备份候选的完整配置来源。备份捕获、导出、恢复及后续启动必须使用同一配置；外部脚本挂载也要纳入可恢复来源，不能仅把检查时的hash改成通过。
2. 保留配置漂移校验，验证候选与全部当前writer的登记/运行状态一致，包括主Compose项目以外的实际服务。当前backup源码部署归档只包含固定部署目录清单，不能假定外部override和脚本已经归档。
3. 在备份→维护双锁、容量和维护门槛满足后，新建一批备份，保留既有失败目录；不重放旧失败批次。采用适合当前业务不中断要求的在线范围；若要冻结writer必须先完成完整维护/恢复闭环。
4. 校验新批次清单、SHA和结构，并在隔离环境验证对应数据库/文件恢复；只读核对生产配置/代际及业务入口保持。确认服务退出0、备份complete及timer后，再报告备份恢复正常。

本轮已完成根因定位与只读判别验证，尚未安装修复候选、修改unit/timer、重跑备份或执行恢复。Docker清理后的约42GiB余量已解决应用发布容量门槛，但不替代上述备份/恢复门槛。

证据：私有`.artifacts/project-memory-no-adapter-20261008/backup-diagnosis-20261008/drift-report.json`；生产journal原时间窗口和活动`service-state.py`/`backup.sh`。报告只包含选定身份、hash及字段名，不包含环境原值或业务正文。
