# 当前仓库与部署分支交付验收

任务reproducible-repository-20261009；核对时间2026-10-09 14:15（Asia/Shanghai）。本轮按用户要求整理并分支推送，不改main，不重启生产业务、不迁移生产库、不签发Key或请求真实模型。

## 交付内容

- 源码分支保存当前修复、回归测试和七组实际运行模块。1425源文件SHA与原运行字节一致，保留组件差异及worklog的实际挂载修复。
- 部署分支在源码分支上增加30服务／21固定镜像的Compose、逐服务Env模板、资源/镜像/缺项检查、受控镜像导入导出、两库结构、路由/HTTPS/systemd模板和AI执行步骤。
- 统一入口README→docs/deployment/AI-DEPLOY.md；历史profile加明显标记。新路径不启动Monitor、适配器、项目Key绑定、Langfuse、reconcile timer或试点组件。
- 受控镜像包已生成，6,147,032,576字节，SHA256 `180eceb32b890e286d3920eda81121f631d7c2b86d2e08f733a00bec3ec8c4c5`；私有配置／静态包22,305,823字节，SHA256 `03f2ca165d9f27c9d5628291ac337b02e2c8ac7d08e832e59e9672668cfc70d6`。位置见controlled-artifacts.json，权限0600；不能发布含机密的配置包。

## 实际验证

| 范围 | 结果与证据 |
|---|---|
| 当前源码 | 相关前端66项、确切代理镜像隔离33项；1425源hash；1454Python编译；见repository-source-20261009 |
| 部署工具 | 21项通过；Image ID/平台、缺Env/占位符、私有路径/目录逃逸、磁盘/内存门槛、OCI身份、归档篡改、SQL密码转义、缺恢复receipt、退休拓扑与实际HTTP路由 |
| Compose | 全部profiles（rag/workers/relay）30服务config解析通过，使用合成私有输入；没有真实Secrets输出 |
| PostgreSQL | 相同固定生产PG镜像，network=none、独立tmpfs，空新库schema恢复与只读gate通过；不是生产业务数据恢复 |
| ClickHouse | 相同固定镜像，network=none、独立tmpfs，23个schema对象创建通过；不含历史数据、模型价格行或业务压力验收 |
| 镜像交付 | Docker save实际包根OCI/index digest、配置平台与lock21身份一致，archive SHA生成并再次验证；未在另一台Docker29机器完整load验收 |
| 生产只读HTTP | 六项匿名/页面/退休下载smoke通过，严格TLS，无模型与写请求 |
| 生产影响 | 配置包阶段30业务容器Config/HostConfig/Image及运行代际前后一致；无业务重启，独立测试容器均停止 |

首次镜像校验误用了旧Docker config-hash口径，真实Docker29导出失败保留原6.15GB包；补OCI index/manifest身份用例后，在原包上验证并完成交付，没有重复导出。首次PG测试误识别初始化临时server就绪导致连接被结束；后继测试改最终TCP就绪后通过。初始工具缺文件Red、上述失败和Green证据都保留，未修改生产迎合测试。

证据保存受控.artifacts/reproducible-repository-20261009；服务侧隔离repository-source/schema/ch-schema/artifacts目录。公开Git只保存此摘要和配置模板，原Env/私有schema中间文件/员工正文不公开。

## 验收边界

全新机器的完整30服务冷启动、GPU/模型缓存/外部上游授权、实际业务数据恢复、用户全流程与主机重启尚未验收。本分支明确给出前置条件及步骤，不能据本轮结构与镜像校验称“新机原样部署已成功”。原完整冻结PG恢复、CH压力等后续事项保持。

Git分支实际提交及远端SHA在任务最终交付记录保存。推送不代表生产发布，历史记录与原C/E工作树保留。


2026-10-09 14:22Git验收：两分支实际push成功，main保持431022b；GH007改本轮未发布提交的邮箱身份为GitHub noreply后通过，文件树一致，无强推。干净Git归档21项/30服务/1425源hash通过；14:20服务侧独立SHA再次验证、6测试容器停止、39运行。源码公开363715c，部署首次公开e5f0a9d，后继交付文档更新不改变代码验证范围。
