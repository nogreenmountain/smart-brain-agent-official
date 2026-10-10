# 个人API请求项目归属接续

## 任务身份与范围

- request-project-attribution-20261009，负责人Codex，创建2026-10-09 09:50（Asia/Shanghai）；10:29已结束/生产限定修复已发布验收。10:18及更早检查点保留为历史。
- 用户要求修复“未归属项目”，并在本轮明确七条历史请求归「智慧大脑agent」dfaefd9a-8e5e-4775-bc18-e3d551c651e4。
- 计划见[执行计划](../plans/2026-10-09-request-project-attribution.md)。保持Key不绑项目、退出适配器、只有Company Memory上传短摘要。原科研Wiki记录保持，不修改真实Key或Token。

## 代码与版本

权威C盘deb4工作树，分支codex/project-memory-no-adapter、基线431022b；共享其他任务脏树不整体提交/推送，E盘仅镜像文档。实际个人代理CID7f3b8975…/imagef0c773cc…、read CID5c07fd26…/image985176d5…，2026-10-09 09:49核对。

## 基线与证据

远端`/srv/smartbrain/acceptance/request-project-attribution-20261009-r1/evidence`；本地`.artifacts/request-project-attribution-20261009`。初始检查脚本两次因docker exec缺-i没有将stdin送入Python，均只读，09:49修正后成功；无生产写入。

实际代理仅读X-SmartBrain-Project-Context，缺失返回None；当前退出适配器流程不再提供该上下文。事件投影用零UUID代表个人无项目。旧网关仍有自动全量Wiki分支，未来归属接入必须防止触发它。

## 2026-10-09 10:18检查点

09:52仅七条会话project_id按用户明确选择修正为智慧脑，附user_confirmed审核标记；09:53新连接实际read投影读回全部正确。七个request_id、账单/消息hash不变，存储Token124584，其中一条usage_missing仍为未知，不补称0Token已确认。原科研Wiki记录未移动或重发。证据history-repair-result.json/history-verified.json；严禁重跑历史写回。

未来候选仅接受每次X-SmartBrain-Project-ID或Codex正式AGENTS规则封装中的UUID，认证成员校验，非法400/冲突422/未知404/非成员403均在上游之前。缺失不猜项目；personal_api保持每请求独立用量、context_complete=false，只写个人工作记录，不触发全量Wiki自动发布。识别的AGENTS规则不进可见工作记录。没有恢复适配器或Key项目绑定。

识别10项、实际代理两批Red→Green最终13项、实际Codex CLI0.144.5首请求封装捕获通过（模拟400终止、CLI exit1预期、0真实模型），真实隔离PG+代理18项通过。PG是最小合成schema，认证claim/上游和排行榜函数为替身，不称完整生产认证/RLS。所有这几批runner和测试容器已终态，停止/no。

10:12实际源字节对照确认旧ai_gateway的hash差异仅CRLF规范化，规范化文字/AST相同；候选manifest追加真正生产原始SHA。生产代理没有额外运行层源码修改（docker diff仅缓存）。双锁发布须再核对容量和backup；10:08Docker43367845888字节>=40GiB通过，backup终态/登记20、无pending。

10:12发现smartbrain-personal-gray-api.service实际绑定较旧灰度容器7ab6dfac…，该容器仍运行；它不绑定公网当前个人代理7f3b8975…。本次保留旧灰度unit及容器，为当前个人代理建立独立准确生命周期绑定，不把旧灰度启动状态当公网代理受管理证据。现行backup Compose登记20只覆盖原登记服务，不能称非Compose个人代理已进入完整writer冻结；本次发布另保存精确writer补充清单、旧镜像和私有配置证据，原全writer门禁保持。

以上为10:18检查点，后续实际结果如下；不重放该阶段runner。

## 2026-10-09 10:25生产发布与验收

[发布记录](../releases/request-project-attribution-20261009-r1.md)：实际旧镜像仅覆盖三文件，新image8e25962f…；真实镜像23项通过。构建r1引用失败、r2测试包名失败和切换r1启动时序失败均保留；r1实际恢复10:23通过，修复等待Docker running后的r2于10:24:23上线，当前CIDb3caf14b…。

新smartbrain-personal-gateway-current.service active/enabled并精确绑定新CID；旧gray unit/容器保持。原Env/HostConfig/26成员/三IP保持，edge双视图SHAc22e68d972ae保持。972个无关基线容器配置及代际保持，975/39运行，本轮所有测试/ready候选停止/no。backup登记20/inactive/success，reconcile disabled、管理gate和pending均不存在。没有生产DDL、真实模型或真实Key/Token改动。

10:24公网8状态、实际源SHA及生产真实成员SQL只读检查通过；生产调用的认证claim、上游及持久化替身边界明确，不能替代另一台客户端真实模型验证。10:25实际300秒用户会话从公网records返回七条全部智慧脑，7账单hash/124584存储Token保持，1未知用量保留；会话finally关闭，未请求正文。

以上为10:25检查点；10:26归档已完成，10:29独立SHA/旧新OCI配置和层、当前unit/入口/容量/972无关容器复核通过，所有本轮runner已终态。私有归档路径/两SHA见发布记录，closeout-verified.json已保存。没有数据库dump，不是全冻结备份恢复证据。禁止重跑七条写回、归档、历史发布/fixture/模型/备份或恢复。

另一台电脑需替换正确UUID规则，现有AGENTS不因插件升级自动更改；原科研Wiki记录保持。全系统未闭环，原完整PG恢复/CH/全writer/整机/四模型G1未通过。本轮源及记录在C盘权威共享工作树，未整体提交/推送；E盘仅镜像此次文档和交付。没有运行中的本轮后台任务。
