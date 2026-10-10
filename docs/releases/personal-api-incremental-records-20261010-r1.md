# 个人 API 使用记录增量化发布

## 发布身份与验收范围

关联[任务](../tasks/2026-10-10-personal-api-incremental-records.md)与[方案](../plans/2026-10-10-personal-api-incremental-records.md)，负责人Codex。用户2026-10-10授权"复现→找原因→写方案→开工→测试→提交→推送→部署生产"连夜自主完成，中途不停下提问。2026-10-10 19:45:48 promote切换成功、20:01:43发布终验通过、20:03:49归档完成、20:07:05收尾独立复核通过（均为Asia/Shanghai），已验收/收尾结束。

问题：AI工作台"AI使用记录"中个人API请求每条记录都打包该页整个聊天记录（含此前所有提示词和回答），单条最大超百万字符，传输/写库放大导致api error频发。生产只读复现（19:10–19:25，仅条数/字节/md5不导出正文）：`personal_api`会话消息总量约164万行而去重后唯一消息约1.7万条（约91.6%重复），逐条前缀递增特征确认。根因：`personal_gateway_proxy.py`的`event_for_response()`把`request_messages()`全量历史写入每条记录。

方案：写侧单点增量裁剪。新增`_incremental_request_tail()`：请求消息中最后一个assistant之前的所有轮次已由此前记录持久化，只保留其后的尾部（本轮新提示）；首轮无assistant历史全保留；尾部为空（历史以assistant结尾）兜底保留最后一条user保证记录非空；存储=增量尾部+本轮响应assistant。知识库存储流程、读侧API、前端、既有`ai_chat_sessions/messages`表结构零改动；存量历史数据不回改不删除。

## 版本与实际镜像检查

| 对象 | 旧版本 | 候选版本 | 生产实际状态 |
|---|---|---|---|
| 当前个人代理 | CID70583b4729de5ed2caeebb4bd80a02b2e2efd4eedafada960b1e321e7eb16b83／镜像sha256:6c9a5779643b…（基底） | 叠加镜像sha256:532a68da4610413d60bfc861addfb341a7a862bc6819964aa3bfe218cecbf6cc，tag smartbrain/personal-key-api:2026.10.10-incremental-r1 | 19:45:48 CID7e700797f7cc3981d41466cda2ae6af6c84d063308ab49cc4567b0fdbe231b20生效，沿用原名smartbrain-personal-key-api-20260923-filter-internal-r1、原Env/Cmd/HostConfig/三网络IP不变 |
| 源码 | 镜像内personal_gateway_proxy.py（打包全历史） | 候选SHA256 3f196fe9d0718f4461ccf20c0810496650e930613835815bc213a408dbc226da（CRLF），AST校验仅event_for_response变更+新增_incremental_request_tail | 19:45后`docker exec cat`实测文件SHA与候选一致 |
| 生命周期 | smartbrain-personal-gateway-current.service绑旧CID | 同unit重绑确切新CID | active/enabled，MainPID/ExecStart准确；writer补充清单/etc/smartbrain/runtime-inventory/request-project-attribution-20261009.json已更新；edge未动（双视图SHA c22e68d972aeb997dbf5328dd00ca1de968fabe7455e4b8eb23037d28ed78626） |

旧容器改名`…-rollback-incremental-20261010`停止保留；构建候选a52ee8b6…已停止；测试容器smartbrain-incremental-red/green/image-20261010-r1停止/no保留作证据（d7d34b99已rm）。主API容器内未使用的同名副本未改：edge不把个人API流量路由到主API，发布前后事件写入实例唯一（gateway-local），有机流量形状亦证明唯一写者。叠加Dockerfile位于deploy/personal-api-incremental-records/Dockerfile.personal-api，第二次提交补`--chown=10001:10001`保持文件属主。

## 切换与失败恢复计划

受控脚本一次性promote：双锁backup→maintenance，核对backup终态/无pending/四盘门槛/Compose登记20。候选容器独立ready核对26成员与匿名401后停止；优雅停旧、保留原名与网络身份给新容器、unit重绑、readiness通过。回退路径：停新容器、旧容器改回原名并启动、unit重绑旧CID，旧镜像保留在本地及归档。本次无生产DDL、无迁移、无Key/Token生命周期变更。

## 实际发布、验收与恢复证据

