# 正式仓库整理与可复现部署

任务reproducible-repository-20261009，负责人Codex，2026-10-09 13:32开发中。用户授权整理nogreenmountain/smart-brain-agent-official并按分支推送，使AI按步骤和前置条件复现当前项目。生产仅只读核对，不部署、迁移、修改Key或重启；本轮推送授权直接来自该请求。

正式远端main基线431022ba5fe5169aa6be97a5e602f5995692ab91。原C盘deb4和E盘脏树保留；新独立managed worktree为C:/Users/test/.codex/worktrees/reproducible-deployment/智慧大脑agent - 服务器端。源码分支codex/current-source-20261009；后继部署分支codex/reproducible-deployment-20261009基于源码分支。只推明确分支，不强推、不改main、不整体提交共享脏树。

阶段：核对运行镜像/源码/实际路由和私有前置条件→逐项保存最新已验证源码与安全来源清单→补齐固定镜像/配置/离线与数据库路径/AI执行入口和验收工具→独立审查、测试和干净checkout验证→提交推送、远端ref核对、更新接续入口。现场结论须记录核对时间，旧发布runner不得重放。

复现分为当前确切镜像+私有配置/数据恢复，以及源码新建空环境；前者需受控镜像与数据交付，业务数据和Secrets不上传公开Git。新建环境不得使用旧seed默认密码、旧Monitor或适配器，Langfuse和reconcile timer保持禁用。生产完整PG恢复尚未通过，不能由仓库整理推导已验收；必须明确所需交付物和未验证边界。

本轮证据保存原C盘.artifacts/reproducible-repository-20261009及独立工作树对应目录。当前没有新生产发布或用户数据导出；运行核对与任务身份将追加到本记录。


## 2026-10-09 14:18交付接续

源码分支已保存两次提交，内容提交784e280b4162058065b71c9c1e2dfb482f7376f7（随后因邮箱隐私更正提交身份，文件树不变；公开最终SHA见下）；部署分支基于它，完成统一AI-DEPLOY入口、30服务固定21镜像、Env模板、检查工具、两库结构、HTTPS/systemd和源构建说明。部署工具21项、Compose30服务、相同固定镜像隔离PG新库结构与CH23对象通过；实际源码hash1425、前端66项、代理33项。受控镜像6147032576字节与私有配置22305823字节已生成，SHA见controlled-artifacts.json；数据及OAuth状态未导出，完整新机冷启动/真实业务恢复未验收。

公开敏感值/UUID比对零命中，文档入口链接完整；只读公网smoke6项通过。测试容器均终态，原业务服务重启0。当前进入干净Git归档检查与两分支推送，不重放已完成的发布、导出或数据库测试。完整证据在受控.artifacts/reproducible-repository-20261009；原C/E共享工作树与历史保持。


## 2026-10-09 14:22发布到GitHub

两分支已实际推送到official，远端main仍431022ba5fe5169aa6be97a5e602f5995692ab91。源码分支公开SHA363715c186cc4b182cd8c8a42ab68fbd176873e2；部署分支第一次推送SHAe5f0a9d886b0ed6649a9d8cfa35c6b24fb17bffa，后继仅更新交付文档。首次GitHub GH007邮箱隐私拒绝保留，改本轮未发布提交的作者/提交者为noreply后成功，无强推，全部文件树一致。干净Git归档验证21项/30服务/1425源hash的结果仍适用，代码未变。

14:20服务侧独立核对：6个本任务测试容器全部停止，39运行，21镜像归档独立SHA再次一致；原业务服务重启0。没有本轮后台runner待接管。完整新机部署和数据恢复仍按AI-DEPLOY执行，不能称已完成。后续从GitHub部署分支获取当前HEAD即可，受控镜像/配置与另行数据备份缺一不可。
