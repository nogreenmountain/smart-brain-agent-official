# 当前源码分支验收

核对时间：2026-10-09 13:43（Asia/Shanghai）。Git 整理，未执行生产发布。

- 1425 个实际运行 Python 源文件逐个 SHA256 一致；1454 个本轮 Python 文件编译检查通过。
- 新工作树前端相关回归 9 文件、66 项通过。首次从仓库根目录调用 Vitest 未加载前端配置；切换到 smartbrain-dashboard 工作目录后通过，源码没有因此修改。
- 确切 personal-api 镜像在 network=none 的隔离容器运行 33 项代理／归属回归通过。首次测试包 namespace 解析失败；后继 r2 补正确测试目录包边界后通过，无生产数据库或模型请求。
- 1509 个选择路径及插件 ZIP 内文件与当前注入的私有凭据／成员 UUID 比对，命中 0；没有上传真实 Env、数据或私有配置。
- 除原字节快照外，`git diff --check` 通过。快照中的既有 CRLF 和历史空白按属性原样保留，使用 SHA256 验证；七组源码不归一为单一版本，worklog 挂载修复明确单列。

证据：受控 `.artifacts/reproducible-repository-20261009/source-verification.json`、`source-runtime-tests-r2.log`；前端本轮 Vitest 输出。历史完整 HTTP+隔离 PG 的 34 项和 5/10/20/30 梯度验收见 [代理 r2 发布](personal-proxy-concurrency-20261009-r2.md)，本轮没有重跑其生产发布。此验收不是新机器全栈恢复验收。
