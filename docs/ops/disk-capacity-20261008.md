# 2026-10-08 生产磁盘只读核查

结论：没有发生整机 3 TB 磁盘占满。生产有 1 TB 数据盘、2 TB 备份盘，以及独立 256 GB 系统 SSD。此前发布容量问题指 SSD 上的 Docker 文件系统可用空间低于 40 GiB 约定门槛，不是整机剩余空间不足。

## 实测容量

2026-10-08 11:05 起通过生产 SSH 只读核对 lsblk、df、vgs、findmnt、Docker 统计和低 IO 优先级 du。GiB 按 2^30 字节；文件系统容量小于磁盘标称容量。

| 文件系统 | 文件系统容量 GiB | 已用 GiB（约） | 可用 GiB（约） | df 使用率 |
|---|---:|---:|---:|---:|
| 根目录 | 97.9 | 59.3 | 33.6 | 64% |
| Docker | 95.9 | 63.0 | 32.0 | 67% |
| hot | 34.3 | 13.7 | 20.3 | 41% |
| cold，1 TB 数据盘 | 915.8 | 653.4 | 253.1 | 73% |
| backups，2 TB 备份盘 | 1832.7 | 1228.1 | 585.9 | 68% |

Docker LV 原始分配 98 GiB；系统 SSD 的 VG 未分配空间约 2.42 GiB，不能仅靠现有 VG 空闲直接补齐 40 GiB 发布余量。数据盘和备份盘是独立文件系统，其空闲不能直接被 Docker 分区使用。

`/var/lib/containerd` 是 Docker 分区 `/containerd` 子目录的 bind mount。两处 du 的 66,970,476,544 字节是同一份存储，不可重复计数。镜像/快照/内容层约 62.37 GiB，为 Docker 分区主要占用；容器目录约 0.55 GiB。journalctl 报系统日志约 1.2 GB，所在根分区，不是当前 Docker 容量的主要原因。

## 清理候选及边界

| 候选 | 观察到的占用/报告可回收量 | 判断 |
|---|---:|---|
| Docker 构建缓存 | 总 14.06 GB；报告可回收 11.24 GB，约 10.47 GiB | 优先核查未共享、未使用缓存；verbose 统计约 160 条未共享且非 in-use。只删除缓存会使后续构建重新生成相应层。未实际执行清理，最终物理释放量须清理后以 df 确认。 |
| Docker 镜像 | 总 52.27 GB；报告可回收 13.61 GB | 必须先确认回退镜像、父镜像和试验归档的保留名单；“reclaimable”不是业务允许删除的判据。与缓存存在共享层，不能直接相加。 |
| 停止容器可写层 | 报告可回收 405.2 MB | 总容器 902、运行 38；容器数量多，不代表容器本身占据数 TB。历史容器仍可能承担恢复/取证用途。 |
| 备份盘 ClickHouse 暂存 | `backups/clickhouse-staging` 60 批，约 483.01 GiB | 显著积累；需核对备份批次完成/失败、归档可恢复性、引用和保留规则，不能仅因 staging 名称就删除。 |
| 备份盘失败目录 | 42 个 `.failed` 目录，合计约 150.36 GiB | 候选，保留失败证据及必要恢复数据后再逐批处理。 |
| 数据盘旧备份 | `backups.pre-2tb-20260907` 约 357.04 GiB | 需与新备份盘归档逐项核对，不能仅凭目录名认定迁移完整或重复。 |
| 数据盘恢复测试/失败恢复目录 | `.data.restore-*` 与 `data.failed-restore-*` 合计约 231.4 GiB | 需核对历史验收、恢复用途、引用及保留规则。未把活动 `data` 目录列为清理对象。 |

上述目录统计是现场 du 结果；共享/硬链接、跨挂载以及活动数据库文件变化会影响“目录占用”和“实际可释放”之间的关系。cold 扫描期间 ClickHouse 临时 merge 文件消失，du 返回 1；其余目录统计及 df 保留，未把活动目录的扫描值当作一致性快照。

未发现上述候选名称作为 Docker 容器直接 mount Source；这不证明没有经父目录、bind mount、服务脚本或恢复清单间接引用。备份服务仍 failed、MainPID=0、Job 空；未重跑备份，也未改变 timer。

推荐顺序：先评估/定向清理未使用构建缓存，复核 Docker df 和生产状态；再建立历史镜像、备份暂存、失败批次及恢复目录的保留清单。清理大盘目录不会直接解除 Docker 分区门槛。长期 Docker 容量规划需独立设计，当前没有执行磁盘迁移、扩容或服务停启。

Docker 官方说明支持单独清理构建缓存，且共享缓存层可能只释放元数据；见 [builder prune](https://docs.docker.com/reference/cli/docker/builder/prune/) 与 [buildx du](https://docs.docker.com/reference/cli/docker/buildx/du/)。本轮没有执行 prune、删除、迁移、扩容或生产发布。

私有原始证据：`.artifacts/project-memory-no-adapter-20261008/disk-readonly-20261008/{capacity,detail,refs,cache-summary}.json`。仅采集容量、目录和选定元数据，不公开凭据、环境变量或业务正文。
