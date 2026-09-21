# M03 — content-rag

## 业务职责

负责文件接收、格式解析、内容标准化、文档块生成、embedding、reranking、检索和知识回答。

## 不负责

不负责项目成员权限、Wiki 审核、个人 Key、员工身份或部署。

## 当前实现

- `agentops_local/rag/`
- `knowledge.py`、`project_materials.py`
- `rag_services/embedding_service/`
- `rag_services/reranker_service/`

## 数据与接口

- 数据：`documents`、`document_chunks`、`document_chunks_v2`、材料元数据和对象存储。
- 输入：授权后的项目 ID、文件/文本、检索查询、模型配置。
- 输出：标准化文档、检索命中、引用、回答和索引状态。
- 公共接口：`ContentDocument`、`DocumentChunk`、`SearchPort`、`EmbeddingPort`。
- 内部接口：具体 SQLAlchemy model、embedding 服务 URL、chunk 算法。

## 权限与拆分风险

权限必须由 M01/M02 提供已验证的 resource scope，RAG 不应自行推断用户身份。当前 `project_memory.parsers` 与 RAG 共用解析实现，必须先抽出 content-kernel。

## 测试与部署

应有纯解析测试、索引测试、授权检索测试和替身模型测试。RAG 服务可以单独构建，但业务 API 仍依赖主 API 和 PostgreSQL。
