# 每次个人API请求的项目归属修复计划

2026-10-09 09:50（Asia/Shanghai）。用户授权修复请求归属，并明确这七条历史请求归智慧大脑agent。保持取消Key绑定项目、退出适配器、短摘要专用上传的既有选择。

1. 以实际个人代理/read源码和用户七个请求的会话投影建立基线，不读取无关正文；判别“没有传项目上下文”和“读模型忽略项目”两个原因。
2. 用七个明确request/session ID修正该用户会话的项目字段，保存前态、确认成员权限和审核标记；请求ID、Token账单和不可变admission不改。认证读API核对七条标签和总用量不变，不补发Wiki。
3. 为未来请求验证显式项目请求头或Codex AGENTS规则上下文的接入，按当前认证用户校验项目权限，缺失/冲突不猜。先写失败行为测试再实施；不能通过按用户/Key设默认项目、时间邻近或扫描任意用户正文实现归属。
4. 归属到项目不能触发旧网关全量上传Wiki分支；仅Company Memory保存授权短摘要。真实隔离PG与实际代理协议/权限/用量测试通过后，再核对容量/备份/版本/回退，决定限定生产切换。
5. 最终记录已发布、候选和另一台客户端未验的实际范围。旧历史病例保留，新规则明确来源；不恢复adapter、不修改原Key/Token、不重跑备份/恢复/旧发布。

主要文件：personal_gateway_proxy.py、ai_gateway.py及请求项目识别/验证模块与专项测试；本任务以实际线上源码为发布底，不用共享脏树整体镜像覆盖。

官方Codex文档已实际读取：https://developers.openai.com/codex/config-reference/ 与 https://developers.openai.com/codex/cli/reference/ 。provider请求可带http_headers，但项目本地config不能覆盖model_providers；不误写无效的项目配置。初始真实现场Docker容量低于40GiB，不沿用旧通过证据发布。
