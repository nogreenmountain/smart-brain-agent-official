# 多人使用的硬件容量核查

负责人Codex；2026-10-09 11:12开始，Asia/Shanghai。用户已手动验证另一台客户端的对话提交及项目归属闭环，现请求判断多人同时使用时内存、硬盘等限制是否可能使该链路失败。

本轮只读核查当前生产硬件、容器资源门槛、数据库连接与业务持久化边界，保存安全元数据和容量摘要；不发起真实模型、不做生产写入压测、不扩容或调整服务。历史授权不自动恢复适配器、项目Key、Monitor、Langfuse或reconcile。预计同时使用人数已通过异步问题询问，不阻止独立核查。

权威工作树C盘deb4，分支codex/project-memory-no-adapter，基线431022b，已有共享脏树；不整体提交/推送，E盘仅镜像本轮文档。证据目录.artifacts/hardware-capacity-20261009；远端/srv/smartbrain/acceptance/hardware-capacity-20261009-r1/evidence。

验收标准：取得当前而非历史内存/CPU/磁盘与关键容器限制；核对PG、Redis、ClickHouse实际状态和记录链依赖；区分单人功能通过与多人容量未压测，给出可执行的优先级建议和证据限制。

## 11:20实际结果与收尾

用户明确预计10–30人同时发任务。当前16GB/6核12线程，MemAvailable约6.60GiB；Swap4GiB几乎满，短采样没有新换页/OOM。Docker约40.8GiB空闲、数据机械盘约251.8GiB，分别只高于原40/250门槛约0.8/1.8GiB；备份盘约522.6GiB。CH内部3.6GiB/容器4GiB、持续Code241、2核限额8秒全部80周期被节流，PG与CH共享机械数据盘。

实际个人代理1个uvicorn进程、QueuePool1+3/30秒；等待120秒模型期间持有连接。活动源码a9536fd9…在隔离内存SQLite/假模型/合成鉴权下，4并发全200，第5出现1个500；夹具等待缩短0.25秒，不是生产最大4人或10–30容量通过结论。PG其他client14、无锁等待；收尾单次idle in transaction1未作长期故障结论。MCP保存提交后才确认、Wiki失败可同submission重试；个人代理工作记录失败仍返回上游答复，需补可靠重试/告警。

完整[容量报告](../ops/hardware-capacity-20261009.md)列出软件优先级及32GB/独立NVMe数据盘的规划建议。没有执行修复/扩容或生产写入压测。全部runner终态，无新增监听、真实模型、账号/Key/配置变更或服务重启；11:20关键容器启动代际保持。

初次辅助脚本在旧个人镜像导入缺失模块失败，诊断保留；修正为只读文件hash后成功，不安装依赖。证据capacity/dependencies/concurrency-boundaries/isolated-pool-probe/final-readonly两端保留；不重放带assert防重复的证据脚本。

本轮变更仅本任务/报告/CURRENT及上述本地诊断脚本。共享脏树不提交或推送，E盘镜像文档/hash核对。下一阶段如继续实施，按报告先连接生命周期与隔离并发，再CH资源预算、失败补偿和磁盘/内存规划；不从历史记录恢复禁用功能或把原未通过恢复验收改passed。
