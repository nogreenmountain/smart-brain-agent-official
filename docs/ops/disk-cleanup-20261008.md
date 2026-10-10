# 2026-10-08 构建缓存清理与历史目录整理

用户授权顺序：先处理构建缓存，再整理历史备份和恢复目录。本轮不删除生产镜像、容器、数据卷或备份归档，不重跑历史备份或恢复器。

## 已执行的缓存清理

2026-10-08 11:11:52，持有 `.backup.lock` → `/run/lock/smartbrain-maintenance.lock` 两锁，确认备份无活动 PID/Job、无检测到的 Docker/buildx/buildctl build/bake 进程后，执行一次：

```text
docker builder prune --all --force --filter until=168h
```

范围为超过 7 天未使用的构建缓存。原始 before/after/intent/prune/result 证据保存于生产私有目录 `/srv/smartbrain-backups/backups/docker-cache-cleanup-20261008-r1`，没有自动重放资格。

| 验证 | 结果 |
|---|---|
| 命令退出 | 0；Docker 报告 Total 13.42 GB，含共享缓存元数据口径 |
| 文件系统可用空间 | 34,277,556,224 → 45,529,014,272 字节，即约 31.92 → 42.40 GiB |
| 实际可用空间增加 | 11,251,458,048 字节，约 10.48 GiB；以 df/statvfs 而非命令报告量为准 |
| 构建缓存 | 363 条/14.06 GB → 10 条/642.3 MB，剩余报告可回收 586.2 MB |
| 容器 | 前后 902 个、38 个运行；完整容器集合保持 |
| 配置与启动代际 | 全部容器 Config/HostConfig/Image 的规范 JSON hash、Running/StartedAt/FinishedAt/RestartCount 前后相同 |
| 镜像 | 镜像 ID/Repository/Tag 清单前后相同，185 个镜像保留 |
| 公网 HTTP | 严格 TLS login/profile/workday/health/ready 200，匿名 Key/models 401 |

Docker 40 GiB 发布容量门槛已恢复。本结果不代表备份服务已修复或应用候选已发布。

## 历史目录清单

已逐个整理 73 个正式/failed/partial 批次、60 个 ClickHouse 暂存、旧备份根下 81 个子目录以及 16 个恢复/预恢复目录。完整机器清单及各对象决策保存在私有 `history-inventory.json`；未移动原路径或修改恢复指针。

必须保留的具体对象：

- 最新正式目录中标记 complete 的 online 批次 `20260924T014313Z`，以及 frozen 批次 `20260907T150005Z`。元数据 complete 不代替本次实际恢复验收。
- `backups.pre-2tb-20260907/20260829T183050Z` 仍为实际 bind mount 目标，即使在新盘有同名/同清单对象，也不可直接删除。
- `.20260910T013703Z.3229005.failed` 内部 backup-state 标记 complete，包含归档与 SHA256SUMS；目录失败状态和备份完成状态不同，不能按 failed 后缀统一清空。
- `restore-cold-20260907T150005Z-fresh-r3` 是既有恢复基线；旧恢复/失败恢复目录需保留对应历史证据和引用。

可进一步核验的重复候选：

- 60 批 ClickHouse 暂存中 49 批找到了同时间/进程身份的归档对象；清单同时记录 backup-state 声明的 backup_name，未找到对应归档的暂存保留。正式完整批次优先于失败批次核验。
- 旧备份根下 81 个子目录在新备份根都有同名目录，其中 29 个对象的 SHA256SUMS 内容相同。仅同名、大小或记录 hash 相同不等于今天实际归档字节已校验，也不证明所有子文件已完整复制。
- 16 个恢复对象未发现直接或父目录的 Docker mount Source 引用；这不排除恢复清单、文件挂载或服务脚本的引用。

因此，本轮对历史目录实施清单整理与完整性核验，尚未实施归档/恢复数据删除。后续删除范围应具体到已验证重复暂存副本，保留压缩归档和唯一恢复数据；不得运行全局 prune、按 failed 后缀删除或直接删除整棵旧备份目录。

11:18:13 首批完整性核验通过：`20260924T014313Z/clickhouse.tar.gz` 实际 SHA256 与原 SHA256SUMS 相同；归档内全部994个文件、11,051,543,654字节与对应暂存 `smartbrain_20260924T014313Z_3008214` 逐文件内容相同，无多余/缺失文件。归档及被核验文件的 inode/size/mtime 前后保持。该暂存可进入“已验证重复副本”清单；未删除暂存或归档，且内容相同比对不等于数据库完整恢复验收。其他48个有归档的暂存尚未按此标准逐文件验证，不冒称49批全部通过。

## 证据与剩余事项

本地私有证据：`.artifacts/project-memory-no-adapter-20261008/disk-cleanup-20261008/{cache-result,history-inventory,history-summary,public-http,staging-latest-verification}.json`。首次暂存核验尝试遇到锁竞争，已保留失败日志；没有绕开锁或启动删除。重新确认两锁空闲后只读核验通过并退出，未遗留核验进程或持锁任务。

11:19最终复核：核验退出、双锁无owner，Docker仍约42.36 GiB可用，902容器/38运行及配置/代际保持。首次final-state集合比较误用`docker ps`短ID与inspect完整ID，导致假false；原证据保留，后继`final-state-r2.json`使用`--no-trunc`实际重查，容器集合相同。没有因这个核验器错误进行生产变更。

现行 backup 脚本关闭自动删除并保留失败目录；ClickHouse 原始暂存打包后未自动清理。这解释了历史暂存/失败批次持续积累。没有修改该脚本、保留策略、systemd unit/timer，或重跑备份。备份 failed 状态及专项备份/恢复发布门槛仍待处置，原 AGENTS.md/company-memory 候选未生产发布。