构建与测试：r1构建镜像层叠加候选文件；测试先在生产运行镜像内红（6 failed全部为新增量用例／32 passed／6 skipped，network=none、read-only，容器smartbrain-incremental-red-20261010-r1），挂载候选后绿（38 passed／6 skipped，green容器），再用构建产物镜像无挂载复测38 passed（image容器），证明镜像内字节即候选。本地py_compile通过。git提交807cedb（修复+7新用例+方案/任务文档+Dockerfile）与6c38321（属主修正）已推official/codex/project-memory-no-adapter。

19:45:48 promote成功。发布终验（20:01:43，release-verified.json）：1032个无关基线容器完整Config/HostConfig/Image与代际保持，当前1035容器/39运行；部署文件SHA匹配；edge双视图一致；health 26成员、限额8/24/60s/db3/16MiB、waiting 0/db 0；公网/login、/workday、/admin、/health/ready 200，/v4/ai-gateway/keys、/v4/personal-api/v1/models、/v4/personal-api/v1/responses、/v4/ai-usage/records匿名401；新生产容器内合成端到端deployed-checks.json passed——chat/Responses/SSE三路径增量尾部、首轮全保留、assistant结尾兜底、system/tool角色过滤、authorization不外发、5个独立合成请求，只读事务零生产写入、零真实模型请求。

有机流量形状验收（关键）：promote后约16分钟51个真实会话逐条比对（仅role序列/md5，不取正文），全部无"assistant后仍跟user"的交错——旧打包特征为零；与发布前旧记录（如08:45会话34条含交错assistant）对照确认判别有效。相邻会话头部重叠仅出现在user消息且属合法重试（首发响应为空存1条user、重试存[user,assistant]；同提示整段重发为新首轮），不是历史打包。real_model_requests=0、production_db_writes=0；指纹15595:1643395→15596:1643434为窗口内自然流量，发布自身零写入。backup inactive/PID0/Job空/success、登记20、无pending；四盘42.99/33.91/521.85/271.96GB均过40/20/250/250GiB门槛。

证据：远端`/srv/smartbrain/releases/personal-api-incremental-records-20261010-r1/evidence/`（production-before.private.json、baseline.json、build-verified.json、tests-image.json/log、promoted.json、promotion-baseline.private.json、deployed-checks.json、release-verified.json、archive-manifest.json、closeout-verified.json）；本地`.artifacts/personal-api-incremental-records-20261010/`（repro-output*、tests-red/green/image.log、verify/archive/closeout脚本）。敏感纪律：全程不导出正文，仅用条数/字节/md5比对。

## 未完成与保留边界

知识库（Company Memory/Wiki）提交流程不变，personal_api本就不进admissions、不走Wiki；对话记录知识库存储保持不变符合用户要求。存量历史（含约3GB重复打包内容）不回改不删除，仅新记录增量。客户端若在首轮之后仍发送完全无assistant角色的全user轨迹（个别agent循环），该轮记录无法区分新旧而保持全量——发布后实测仅1例（33条），其后同会话记录已增量；正常多轮客户端（有assistant边界）全部增量。request_message_count/context_source维持不设置（空响应会触发既有校验器）。本发布为writer补充清单级别，未纳入完整冻结backup协调器；不是全系统验收，原17项/全writer冻结/整机重启验收不因此完成。

## 归档与终态（2026-10-10 20:07）

20:03:49归档完成，远端`/srv/smartbrain-backups/backups/personal-api-incremental-records-20261010-r1`目录0700：旧+新两确切镜像images.oci.tar.gz为193027711字节、SHA bca17141f08512d04e8fe333a274844a383c78d21eac0155d12b081a1b65765d；私有证据evidence.private.tar.gz为1304959字节、SHA 7c11d3e83b72bd7ecb88ffdaa1db96ed0bdeb3006b8f00cf7ecf0fced1e883cf；两tar均0600，附manifest.json。含旧配置、部署源、测试红/绿/镜像日志、实际unit与writer清单；没有数据库dump，不是全冻结备份/恢复合格点。

20:07:05独立复核：重算两归档SHA一致，OCI导出旧/新镜像配置与完整RootFS层逐一匹配实际镜像；当前CID/Image/unit绑定、1035/39、无关基线保持；公网ready/models/records三项再通过；edge双视图SHA不变；backup登记20；四盘门槛通过。closeout-verified.json记录证据。所有本轮runner终态，无需接管或重跑promote/归档；禁止重跑切换。权威源码为C盘工作树，已提交推送official；E盘镜像按惯例同步文档与交付。