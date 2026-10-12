# 管理工作台视觉刷新发布记录

关联任务：[2026-10-11 管理工作台视觉刷新](../tasks/2026-10-11-management-workspace-visual-refresh.md)。

## 结果

- 源码提交：`deec447`，已推送 `official/codex/project-memory-no-adapter`。
- 本地验证：管理页 42 项、相关回归 49 项、TypeScript 检查、Next 生产构建和 1440/1024/375 静态浏览器验收通过。
- 生产部署：**未执行**。2026-10-11 17:57（Asia/Shanghai）发布前现场核对 Docker 可用空间为 `42,747,080,704` 字节（约 39.81 GiB），低于硬性 40 GiB 发布储备线。构建/发布脚本在任何镜像构建、候选容器创建和业务切换前退出。
- 生产当前版本：主前端仍为容器 `85f21545e254d0d6ee85fd03f4ff3c3bed898f32a118e7227dfe8d7007846006`、镜像 `sha256:743d5093f6c4d6694767593aa60368bd02bfc443fd05c2275d8f1619d7254ea3`，2026-10-10 09:10:54Z 启动；API 容器 `621935d93b37…` 与 edge `f72614f0f738…` 未改。
- 其他门禁：备份 timer `active/waiting/success`，无 `maintenance.pending`，内存可用约 7.96 GiB；backups/cold 空间通过，Docker 门禁不通过。

## 回退和限制

没有执行生产切换，因此没有本次发布回退动作。旧生产镜像和容器保持运行。Docker 主机显示约 13.61 GB 可回收镜像和 411.5 MB 已停止容器空间，但历史清理/删镜像/日志/parts/prune 未执行，需按容量处置授权另行处理后再重跑发布前门禁。
## 18:06 容量门禁复核

再次核对时间：2026-10-11 18:05–18:06（Asia/Shanghai）。Docker 可用空间为 42,743,386,112 字节（约 39.82 GiB），仍低于 40 GiB 硬储备线，差额约 197 MiB。备份 timer 为 activective/waiting/success，无 /srv/smartbrain/maintenance.pending，内存可用约 8.00 GiB，/srv/smartbrain、/srv/smartbrain-backups、/srv/smartbrain-cold 均通过各自门槛。未执行构建、候选容器创建、生产切换，也未清理历史对象；生产前端、API 和 edge 容器 ID/镜像保持不变。

## 18:11 生产只读终态核对

核对时间：2026-10-11 18:11（Asia/Shanghai）。未执行生产切换，当前前端容器 85f21545e254d0d6ee85fd03f4ff3c3bed898f32a118e7227dfe8d7007846006、API 容器 621935d93b37fe1a6a9245307686ee1e0fd4ca8afc4497b914cf4085e3c46227、edge 容器 f72614f0f738bd35815aeb2455dc97df99d06d1dc480e17db70ceeeb66d42e73 均运行中且启动时间/镜像未变。公网 /login、/wiki、/admin、/workday、/health/ready 返回 200；匿名 /v4/ai-gateway/keys 与 /v4/ai-usage/records 返回 401。该核对证明现网旧版本健康，不证明本次视觉改动已生产验收。


## 2026-10-12 10:04 生产部署完成

### 容量处置

在双锁、备份终态和无维护 pending 条件下，清理明确无引用的测试/构建对象：`agentops-test-supabase:latest`、`agentops-test-clickhouse:latest`、`candidate26-builder:local`，退出临时容器 `smartbrain-agents-template-compile-20261010-r1`、`smartbrain-agents-template-frontend-ready-20261010-r1`、`smartbrain-agents-template-api-ready-20261010-r1`。实际释放 `1,519,050,752` 字节（约 1.42 GiB）。没有全局 `docker system prune`，没有删除运行中业务容器、生产回退对象、业务数据、日志、备份或 ClickHouse parts。

### 候选构建

远端 release `/srv/smartbrain/releases/management-workspace-visual-refresh-20261012-r6` 的源码 manifest 115 项全部匹配，Next build 和 runtime image 构建通过。候选镜像：`smartbrain-management-workspace-frontend:2026.10.12-r6`，SHA256 `6dc4244535c779ff4ce4ab9ce08f694aee15749732ae10aaae6930a948a6500f`；候选页面 `/login`、`/wiki`、`/admin`、`/workday` 均 200。

### 生产切换

核对时间：2026-10-12 10:04（Asia/Shanghai）。持有 backup/maintenance 双锁后，仅停止旧管理工作台前端并将其保留为 `smartbrain-agentops-dashboard-rollback-20261012-r2`，创建新 `smartbrain-agentops-dashboard-1`：ID `32aaa12fcdd962589a957d845198db71f9e9185cf020fc7958b0730aebdcb346`，镜像上述 SHA，启动 `2026-10-12T02:04:44.731853423Z`。旧容器停止且保留网络外配置用于回退。API `621935d93b37fe1a6a9245307686ee1e0fd4ca8afc4497b914cf4085e3c46227` 和 edge `f72614f0f738bd35815aeb2455dc97df99d06d1dc480e17db70ceeeb66d42e73` 的 ID、镜像、启动时间和 fingerprint 未变。

第一次切换尝试在生产页面刚恢复期间捕获短暂 502，自动回退并恢复旧前端；第二次切换加入有限 502/503 重试后完成，未留下运行中的失败容器。

### 生产终验

`/login`、`/wiki`、`/admin`、`/workday`、`/health/ready` 返回 200；匿名 `/v4/ai-gateway/keys` 与 `/v4/ai-usage/records` 返回 401。Docker 可用空间 `43,803,082,752` 字节（约 40.8 GiB），内存可用约 7.9 GiB；`/srv/smartbrain`、`/srv/smartbrain-backups`、`/srv/smartbrain-cold` 均过门槛；备份登记服务 20，backup service 终态 success，`maintenance.pending` 不存在。管理工作台真实登录后的成员数据视觉未做自动化浏览器操作，本地 1440/1024/375 fixture 证据仍标注 fixture-only。
