# 个人 API 使用记录增量化计划

2026-10-10 19:30（Asia/Shanghai）。用户授权：在知识库对话记录存储保持不变的前提下，把 AI 工作台“AI 使用记录”里个人 API 请求的记录逻辑从“每条打包整个页面聊天记录（含此前提示词和回答）”改为“一步一步、一点一点”的增量记录；流程为复现→找原因→方案→修改→测试→提交→推送→部署生产，中途不停下提问。

## 复现结论（生产只读，2026-10-10 19:10–19:25 核对）

- 数据路径：OpenAI 兼容协议无状态，客户端每轮必须重发完整 messages 历史 → `agentops_local/api/personal_gateway_proxy.py` 的 `event_for_response()` 把 `request_messages(request_payload)`（全部可见历史）与 `response_messages` 整体写入事件 → `_ingest_gateway_events` → `_materialize_personal_api_conversation` → `ai_chat_sessions` + `ai_chat_messages`。前端“AI 使用记录”经 `/v4/ai-usage/records` + `_attach_messages` 把整段历史逐条返回。
- 生产证据（smartbrain-prod 只读，仅条数/字节/md5，未导出正文）：
  - personal_api 会话 15,475 条；消息 1,639,756 条 / 3,062 MB；去重后唯一内容仅 16,883 条 / 258 MB（≈91.6% 为重复转存，约 12 倍膨胀）。
  - 员工 songhao 2026-10-09 起 640 条会话窗口：311/639 个连续对满足“前一条消息序列是后一条的完全前缀”（其余为该员工并行多个 CLI 会话交错）；链内消息数 1→3→4→6→8→10 递增，单条字节 21KB→63KB 随轮次堆积。
  - 最大单条记录 1.24 MB / 499 条消息（songhao，2026-09-23）。
- 用户关于“传输失败导致 api error”的猜测成立为现实风险：单条记录随对话轮次无限增长，写库行数 O(N²)、读取与传输负载同步放大。
- 证据：`.artifacts/personal-api-incremental-records-20261010/`（repro_readonly*.py、repro-output*.json/txt、prod_file_sha2.py、prod_inspect.py）。

## 根因

客户端重发全部历史是协议要求（无法也不应改）；错在**记录侧把传输格式当作“本轮新增内容”存储**。每轮记录都包含第 1..N-1 轮的全部提示词与回答。

## 方案

1. 写侧单点修复 `event_for_response()`：请求消息先按既有规则投影（过滤 system/developer/tool 角色与 AGENTS 指令块），再裁成**增量尾部**——最后一条 assistant 消息（上一轮响应，已由上一条记录保存）之后的消息；历史中无 assistant 视为首轮全保留；尾部为空时兜底保留最后一条 user 消息，保证记录不为空。追加本轮响应消息不变。Chat `messages` 与 Responses `input` 两种负载共用此逻辑；缓冲与流式两条路径共用同一函数。
2. 明确保持不变：
   - 知识库/对话记录存储结构与流程不动：仍然每个请求一条 `ai_chat_sessions` 与对应消息行；`project_conversation_records`/Wiki 路径本就不处理 personal_api（`event.app_type != 'personal_api'`），不受影响。
   - 读侧（`ai_usage.py`、`gateway_content.py`）与前端不改；每条记录自然只含本轮内容。
   - `request_message_count`/`context_source` 维持不设置（个人代理现状；增量语义下响应为空时设置边界会触发既有校验器拒绝）。
   - 存量历史记录不回改、不删除。
3. 先红后绿：新增增量裁剪专项测试（多轮历史只留本轮、首轮全保留、尾部为空兜底、Responses input 变体、历史角色过滤、错误响应仍记录），再实现。
4. 验证：后端 pytest 相关目录全量、Python 编译、`git diff --check`；前端无改动则如实记录未触碰。
5. 部署：按 agents-template-release-20261010-r1 已验证的单文件叠加流程，仅对 personal-key-api 服务（`agentops.api.personal_gateway_app:app`，当前镜像 6c9a5779643b、容器内活动副本与工作树 SHA 9f7ed873 一致）构建叠加镜像；门禁为双锁、verify_backup==20、四盘 40/20/250/250GiB 与 2GiB 内存、promote、公网验收（含一条真实个人 API 请求验证新记录只含本轮）、终态观察、归档、发布记录与 releases/README、CURRENT、推送、E 盘镜像。
6. 不扩展授权：不改协议与客户端、不动 Key/配额/模型、不回填历史、不重启无关服务；主 API 容器内未被该服务使用的同名副本不因此次发布改动（如实记录）。

主要文件：`agentops_local/api/personal_gateway_proxy.py`、`agentops_local/tests/test_personal_gateway_proxy.py`；部署叠加 `deploy/personal-api-incremental-records/Dockerfile.personal-api`。