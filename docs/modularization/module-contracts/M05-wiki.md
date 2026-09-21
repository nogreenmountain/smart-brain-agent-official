# M05 — wiki

## 业务职责

负责项目 Wiki、成员 Wiki、版本/审核、MCP 访问和对应后台编译任务。

## 不负责

不负责认证实现、项目成员主数据、通用 RAG 算法、AI 用量结算或部署平台。

## 当前实现

- `project_wiki/`
- `member_wiki/`
- `wiki_mcp/`
- `project_wiki.py`、`member_wiki.py` 和相关 worker。

## 数据与接口

- 数据：project wiki pages/changes/tokens、member wiki experiences/versions/sources/runs、processed sessions。
- 输入：项目/成员 scope、MemoryCandidate、审核动作、MCP 请求。
- 输出：Wiki overview、版本、候选、MCP 响应、worker 状态。
- 公共接口：Wiki Read/Write port、Compile Job port、MCP contract。
- 内部接口：编译器、SQL query、token hash、模型 prompt。

## 当前耦合与风险

Wiki 直接使用项目记忆、RAG、成员、会议和认证实现。MCP 不能在当前状态直接独立成仓库。

## 测试

需要项目权限、成员权限、审核幂等、MCP token、编译失败重试和 worker 调度测试。
