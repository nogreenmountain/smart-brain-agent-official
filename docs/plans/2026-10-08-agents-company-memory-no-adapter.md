# AGENTS.md + company-memory 项目记录与桌面适配器退出计划

日期：2026-10-08，Asia/Shanghai。
状态：用户已确认；候选源码及隔离验证完成。用户授权清理构建缓存后，生产 Docker 容量门槛已恢复（约42.4 GiB可用）；备份门槛仍待处置，未进行生产迁移或服务切换。详见任务与候选发布记录及磁盘清理记录。

## 目标和用户已确定的选择

- 用户选择 AGENTS.md + company-memory 作为项目内容记录方式。
- 网页彻底移除桌面适配器面板、检测按钮、端口提示、启动命令、Provider 修改要求和所有适配器下载。
- 保留项目 AGENTS.md 的编辑、初始化、上传和下载；项目对话记录与 Wiki 上传统计继续提供。
- 项目记录保存的是用户授权提交的对话内容和任务结果，不承诺后台采集每次模型请求或完整客户端会话。
- 上传成员和时间由服务端确定；项目归属由项目 UUID 和成员权限校验确定。
- 不修改现有个人 Key、模型入口和历史记录，不删除生产旧镜像、备份或证据，不启动子代理。

## 已核对的实施基线

- 当前聊天工作树为旧提交 8280add，不能直接用于生产覆盖。
- 同仓库 state-sync-20261008 工作树已整理较新源码，核对时为 431022b / codex/state-sync-20261008；开始实施前重新核对提交和状态，建立本任务独立分支，不修改其他聊天的分支。
- 活动项目页面来自 2026.09.24-project-context-r9；主 API、个人代理、工作记录读取服务和 MCP 服务版本存在差异。发布前逐服务核对源码、镜像、入口映射和回退点。
- 生产 MCP propose_memory 不接受 conversation_record；新版本地源码虽支持此 memory_kind，现有通用写入流程仍不能等同于项目对话记录表、知识库列表和统计的完整写入。
- 2026-10-08 10:10 只读核对：Docker 卷可用 34,523,635,712 字节（约 32.15 GiB），低于既有 40 GiB 发布门槛；backup.service failed，MainPID=0，Job 空。先完成本地候选和隔离验证，发布必须解决或得到针对门槛的明确处置，不自行清理旧资源、不重跑备份。

## 阶段 1：锁定源码、发布入口和记录契约

文件：本计划、docs/tasks/2026-10-08-project-memory-no-adapter.md、docs/CURRENT.md。

- 保存本任务改动前的源码清单和生产只读观察。
- 确定现有 canonical 对话表和 Wiki 关联结构能否复用，避免另建不参与知识库显示的孤立记录。
- 为 company-memory 增加专用工具（暂定 record_project_conversation），不将原始对话塞进通用 propose_memory。
- 输入契约包含 project_id、稳定的 submission_id、标题、用户选择提交的 user/assistant 消息、任务结果和可选客户端模型名称。
- 服务端校验项目访问、写权限、账户状态、scope、内容边界、大小和秘密；成员与上传时间由认证身份和服务端时钟产生。
- 客户端声明的模型、会话 ID 不伪装成网关实报；没有可信用量时保留 unknown，不杜撰 request_id 或 Token。
- 相同成员、项目和 submission_id 的相同内容重试返回同一记录；不同内容冲突拒绝。返回 record_id、project_id、uploaded_by、保存状态和 Wiki 状态。
- 记录正文限制在有明确授权的提交范围内；不读取其他成员原始聊天，不包含 system/developer 指令、秘密或工具环境转储。

验证：接口契约与表结构对照；在编写行为代码前建立权限、重复提交、冲突、保存与列表一致性的失败测试。

## 阶段 2：完成插件记录路径和 AGENTS.md 指引

预计文件：

- agentops_local/wiki_mcp/server.py、operations.py；新增专用保存服务与测试。
- agentops_local/api/routes/v4/project_agents.py。
- agentops_local/api/routes/v4/knowledge.py 与相关统计读取代码，仅在复用 canonical 表需要适配时修改。
- plugins/company-memory/skills/company-memory/SKILL.md、docs/WIKI-MCP.md。
- supabase/migrations/：仅当现有表无法表达可信来源、未知用量或幂等要求时增加向后兼容迁移；生产迁移不是默认步骤。

变更：

