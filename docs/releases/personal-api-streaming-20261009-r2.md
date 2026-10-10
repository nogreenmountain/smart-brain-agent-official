# 个人API流式转发与超时修复 r2

任务[personal-api-disconnect-20261009](../tasks/2026-10-09-personal-api-disconnect.md)。2026-10-09 16:36（Asia/Shanghai）准备发布，尚未切换生产。用户授权接续故障排查和必要修复；历史发布脚本未重放。

## 故障与版本

16:15只读现场：四小时17个502全部120002–120046ms，代理ReadTimeout17；代理/edge无重启、OOM0、排队0、PG idle-in-transaction0。旧版同时缓冲SSE到EOF并在120秒总截止，持续正常合成流也复现502。

- 旧CID acbab2fcb677f0c3399aae43808dec00380c1ebb111ae6b228b46a3ff4a9c4b5 / image08f24c57…。
- r1候选03b707a8…修流式，但隔离PG发现历史完成字段强制true；没有生产发布，失败保留。第一次镜像测试误选历史af95e645…，失败保留，后继修正测试目标。
- r2候选6c9a5779643b6b6ee33f2df06a7cef7c2c15d5f688f31ac8a6bb8fd65065ae99；仅personal_gateway_proxy与实际个人API ai_gateway路由两源覆盖。proxy9f7ed873… / route2db168c8…，manifest在本任务artifacts。

## 行为与验收

stream:true实时转发；120秒无数据超时、1800秒绝对最长流时限。8执行/24等待/60秒及DB并发3保持；许可持有至响应/保存收尾，取消释放。最多捕获16MiB用于记录，超过上限继续传输但正文不标完整。EOF无terminal、provider failed、空闲/总截止/取消均分开失败记录，未知用量保留；HTTP已发200时不能更改响应码，以连接中断或原生失败event通知客户端。JSON保持120秒旧路径，未新增自动模型重试。

实际r2镜像41项真实HTTP/隔离PG回归通过：5/10/20/30请求阶梯、真实hash/账户/项目SQL、短事务、单账单、首包、取消、上限、失效权限、未知失败及完成字段。16:36同镜像130.12秒合成流通过，首包55ms，120秒idle与1800总限均原默认，模型调用0。

## 本轮发布与恢复步骤

本轮promote_remote先核对确切旧CID/镜像/源码、41项镜像测试和130秒终态；backup→maintenance双锁、备份20登记且inactive/success、无pending、四盘40/20/250/250GiB门槛。保存旧Config/HostConfig/unit/writer清单/edge，候选匿名401和health8/24/DB3。短暂等空闲，systemd停止原代理并排空，保留旧容器，再同三IP/Env/HostConfig clone新版本。current unit精确绑定与1830秒stop/1860秒超时；既有补充writer inventory改新CID。edge/DB/Key无变更。

失败按本轮保存的原身份恢复名称、三IP、unit及清单；旧容器保留，不恢复数据库。r2实际回退尚未执行。发布后必须独立核对源码、生产SQL只读鉴权/项目、公网入口、原其他容器完整配置与代际、旧候选停止及备份状态。实际结果待填。

## 实际发布与核对（2026-10-09 16:44）

16:39切换通过，当前CID70583b4729de5ed2caeebb4bd80a02b2e2efd4eedafada960b1e321e7eb16b83 / image6c9a5779…；current unit active/enabled精确绑定，1830秒stop/1860秒超时，writer补充清单更新。原Env/HostConfig/三IP/edge保持。旧acbab2fc与候选5060d559停止保留，没有DDL或Key操作。

16:40独立源码hash、8公网入口、生产账户/项目只读SQL检查通过。1018无关基线容器完整配置/启动停止代际一致、39运行、测试运行0；备份inactive/success/PID0/Job空/登记20，无pending。池1+3、DB3、8/24/60秒保持；当时2执行/0等待/DB占用0。Docker43262550016字节仅高于40GiB门槛约0.29GiB，仍不是容量充裕。

16:44上线后的26条自然用户调用（8 GPT/18 Kimi）均200，正文完成与实报用量保持，本轮没有主动真实模型调用。最长这批53秒；不把这批短请求称为真实员工超过120秒验收，后者仅合成130秒通过。

归档 `/srv/smartbrain-backups/backups/personal-api-streaming-20261009-r2`，单新镜像images/images.tar194435072字节/SHA52197abae6332c8b06dd72ab82c56ed53ecb22b6494e325203717e5db8cb0ae0；evidence.private.tar.gz1925103字节/SHAb7a3f291e6a8a0f574ffc40c8bfc00e32b09200062ca2a92bf2eefde2d2cf9c3，0600。包含新旧现场/失败/测试及绑定证据，不是生产完整数据备份。单镜像作为基线21镜像包的增量，部署文档保留base lock和delta lock，最终current lock校验。

发布准备时第一次因130秒测试尚未终态而拒绝、独立验收第一次因发布仍持锁而拒绝；均在生产改变前的门槛/只读失败，随后按依赖终态继续。不要把这些拒绝当生产回退。所有原始失败日志保留，不重放旧r1/发布/归档。r2实际回退未执行。

## 16:50–16:56独立收尾与上游边界

16:50新镜像归档SHA/OCI身份、私有证据SHA/0600、current21镜像全部匹配；当前源码、unit、edge双视图、1018无关容器配置代际再次保持，39运行、测试运行0、backup20登记。真实GPT6.1请求627576ms（10分27.6秒）成功200、正文完整/usage已报告，超过原120秒截断边界。当前2执行/0排队/DB占用0。

自然用户调用同时有gpt-6-sol失败event（HTTP200内部failed，记录502/不完整/unknown）和上游503；不是新代理ReadTimeout，个人代理日志没有新的超时或流错误。16:56本机192.168.10.146:9000实际Node代理24744、cwd CLIProxyAPI2只读核对，08:49:50Z的28665ms failed与PG28680ms对应，08:50:22Z的503/6961ms与PG7012ms对应，日志明确capacity/server_is_overloaded/service_unavailable_error。随后仍有同类上游过载。短暂客户端断开另记499，不能归于上游过载。

本轮修复网关总截止与记录字段，不承诺消除供应商模型过载。未改Windows上游配置/授权/重试策略，不新增自动模型重试或跨模型替换。安全摘要 `.artifacts/personal-api-disconnect-20261009/{closeout-verified,post-release-errors,windows-upstream-errors}.json`；完整Windows日志留原位置，远端补充日志0600，不重写已归档包。

17:00 official仓库新分支codex/personal-api-streaming-20261009修复提交b105937f60df956b32fc040ebe23974633c64f77远端SHA通过、main431022b保持。代理及runtime两源字节对应发布manifest；部署22项及Compose模板静态通过，单新镜像包可按delta lock验证导入，最终current21镜像通过。误推原origin的同名新分支已清理；本轮runner全终态。新机全量业务恢复和供应商过载不据此称通过。
