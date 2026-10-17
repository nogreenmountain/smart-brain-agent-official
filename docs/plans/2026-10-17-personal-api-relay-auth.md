# 个人 API 到 Windows 9000 中转站的认证适配方案

## 目标

修复个人 API 经过智慧大脑代理访问 `192.168.10.146:9000/v1` 和公网 `/v4/personal-api/v1/*` 时因缺少个人 `Authorization` 而返回 401，同时保证个人 Key 不会被发送到最终模型服务。

## 已确认的根因

- 2026-10-17 生产只读复现显示 9000 现在要求真实的 SmartBrain 个人 Bearer Key；无认证和无效 Key 均返回 401。
- `agentops_local/api/personal_gateway_proxy.py` 在构造上游请求头时一直删除 `Authorization`。
- Windows 9000 会先用该个人 Key 调用 SmartBrain `authorize`，再替换为内部 CPA Key 转发到本机 3000；因此代理必须把 Key 交给 9000，但不能越过 9000直接把个人 Key发给模型服务。

## 实施阶段

1. **红测与最小代码修复**
   - 个人代理支持显式 `SB_PERSONAL_UPSTREAM_AUTH_MODE=smartbrain_relay` 和 `opaque`。
   - relay 模式只转发已通过本地 `_gateway_claims` 的原始 Bearer `Authorization`；项目上下文、Hop-by-hop、其他凭据头继续剥离。
   - 上游根地址允许配置为 `9000` 或 `9000/v1`，内部只拼一次 `/v1`；relay 模式严格限制到受信 `http://192.168.10.146:9000`。
   - 未知模式、无效 URL、未提供本地验证头时拒绝启动或请求。
2. **隔离验证**
   - 单测覆盖 relay/opaque、头过滤和 URL 归一化。
   - 合成 HTTP 链路确认 9000 收到个人 Bearer，模型下游只收到内部 CPA Key（由 Windows relay 自己完成替换）。不使用生产 Key、正文或真实模型。
3. **受控生产发布**
   - 只对当前 personal-key-api 做单文件叠加镜像，并显式注入非敏感 `SB_PERSONAL_UPSTREAM_AUTH_MODE=smartbrain_relay`；保留旧容器和精确 unit 回退绑定。
   - 发布前复核 backup 登记、maintenance pending、四盘空间和内存门槛；容量不足不构建、不清理历史证据。
   - 发布后核对 direct 9000 与公网 personal API 的匿名 401、有效个人 Key 的 `/v1/models`/`responses` 至少一条合成或授权请求、容器/unit/网络身份及错误计数。

## 不在本轮范围

- 不把个人 Key 改成 CPA_UPSTREAM_KEY，不改 Windows 9000 或最终模型服务。
- 不改数据库迁移、Key 生命周期、`llm_credential_refs` 双表认领、重试/模型选择或工作记录结构。
- 不删除历史容器、日志、parts、备份或执行全局 prune。

## 回退条件

若新容器启动、配置或有效授权请求任一失败，立即按本轮保存的旧 CID、镜像、unit 和网络身份恢复；不做循环重启，不改数据库。