- 插件工具保存至项目对话记录并提供可核对回执，记录与知识库分类、上传成员统计保持一致。
- Wiki 发布失败与正文保存失败分别显示；重试不重复增加记录或统计。
- AGENTS.md 默认指引包含项目 UUID、调用专用工具的时机、授权内容边界和失败后的反馈要求。
- 不再要求本地端口、适配器、项目上下文令牌或修改 Provider 地址。
- 已有项目 AGENTS.md 可能是负责人自定义内容：不批量覆盖；识别旧默认模板并明确记录更新方案，自定义文件由负责人保留并按页面提示更新。
- 仓库插件说明更新后，另核对桌面已安装插件版本与工具发现缓存；不将仓库文件变化当作用户客户端已经升级。

验证：后端专项与受影响回归；隔离真实 PostgreSQL 的记录/列表/统计/幂等/权限测试；MCP 工具发现和输入输出测试。使用合成内容，不发起真实模型调用。

## 阶段 3：彻底退出网页适配器模块和下载

预计文件：

- smartbrain-dashboard/components/project/ProjectAgentsPanel.tsx 及测试。
- smartbrain-dashboard/lib/api.ts、api.project-agents.test.ts。
- smartbrain-dashboard/lib/projectAdapterLauncher.ts 及专用测试。
- smartbrain-dashboard/public/downloads/smartbrain_codex_adapter.py。
- smartbrain-dashboard/public/downloads/Start-SmartBrainCodexAdapter.ps1。
- smartbrain-dashboard/public/downloads/Start-SmartBrain-CodexProject.ps1。
- tools/smartbrain_codex_adapter.py 与专用测试。
- docs/desktop-project-context-adapter.md 与当前使用说明。

变更：

- 删除本项目桌面适配器面板、尚未检测/已连接状态、检测请求、端口算法、启动命令、下载按钮和一键启动器生成逻辑。
- 项目流程调整为：编辑项目 AGENTS.md → 下载至项目目录 → Codex 读取规则并连接 company-memory → 提交项目记录并核对回执。
- 撤下上述活动下载文件和专用启动器；历史 Git、证据和发布记录保留，不清空整个 downloads 目录。
- 核对公网下载实际来源。旧 URL 返回 404/410，不因旧容器、旧静态资源回退或代理缓存继续提供脚本。
- 兼容数据库和个人代理代码不为删网页而整片删除；不擅自结束用户机器上可能仍运行的适配器进程。

验证：页面在普通成员、负责人角色下没有适配器模块或下载；不请求任何 localhost 检测端口；AGENTS.md 上传/下载和权限仍可用；前端专项、类型检查和构建通过。

## 阶段 4：准备发布与有限范围上线

文件：docs/releases/<本次发布编号>.md、部署清单和私有 .artifacts 证据。

- 基于每个活动服务的准确版本构建候选，避免用较早本地模块覆盖线上后续修复。
- 准备旧镜像、配置双视图、生命周期绑定、数据兼容性和具体回退操作。
- 重新检查容量、备份与维护状态；门槛未解决时保持候选，不执行生产构建/切换/DDL。
- 在发布条件满足后，先发布专用插件记录接口，再发布网页与下载退出，防止新页面指引一个不可用工具。
- 只替换本任务必要服务，不重启数据库、隧道、模型网关或其他业务服务。

验证：真实活动入口和严格 TLS；MCP 工具发现；合成项目记录一次提交与重复回执；知识库对话记录列表和成员统计读回；旧下载 URL 404/410；个人模型匿名鉴权仍拒绝；主页面无适配器和 localhost 检测。

## 完成标准

1. 所有活动网页入口移除适配器模块、检测与下载，新静态资源不包含启动器。
2. 旧下载地址实际不可获取脚本，不仅按钮消失。
3. AGENTS.md 指引明确使用 company-memory，不要求修改模型 Provider。
4. 授权用户可通过专用插件工具将选定对话记录到正确项目，上传身份来自服务端。
5. 同一次提交重试不重复，越权/伪造上传成员/不安全内容被拒绝，未知用量保持未知。
6. 保存回执、知识库列表、Wiki 状态和统计一致，失败可反馈和重试。
7. 分别报告本地验证、生产发布和客户端插件生效状态；未发布或未验证的部分不标完成。

## 开始前的计划审阅

计划把“网页删除适配器”和“插件形成实际项目对话入库路径”作为同一任务。若用户仅要求第一项，应先明确缩小范围，避免发布一个缺少记录能力的新工作流。

用户已确认计划并开始实施。当前完成候选实现；生产门槛按本计划执行，不能将本地测试或内存加载的候选称为已上线。
