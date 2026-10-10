# 智慧大脑全面验收结果

记录更新时间：2026-10-09 09:43（Asia/Shanghai）。业务修复生产复验为2026-10-08 22:10/22:33；完整现场最终核对为2026-10-09 09:31，实际unit/入口09:33核对，匿名模型/退休入口09:36补验。文档更新时间不代替现场时间。

本轮测试已完成并清理验收身份，发现的三处业务缺陷已发布和复验；全系统验收结论为**未完全通过，尚未闭环**。原17项及四模型Codex G1没有被本轮矩阵替代。

## 验收范围和结果

| 范围 | 结果 | 证据与实际限制 |
|---|---|---|
| 前端完整回归 | 通过 | 40文件181测试；本地工作树测试，不等于每条生产页面行为都被覆盖 |
| 后端完整文件批次 | 初始失败，后继补验 | 实际主API依赖隔离容器67文件，61文件通过、6文件失败；此前任务误记60，本报告纠正为61 |
| Key操作与持久化 | 限定范围通过 | 独立PG20项；原生网关为合成替身，未签发/撤销真实员工Key |
| 对话真实PG | 通过 | 限定NOLOGIN/NOBYPASSRLS reader角色补齐后14项；首次环境缺失失败保留 |
| 项目AGENTS | 通过 | 实际资源补齐后10项；新合成项目默认v4，已有自定义文件保持 |
| 实际个人代理 | 通过 | 正确个人流量镜像清空默认Redis环境后8项；主API镜像的旧代理不是该入口活动实现 |
| MCP与资料读取回归 | 通过 | 最新MCP镜像54项，含relay静态配置；真实独立PG6项，包括实际版本diff SQL。未实际上传500MB |
| 会议旧测试 | 残余失败 | `.doc`拒绝预期与当前已支持`.doc`的实现契约不同；没有删除或修改测试以冒充全绿 |
| 对话摘要、幂等、统计、Wiki、会议读回 | 修复后通过 | 第一批75通过/7失败保留；最终合成业务22通过/0失败。新干净项目保存2条，成员各1条，统计各50% |
| 资料上传、审批与MCP正文 | 修复后通过 | API资料volume挂载补齐，原审批job第6次完成；未重建审批。资料正文3块、搜索、引用、结构、版本、只读Token及越权18项通过，原114字节文件hash保持 |
| 部署网页与角色 | 通过 | 负责人实际登录，AGENTS v4/对话合计2/独立插件更新按钮可见；普通成员无管理导航；控制台error/warn空。成员名单项目内公开为现有设计，未读取真实员工正文 |
| 公网与匿名权限 | 通过 | login/admin/wiki/knowledge/workday/profile/ready200；auth/Key/records401。09:36正确模型入口`/v4/personal-api/v1/models`401、旧device-ingest POST410 |
| 首次最终脚本猜测模型路径 | runner错误，已补验 | `/v1/models`404保留；它不是配置中的个人模型入口，不据此认定产品故障 |
| 个人工作记录 | 元数据核对通过，任务聚合未接通 | 用户09:15–09:17七个不同ID，六次Terra及一次审核；context_complete=false，没有可信共同任务ID，不能按时间强行合并 |
| online备份完整性 | 通过 | 唯一批次`20261008T033252Z`36文件SHA、4小tar安全结构通过；登记20服务，未证明全部writer闭包 |
| Redis隔离恢复 | 通过 | network none；stream16875、PEL0/group匹配。备份8key，恢复7key，RDB核验证明1已自然过期会话 |
| 完整PostgreSQL恢复 | 未通过 | r1权限/r2缺pg_net preload/r3 COPY700秒超时，失败保留，容器终态停止 |
| 7张关键PG表限定恢复 | 行数检查通过 | auth.users27/documents217/receipts0/member experiences1552/projects141/wiki pages88/users26；仅数据行数匹配，不证明全字段/索引/FK或完整恢复 |
| ClickHouse | 实际故障未修复 | 09:31活动错误仍有Code241 MEMORY_LIMIT_EXCEEDED；未调整生产内存或配置、未重启 |
| Docker容量 | 09:31不通过 | 可用42680668160字节，小于40GiB=42949672960；数据/备份/cold盘门槛通过，MemAvailable6618554368字节 |
| systemd生命周期 | 未通过完整验收 | 实际旧smartbrain-tunnel.service failed，Docker隧道正常；若干旧personal unit停用或失败；实际read/records frontend与personal-gray API/web-r3 active/enabled。未演练整机恢复 |
| Key reconcile/灰度 | 本期未启用 | timer disabled，management gate文件不存在，未为验收启用 |
| 全writer冻结、CH/models/material全物理恢复、四模型真实G1、真实员工Key全生命周期 | 未验 | 本轮发起真实模型请求0；用户自己的七次调用只读核对，不作为本轮发起的模型验收 |

