# 新账号个人 API 准入发布 r3

## 身份与授权

- 发布：personal-api-registration-20261019-r3；关联[任务](../tasks/2026-10-19-personal-api-registration.md)及[方案](../plans/2026-10-19-personal-api-registration.md)。
- 用户明确“已停止，切入生产”；负责人/核验：Codex。2026-10-19 18:27（Asia/Shanghai）核对后准备，尚未执行切换。
- 原r1/r2在排空门槛前失败且未切换，禁止重跑。r3使用新目录、unit、候选/回退名称；同一已测试镜像，无重新构建/扩容/清理/备份。

## 固定版本与现场

- 原CID `052676a8caaff02578b73a25f10258da0d11350f164e4a94469d7912f2dae35e`，image `sha256:28cd0714f8ebdb214ad259444e4a9123b1d5d6ec4b89bf93fd48a40bd19e1cb1`，StartedAt `2026-10-18T14:43:13.86527095Z`。
- 候选image `sha256:97c378c7e3f3d9a60cd00e5bdae53063da7814786695cef7f4caa4db6452edd4`；实际镜像隔离PG/HTTP r4通过，零生产Key/模型调用。
- scope SHA `2878fb16424cdd9d13e9442050971211a29631467914b8f624e3287c23db8534`；app SHA `c804ec8fdd3f3f8c6fbeb03ee5c280c2f493736e77838bc0134af6babe2ae1ad`；proxy `075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe`保持。
- r3 driver SHA `c268130b3dcf7877db9f542193fc972182f261bc368ee205ad0bbdcba2a2be3b`；仅从r2替换本次身份，300次有界排空/两次零在途门槛保持；本地21项通过。初次未加载既有pytest依赖失败保留，指定本任务test-deps后通过。
- 18:27:39原服务 active/enabled，执行0/等待0/DB0；47条Key指纹 `92286ee623b3d5708891f3a6faafb074`；25个有效账号其中旧名单外3个。1061容器基线，edge双视图c22e68d9一致。
- online备份 `68dcec4071f04a6c806763d4d72a40d7` inactive/success/PID0/Job空，登记20；16:40核验收据仍有效。四盘free bytes 44900036608/33007861760/347418877952/271521247232，MemAvailable6602358784。

## 单次发布及回退

1. upload_r3.py 在双锁下核对r2确切失败Invocation/候选停止、原业务配置/网络保持，创建全新r3目录并复制原测试/备份收据。
2. start_release_r3_remote.py 先复核门槛，再以systemd-run --no-block启动一次；后续仅observe原Invocation。
3. 发布器验证候选实际源码/健康，复核门槛和两次无在途；停原current unit，断旧网络并保留回退容器，创建同配置新容器并精确绑定current。核验公网/Windows边界，更新writer inventory。
4. 切换前失败不重启业务；切换后失败仅一次恢复原容器/网络/unit/inventory，仍先排空新服务，不强杀长流。无DB迁移/Key重置或数据恢复，新增Key/撤销状态保留。
5. 成功后独立只读核验实际app准入全部有效账号、Key聚合、无关容器与edge，单次镜像/私有证据归档，文档镜像及推送。

## 验收边界与待补结果

真实新号页面领取及模型使用须用户侧确认，不以隔离PG或只读准入冒充。原备份为online；完整冻结恢复未验收。生产实际回退未执行。发布/独立核验/归档结果待后继追加；证据位于 `.artifacts/personal-api-registration-20261019/` 与服务器对应r3目录。
