# 新账号个人API准入发布 r2：切换前等待门槛退出

核对时间：2026-10-19 16:53（Asia/Shanghai）。关联[任务](../tasks/2026-10-19-personal-api-registration.md)及[方案](../plans/2026-10-19-personal-api-registration.md)。状态：候选已验证，未切入生产，等待空闲窗口。

## 版本与验证

正式分支`codex/project-memory-no-adapter`；修复89d5f61，Dockerfile权限e7d2991，回退名称边界77778be，r2发布工具26a4f43，均已推official。实际镜像`sha256:97c378c7e3f3d9a60cd00e5bdae53063da7814786695cef7f4caa4db6452edd4`，tag`smartbrain/personal-key-api:2026.10.19-registration-r1`。r2复用同一产物，没有重新构建或重跑PG测试。

仅叠加scope/app。实际SHA分别为`2878fb16424cdd9d13e9442050971211a29631467914b8f624e3287c23db8534`、`c804ec8fdd3f3f8c6fbeb03ee5c280c2f493736e77838bc0134af6babe2ae1ad`；原proxy`075b650186ad79cfec6b74eb8cb257ceabe8fee7426016f91308c1acb6cc09fe`不改。修复正式入口固定26人名单；仍实时验证有效注册状态、配额、归属、禁用/封禁/删除/匿名边界。

20项scope、合并22项回归/1无关项deselected、21项发布工具通过。16:41实际镜像r4独立PG及socket HTTP组合1 passed：新账号首Key、默认额度1、6并发仅1成功、跨账号隔离、旧新Key hash/SQL、停用及再次创建、8/24/DB3。镜像源未被挂载替换。会话解码和模型响应为合成替身，零生产Key创建/模型调用，不等同真实用户领取。

## 空间、备份与实际发布

- 用户授权2GiB后，15:29 Docker LV/ext4在线扩容成功。15:37仅删除逐文件与正式归档相同的三份CH staging副本，释放30.887GiB，正式归档不删。这些终态动作不可重跑。
- 原唯一online备份`68dcec4071f04a6c806763d4d72a40d7`成功；批次`20261019T073739Z`。16:40核验36项自校验、31小文件独立SHA、根身份及登记20；5大payload按精确Invocation自检，未独立完整恢复。发布继续使用既有四盘与内存储备，未降低门槛。
- r1从16:42:22至16:43:34，Invocation`c3b25e0450ce4c99aafdd64768c7b98a`；候选通过，60秒未排空，在cutover前失败退出。启动调用的systemd-run等待超时已按确切unit/ExecStart/SHA核对原进程，没有重复启动。
- r2根`/srv/smartbrain/releases/personal-api-registration-20261019-r2`；driver SHA`d93278ba620ba9d6bda16e307d11a99c59bb79cd1d3d9e584adc91d04d4b762c`，非阻塞启动，300次有界排空检查。16:46:44启动，Invocation`b37eea7487cd4d9e8282cb6ab74b8529`，16:51:59因持续在途请求退出。终态failed/exit1/PID0/Job空，new_id=null；未进入cutover，没有停止旧业务，没有实际回退。r1/r2均不可重跑。

## 16:53 独立终验

原1059容器的配置、镜像、运行/启动代际全部保持；仅新增两候选06d8dc49/a976843c，均停止。当前个人仍CID`052676a8caaff02578b73a25f10258da0d11350f164e4a94469d7912f2dae35e`、image`28cd0714…`、StartedAt`2026-10-18T14:43:13.86527095Z`，current unit active/enabled，Invocation`c1554993c4ba4e9c85ce6fa887082f5e`。47条Key聚合指纹`92286ee623b3d5708891f3a6faafb074`保持；edge宿主/实际挂载SHA`c22e68d972aeb997dbf5328dd00ca1de968fabe7455e4b8eb23037d28ed78626`保持。

公网login/ready200、匿名keys/models/responses401；9000员工直连403/内部标记匿名401，未改Windows。当前3执行/0等待/DB0，8/24/DB3上限保持；Docker/root/backup/cold空闲44910219264/33017987072/347418877952/271470034944 bytes，内存可用6580117504 bytes，原备份成功/登记20。

尚未上线，新号实际领取未验收。已请求暂缓新请求并等待当前生成结束，再以新发布身份执行已授权切换；不要求重新提供Key。没有后台发布进程或新定时任务。生产镜像/配置归档、真实领取、生产回退及完整冻结恢复均未执行。

证据：`.artifacts/personal-api-registration-20261019/`的`backup-verified.log`、`build.log`、`isolated-pg-r4.log`、`release-r2-tests.log`、`r2-uploaded.json`、`release-r2-observed.log`、`independent-blocked.json`、`blocked-final-comparison.json`；远端两个发布根保留历史状态和私有配置。禁止输出Env、Key、Cookie或员工正文。
