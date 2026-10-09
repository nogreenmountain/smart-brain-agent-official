# 个人 API 反复断开排查

## 任务身份与范围

- 任务编号：personal-api-disconnect-20261009；负责人：Codex。
- 创建时间：2026-10-09 16:12（Asia/Shanghai）。开发阶段：调查中；部署范围：未部署。
- 用户反馈个人API显示api error，继续后再次中断；本轮先核对网关、上游、流式与超时证据，确认原因后作必要的最小修复与验证。
- 验收：复现与根因有区分性证据，修复通过相关回归，实际入口与服务状态核对。历史授权不作为本轮生产变更授权。

## 代码与版本

- 权威工作树：C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端；codex/project-memory-no-adapter / 431022ba5fe5169aa6be97a5e602f5995692ab91。
- 既有脏修改保留。本轮证据 `.artifacts/personal-api-disconnect-20261009/`；远端私有证据 `/srv/smartbrain/acceptance/personal-api-disconnect-20261009-r1/`。
- 生产身份/根因：16:40核对70583b47/image6c9a5779流式r2；12:17 concurrency r2已被本轮替换。E盘源码不覆盖权威工作树与生产。

## 已完成与未完成

- 已读CURRENT、维护流程、相关发布及系统调试技能。
- 16:15只读证据确认17次502均120秒；合成持续流在旧代理总截止稳定失败。修复实时SSE、120秒idle/1800秒max、并发许可生命周期和失败完成字段。
- 实际镜像41项HTTP/独立PG、默认130.12秒长流通过；42项验证涉及单首包55ms、断连/失败/队列/鉴权/记录归属。部署工具22项/源码manifest/Compose静态通过。
- 16:39只切个人代理与current unit/writer清单；16:40独立生产验收通过。16:44自然26用户请求均200。无DDL、Key操作或主动模型调用；其他1018容器配置代际保持。
- 详见[本轮发布](../releases/personal-api-streaming-20261009-r2.md)。16:50归档独立SHA/OCI及21镜像身份通过；真实GPT请求627576ms成功。16:56剩余上游503/内部failed与Windows上游capacity/server_is_overloaded日志逐时刻对应。供应商过载尚未消除，完整平台容量/冷恢复未验收。

## 运行中的任务与下一步

- 本轮采集、测试、130秒、构建、发布和归档runner均终态，测试容器停止；backup inactive/success，无pending。
- 下一步：官方仓库新分支同步和远端SHA核对，镜像包入口保持基线＋增量。禁止重放发布/归档/模型批次。没有需要接续的本轮活runner。

## 17:00收尾

开发阶段：已结束；部署范围：生产个人代理/current unit/writer清单。官方分支codex/personal-api-streaming-20261009修复提交b105937f60df956b32fc040ebe23974633c64f77已推送且远端SHA一致、main431022b保持；新分支包含当前源码/运行快照、21镜像lock、旧base lock与单镜像delta lock及部署说明。清理误推原origin的本次临时分支，官方副本保留；没有PR创建或main合并。

22项部署工具、全源码manifest及Compose模板静态验证通过；代理41项和独立130秒合成（总42）通过，真实627576ms完成。完整新机冷启动与供应商模型容量未验收，过载仍可产生API error。无本轮运行任务需要接续，不复用旧发布、归档或模型批次。
