# 个人 API 中转站认证适配 r1

## 发布身份

- 发布编号／关联任务：`personal-api-relay-auth-20261017-r1`／`personal-api-relay-auth-20261017`
- 发布负责人／验证人：Codex
- 目标环境与精确对象：`smartbrain-personal-gateway-current.service` 当前 personal-key-api；Windows 受信中转 `http://192.168.10.146:9000`
- 授权来源、范围和有效期：用户 2026-10-17 请求；仅个人 API 认证链路，未扩展 Key 数据模型、Windows 中转或模型服务
- 状态：候选已验证；生产发布受备份终态门禁阻断
- 记录更新时间／最后现场核对时间：2026-10-17 17:10（Asia/Shanghai）
- 预期行为：本地认证成功的个人 Bearer 只到受信 9000；9000 再换成内部 CPA 凭据；个人 Key 不到最终模型服务

## 发布前后版本清单

| 组件 | 旧版本与身份 | 候选版本与身份 | 实际生效版本与核对时间 | 源码和构建证据 |
|---|---|---|---|---|
| personal-key-api | CID `7e700797…`，image `sha256:532a68da…`，StartedAt `2026-10-10T11:45:38Z` | image `sha256:28cd0714…`，tag `smartbrain/personal-key-api:2026.10.17-relay-auth-r6` | 未切换；旧 CID 仍 active（2026-10-17 16:20） | 源码 SHA `075b6501…`；`candidate-result-remote.json` |
| personal gateway unit | `smartbrain-personal-gateway-current.service`，active/enabled，Invocation `370fc92f…` | 未创建 current unit | 旧 unit 保持 | `production-precheck.json` |

## 数据迁移与兼容性

- 数据库迁移：无。`ai_gateway_events`、Key 表、用量记录和项目归属逻辑未改。
- 个人 Key：只读取现有本地已验证 Bearer；不签发、撤销、轮换或复制 Key。
- 备份：最近 `smartbrain-backup.service` Invocation `af6faabf…` 以 `exit-code` 失败，原因是容量门禁；timer 仍 waiting，未启动第二批备份。既有静态登记未作为新鲜备份成功的替代。
- 恢复：未执行生产回退或数据库恢复。

## 实施与实际结果

| 顺序 | 目标与前置条件 | 动作及预期结果 | 实际结果 |
|---|---|---|---|
| 1 | 复现 9000 和公网 401 | 匿名请求只读核对 | direct `/v1/models` 401；公网 `/v4/personal-api/v1/models` 401；旧代理未转发 Authorization |
| 2 | 最小代码修复 | 增加 `opaque`／`smartbrain_relay`，relay 仅转发已验证 Authorization；归一化单一 `/v1` | 完成；项目/凭据/Hop-by-hop 头继续过滤 |
| 3 | 隔离回归 | fake relay、JSON、SSE、ASGI、旧代理并发路径 | 本地 shim 37 passed；候选镜像网络隔离回归 52 passed（1 个既有 warning） |
| 4 | 候选构建 | 以旧镜像为 base，网络隔离构建，显式检查 relay mode | 完成；候选 r6，import probe `relay-config-ok`；Docker 可用空间构建后 `43,354,869,760` bytes |
| 5 | 生产切换 | backup 成功、maintenance 无 pending、四盘门禁、回退绑定全部满足后才切换 | 未执行。最新 backup service failed，且 `/run/lock/smartbrain-maintenance.lock` 仍存在；旧容器/unit/流量不变 |

## 发布后验收

| 验收标准 | 实际入口与身份 | 实际结果和时间 | 证据 |
|---|---|---|---|
| 匿名边界 | direct 9000、公网 personal API | 两者仍 401（2026-10-17 16:20） | `anonymous-probe.json` |
| 候选认证头契约 | 网络隔离 fake relay | JSON/stream 均收到已验证 Bearer；伪造项目/API-key 头被剥离，Key 不入 URL/body | `harness-manifest.json`、`proxy-tests-rerun.log`、`candidate-tests.log` |
| 实际生效版本 | current unit / personal container | 未切换；旧 CID active，RestartCount 0 | `production-precheck.json` |
| 真实个人 Key 200 | 公网 `/v1/models` 或 Responses | 未使用、未读取或输出真实 Key；需发布后由用户用现有 Key 做一次受控验证 | 未执行 |

## 回退方案

- 触发条件：候选启动/健康、显式 Env、真实授权请求或入口核对失败。
- 回退目标：旧 CID `7e700797…`、旧 image `sha256:532a68da…`、原 unit ExecStart 与三网络身份；切换前保存完整 Config/HostConfig/unit/inventory。
- 回退动作：停止新容器、恢复旧容器原名和网络 IP、恢复 unit 和 writer inventory、daemon-reload 后启动一次并核对；不改数据库、不循环重启、不杀在途长流。
- 本轮实际回退：未执行，因为未发生生产切换。

## 限制与后续

- 当前生产 active Key 元数据来自 legacy `public.ai_gateway_keys`（`sbk_` 前缀）；`llm_credential_refs` 当前无生产行，本轮不扩展 `sk-` 新 Key 路径。该新路径需独立设计，不能把本候选称为新 Key 管理闭环。
- Docker 当前约 `40.38 GiB` 可用，备份盘约 `339.48 GiB`，虽通过应用硬线但备份任务容量门禁失败；不通过删除历史证据、prune、迁移数据或重放备份来绕过。
- 候选构建及测试容器是本轮新增证据对象，未接入 systemd、edge 或生产流量；候选失败尝试的日志保留在 `.artifacts/personal-api-relay-auth-20261017/`。

## 16:36 续核

生产只读状态仍为旧 CID/image，当前 unit active/enabled；备份服务 `af6faabf…` 仍 failed/exit-code，timer waiting，维护锁仍在。没有执行切换、重启、清理、备份重放或真实 Key 请求。候选 r6 的 52 项回归与 relay 配置导入检查仍是本轮可用证据；发布后有效 Key smoke 必须由用户以现有原始 Key 受控执行，系统不会读取或输出 Key。

## 17:02–17:10 接续核对

- Windows 启动链修正已在现场验证：`start-services.test.ps1` 4/4 通过，Node relay 与 gateway 回归 26/26 通过。解析器只读取 `access.api-keys`，实际值仅核对长度/脱敏前缀/哈希；脚本 SHA 为 `55e33f25…`，测试 SHA 为 `1fc02378…`，代理脚本 SHA `f5487503…`。
- 旧 relay PID `24220` 与 backend PID `26204` 未重启。9000 有一条自启动后持续的已建立连接，按在途长流处理；强制重启会丢连接，故未执行。新脚本只会在下次安全启动时加载正确 CPA Key。
- 17:00:41 生产门禁刷新仍显示旧 personal gateway；backup Invocation `af6faabf…` failed/exit-code，备份储备短约 6.38 GiB，维护锁与备份锁存在。生产切换、清理、备份重放、真实 Key smoke 均未执行。
