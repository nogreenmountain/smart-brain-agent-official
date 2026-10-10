# 个人请求项目归属限定发布

## 发布身份与验收范围

关联[任务](../tasks/2026-10-09-request-project-attribution.md)，负责人Codex。2026-10-09 10:24发布、10:25认证HTTP验收通过、10:29归档及当前入口独立复核通过，已验收/收尾结束。用户要求一条龙修复个人请求归属并确认七条历史按原意归智慧大脑agent；本期不恢复适配器、Key项目绑定或其他停用功能。

只替换当前公网个人代理三文件。每次请求从显式头或正式Codex AGENTS封装取UUID，真实项目成员校验；没有声明保持未归属。个人请求仍独立计量，不能触发全量Wiki发布。知识库仍由Company Memory按授权提交短摘要。

## 版本与实际镜像检查

| 对象 | 旧版本 | 候选版本 | 生产实际状态 |
|---|---|---|---|
| 当前个人代理 | CID7f3b8975…/imagef0c773cc… | image8e25962f559c443f10a62e9bdf12185be96f2320263f43a81bd1a599e7314588，smartbrain/personal-key-api:2026.10.09-project-attribution-r1 | 10:24 CIDb3caf14b214aff42077849e47d1892f8f50806305db82f10262151b60ff641dc生效 |
| 源码 | 实际运行镜像源，不用共享脏树整体覆盖 | personal_gateway_proxy.py a9536fd9…；ai_gateway.py e6288170…；request_project.py 4149519f… | 10:24实际运行三文件SHA一致，新镜像23项通过，无源码挂载 |
| 当前生命周期 | 当前代理无独立unit；旧gray-api unit绑定其他旧灰度容器 | 新smartbrain-personal-gateway-current.service绑定确切新CID | 10:24 active/enabled、ExecStart/Stop准确；旧gray unit与容器保持 |

旧ai_gateway实际raw SHA68dbeb3a…与早期读取规范化SHA20cb70fc…差异仅CRLF，规范化正文及AST相同。manifest保存raw前置SHA；所有未指定函数AST保持。

构建r1误将Image ID作Dockerfile FROM，构建器当远程仓库名而403，未切换。r2改核验本地tag后构建成功；测试收集因checkout包名agentops_local与安装包名agentops不同失败。r3只改测试导入到实际安装包名，同一镜像23passed/6.79s；前两失败原证据保留。真实隔离PG18项和Codex0.144.5封装捕获另见任务；无真实模型请求。

## 切换与失败恢复计划

受控脚本`.artifacts/request-project-attribution-20261009/promote_remote.py`一次性执行。双锁顺序backup→maintenance，核对backup终态、无pending、四盘门槛和Compose登记20、新镜像/旧源身份。先启动独立ready候选核对26成员和匿名401后停止；优雅停止旧当前代理、保存三网络IP/alias、保留旧容器新名字；新容器用相同IP/alias和原Env/HostConfig/成员权限，独立unit启动。edge字节和其他unit不改。

任一切换步骤失败，停止/断开新容器、恢复旧名字和各网络确切IP/alias、启动旧代理并核对配置hash/readiness；新失败容器保留。应用回退不撤销历史七条归属、不恢复旧库、不修改Key或Token。旧镜像和私有配置保留；没有生产DDL。

本轮为当前代理保存精确writer补充清单与部署证据。原backup Compose登记20的覆盖范围保持，该清单尚未纳入完整writer冻结协调器；不能把它写成全系统备份恢复通过。

## 实际发布、验收与恢复证据

10:20 r1启动检查过早：systemctl返回后Docker尚未running，通用ready立即报candidate process exited。切换失败进入预设恢复；由于stop在新容器启动期间发出，等待150秒终止后完成清理；10:23:05旧代理原名/确切三网络IP、配置hash/readiness实际恢复。失败容器和日志保留，不能把r1称成功。阶段查询曾误匹配完整私有baseline输出，后继限定只查明确无敏感阶段文件，不将私有配置复制到文档/Git/交付。

r2在systemctl start之后先等Docker running，再查health；10:24:23成功，原Env/HostConfig、26成员、三个IP/alias保持；edge没有改动或reload。新unit实际启动并绑定新CID，旧gray unit未改变。旧当前代理停止/no，ready候选及所有本轮测试容器停止/no。没有生产迁移、Key/Token生命周期变更或真实模型请求。

10:24:46实际源SHA、当前unit、8公网状态通过：login/workday/admin/ready200，匿名Key/个人models/个人responses/records401。真实生产项目SQL+已部署代理只读检查，头及AGENTS均识别智慧脑；缺失保持未归属，未知404/非法400/非成员403/冲突422均在模拟上游之前，规则不进消息，3独立fixture请求/各3fixture Token。认证claim、上游及持久化是替身且DB事务只读，不能称生产真实模型及完整写入验收；真实持久化由此前隔离PG18项验证。

972个无关基线容器完整Config/HostConfig/Image与代际保持，当前975/39运行。backup inactive/PID0/Job空/success，登记20；reconcile timer disabled、管理gate不存在、maintenance pending不存在。Docker44275523584字节、其他三盘均通过原门槛。

10:25:42另建300秒实际用户会话，经严格TLS公网records读取：七条全部正确project_id/project_name，Token合计124584、原7账单hash不变，1条用量仍unknown；未请求消息正文。会话finally已关闭。该HTTP产生正常访问审核，不改Key/Token、模型或Wiki。

证据：远端`/srv/smartbrain/releases/request-project-attribution-20261009-r1/evidence`中的promoted.json、release-verified.json、deployed-project-checks.json、history-http-verified.json；历史写回在acceptance同任务目录。本地安全结果`.artifacts/request-project-attribution-20261009/release-verified.json`。

## 未完成与保留边界

另一台电脑本机不可操作，必须使用正确UUID的[AGENTS](../deliverables/smartbrain-conversation-rules/AGENTS.md)并开启新Codex CLI会话；错误科研UUID会按该声明归科研，不能靠插件更新替换现有规则。没有标识的后台审核不保证归属。原09:17科研Wiki记录未移动、补发或删除。

原全系统验收的ClickHouse Code241、完整PG恢复、全writer/整机与四模型G1仍未完成。本次归属修复不将它们标passed。应用恢复r1实际执行通过，未执行数据库恢复、整机重启或最终r2应用回退。

## 归档与终态（2026-10-09 10:29）

10:26归档完成，远端`/srv/smartbrain-backups/backups/request-project-attribution-20261009-r1`，目录0700、两tar0600。旧/新两确切镜像images.oci.tar.gz为192992598字节，SHA555c3e640b95c45c7435553615e98588a568b2864f9c371cb1408a7091a78cda；私有证据1805579字节，SHA20baf6baf9fdf1d88ea8b95d32e5d5bd7883bf4a0e84e936b77bc9c4245aa80f。含旧配置、部署源、测试/失败/恢复记录、实际unit和writer补充清单；没有数据库dump，不是全冻结备份/恢复合格点。

10:29独立重新计算两SHA，核对OCI导出旧/新配置及完整RootFS层匹配实际镜像，实际当前CID/Image/unit与975/39、972无关基线保持，匿名入口/ready再次通过。Docker44234547200字节>=40GiB，其他三盘门槛通过。closeout-verified.json记录证据，所有本轮runner已终态，无需继续观察活任务；禁止重跑归档、七条写回或历史发布。权威源码仍C盘共享脏树，本轮未整体提交/推送，E盘仅镜像文档/交付。
