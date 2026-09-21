# M04 — project-memory

## 业务职责

负责项目记忆资料、草稿、仓库元数据、审核队列和发布前候选。

## 不负责

不负责通用项目成员管理、RAG 基础设施、Wiki MCP 传输或外部模型网关。

## 当前实现

- `agentops_local/project_memory/`
- `agentops_local/api/routes/v4/project_memory.py`
- 前端 `project-memory` 页面和相关迁移。

## 数据与接口

- 数据：project memory drafts/repositories/review queue、项目材料关联。
- 输入：项目 ID、标准化文档、记忆草稿和审核操作。
- 输出：草稿、审核状态、候选发布事件。
- 公共接口：Memory Draft API、Review API、Publish Candidate port。
- 内部接口：解析器、存储键、SQL 查询和发布算法。

## 当前耦合

直接依赖 RAG、会议领域和 project Wiki service。项目记忆与 Wiki 存在双向逻辑依赖，当前不能独立部署或独立拆仓。

## 拆分前置条件

引入单向 `MemoryCandidate` 合约；Wiki 只消费候选或事件，不反向调用项目记忆内部函数。