各测试批次存在范围交叉，不相加形成“全系统总通过数”。后端第一轮本机依赖收集失败和后继镜像批次分别保留，不能把61文件通过改写为全部测试通过。

## 已发布的修复

1. 对话摘要检查新增`[analysis]`、`[COMMENTARY]`、`【思考过程】`、`[tool_result]`内部封装拒绝，四个Red后43专项通过。服务端检查长度及已知标记，不能辨别所有未标记的思考文本；插件仍必须只选可见请求和最终结果。
2. 主API新增共享资料volume `smartbrain_material-uploads:/var/lib/agentops/material-uploads:rw`。原容器层114字节合成文件先保留、hash核对后复制；不重建旧审批、不删除历史文件。
3. MCP资料读取优先v2分块，同项目同document没有v2时才回退legacy；保留approved/ready/current及ACL，search/get/part/compare统一兼容SQL。无生产DDL、worker切换或灰度启用。

2026-10-09 09:43只读核对，线上MCP的conversations.py与operations.py SHA均与本任务本地修复源相同；验证manifest另存closeout-verification.json。

实际版本和失败/回退详见[发布记录](../releases/full-system-acceptance-fixes-20261008-r1.md)。

## 最终现场及收尾

09:31共963容器39运行；相对于933基线的931无关容器Config/HostConfig/Image/启动代际保持。API与MCP为明确变更对象。edge宿主与实际挂载同SHA `c22e68d972aeb997dbf5328dd00ca1de968fabe7455e4b8eb23037d28ed78626`，本轮路由保持。

09:29已禁用3合成用户、撤销4MCP Token、完成3合成项目、关闭7Redis会话，合成会话剩余0。验收浏览器tab已关闭；09:31本轮测试/恢复容器运行列表为空，停止/no保留。真实唐伟翔账号、Token、Key与原对话记录未修改。

备份service success/inactive/MainPID0/ControlPID0/Job空，timer enabled；无maintenance pending。不是完整冻结备份或整机恢复合格点。

容量整理保存了71个已停止容器的87550689字节历史JSON日志和6个已闭合ClickHouse gzip日志306265319字节，完整复制到备份盘并核验hash；原Docker日志位置改为归档指针，`docker logs`不再包含这些容器全量历史，完整日志可在受控归档读取。活动CH日志、数据库、PID和配置保持。已执行prune/日志转存不得重复；持续增长仍需解决ClickHouse根因。

## 证据与接续

- 远端受控证据：`/srv/smartbrain/acceptance/full-system-20261008-r1/evidence`。私有原始配置、认证信息、完整日志与正文不进入普通文档或Git。
- 本地安全摘要：`.artifacts/full-system-acceptance-20261008/closeout-evidence`，包含`backend-deployed-result-r2.json`、`verified-test-summaries.json`、`postfix-business-results.json`、`material-postfix-results.json`、`backup-verified.json`、`pg-critical-restore-result.json`、`redis-restore-result.json`、`final-readonly.json`及`final-route-supplement.json`。
- 浏览器证据：本地`browser-owner-wiki.png/txt`。合计2等统计另有DOM读回，后续低位置截图不能冒充完整统计截图。
- 最新实际用户病例见[项目归属与七次调用诊断](../tasks/2026-10-09-conversation-receipt-work-records.md)。

接续优先核对ClickHouse内存超限根因和容量，满足门槛后再做新发布；随后按原计划补完整PG恢复、生命周期/全writer闭包、真实四模型及员工Key端到端验收。不得重放已结束的fixture、发布、审批创建、备份/恢复批次或cleanup runner。
