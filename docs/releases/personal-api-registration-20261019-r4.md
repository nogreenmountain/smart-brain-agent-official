# 新账号个人 API 准入发布 r4

- 关联[任务](../tasks/2026-10-19-personal-api-registration.md)、[方案](../plans/2026-10-19-personal-api-registration.md)；负责人/验证人Codex。用户授权“已停止，切入生产”保持。
- 2026-10-19 18:32（Asia/Shanghai）准备中，尚未切换。发布与回退步骤、原业务/镜像/源码、无迁移和真实新号验收边界沿用[r3准备记录](personal-api-registration-20261019-r3.md)，仅全新r4目录/unit/候选/回退名称。
- r3因候选名称漏改而在preflight失败；原业务未停止。r4修正全部批次名称，driver SHA `67674809cd8b2e737181573fd9010b2679e46cd59c65ad585859eeca4088f800`。新增名称隔离测试Red明确复现，r4 22项全通过；不修改业务镜像。
- 镜像 `sha256:97c378c7e3f3d9a60cd00e5bdae53063da7814786695cef7f4caa4db6452edd4`；backup Invocation `68dcec4071f04a6c806763d4d72a40d7`，再次使用原成功批次与测试收据，无新备份/构建/生产Key创建。
- 上传先核对r3确切失败Invocation `4f064dcc591445fca1feb3aa340c1433`、只有failed阶段及旧业务与r2基线一致；新目录须不存在。启动仅一次，保留两次零在途、双锁、备份/四盘门槛和单次受控回退。之后仅观察原Invocation。
- 原配置/网络/HostConfig/长期流代理保持；正式app改为实时有效注册账号准入。无DB迁移/历史回写/Key重置。回退仅原应用/网络/unit/inventory，保留所有新增数据；真实生产回退尚未执行。
- 成功后独立核验实际源码、25个有效账号含3个旧名单外账号、47条Key聚合、无关容器/edge/Windows边界，并单次归档、文档镜像/推送。真实新号页面领取/模型使用尚待用户侧确认；online备份不冒充完整冻结恢复。

实际启动、发布、验收与归档结果随后追加；r1/r2/r3均终态不可重跑。
