# Company Memory 更新渠道与安装器修复

- 任务：company-memory-updater-20261008；负责人：当前Codex。
- 授权：用户本对话要求判断问题后持续完成修复、部署和验收；无额外期限。
- 创建核对：2026-10-08 17:26（Asia/Shanghai）；2026-10-08 18:21已结束、生产已验收；完整现场核对18:18，归档及入口复核18:21。
- 权威工作树：C:/Users/test/.codex/worktrees/deb4/智慧大脑agent - 服务器端，codex/project-memory-no-adapter/431022b。共享脏工作树不整体提交；E盘旧源码不覆盖。
- [执行计划](../plans/2026-10-08-company-memory-updater.md)。
- 验收：网页无需新Token即可下载更新器，实际插件升级为最新版本、保留Token和MCP配置；安装版本和工具可核对，浏览器入口及公网资源匹配部署版本。

## 诊断和证据

17:22公网ZIP为0.2.0，17:24本地marketplace与插件清单为0.1.0。网页更新渠道缺失，安装器缺少版本验收。17:25隔离复现排除“重复add必然保留旧缓存”：更新源后重复add得到0.2.0。17:28补充纠正PATH检查：Get-Command codex漏检了codex.cmd，PATH CLI0.144.5可用，桌面CLI0.162.0-alpha.2也可用；两版隔离升级均通过。不能将CLI缺失或缓存推断为本机根因，也不能据此断言用户某次安装实际执行路径。Token接入与插件技能更新不同，本机安装源和缓存确实仍为旧版。

17:26生产921容器/39运行，主前端3a82c90e5583/image a78a41ab4a39，公网Wiki脚本与主前端相符，edge双视图f68aec19保持；backup inactive/PID0/Job空/Result success，Docker可用43269533696字节、内存可用6978600960字节。本地证据.artifacts/company-memory-updater-20261008，远端/srv/smartbrain/releases/company-memory-updater-20261008-r1/evidence，完整inspect只置私有位置。

## 运行任务和不可重跑

初始隔离复现与只读诊断已终态。没有生产变更、Token创建/撤销、模型请求或备份启动。后续先观察现有intent和结果，不重放前两任务已成功发布/fixture/归档或旧模型批次。

## 初始下一步（历史，已完成）

按计划写失败测试并实现更新器和页面；持续完成候选、实际升级、发布和验收，记录每阶段终态。

## 17:52阶段接续

- 17:40前端三个专项文件17项通过，tsc noEmit退出0。新测试先失败于缺少更新器和更新按钮；旧日志保留。
- 17:39真实隔离CLI四场景通过：旧版升级及重复更新、坏SHA安装前拒绝、CLI提交失败恢复旧源/版本、没有PATH CLI时使用桌面附带CLI。首次WinPS继承PowerShell7模块路径导致Get-FileHash缺失，显式加载系统Utility/Archive后通过；一次故障shim的ASCII中文路径错误保留，后继UTF8通过。
- 17:42本机真实升级0.2.0、用户/进程Token保持，认证MCP200/服务1.4.0/31工具/record_project_conversation可发现，真实模型请求0。旧安装源和旧版本缓存保留；本对话旧技能快照不冒称已热更新。首次管道Unicode路径损坏在执行前失败，后继UTF16 encoded调用成功，不重放升级。
- 17:49依赖准备r1失败：改变Docker RUN网络模式使既有缓存不能复用，none网络下npm DNS拒绝，生产未切换。原失败报告/log保留。r2恢复原依赖缓存模式后进入数据盘隔离编译，编译容器network none/restart no/3GiB限制。
- 当前仅候选构建运行：本地exec session94449；远端build-intent-r2.json及compile-created.json，观察build-frontend-r2.log和容器终态，不重放成功依赖阶段。构建后继续候选浏览器验收、单前端及更新脚本路由发布。

## 18:21任务终态

网页独立更新入口及PS1精确路由已发布。主前端7366d9d631ac/image5721eff53b7d、edge双视图c22e68d972ae；公网脚本/PS1/ZIP逐字节核对、28旧资源和原权限边界通过。部署前端+合成只读API浏览器按钮/下载/JS检查通过；合成用户截图不代表生产真实登录业务。

本机0.2.0实际升级且已有Token保持、认证MCP200/31工具/新record_project_conversation可发现；18:21版本启用再次读回。Token接入和技能升级不同，旧聊天需要新建对话加载新技能；不要把初期PATH或缓存猜测复活为已确认根因。

18:18完整终态：923容器/39运行，920其他既有容器配置/代际保持，候选停止/no，旧主前端脱网停止/no保留；QA代理、SSH和三监听归零。backup终态success、timer enabled/登记20，四磁盘和2GiB内存门槛通过。18:21归档三SHA及OCI身份、公网Wiki和更新器再次核对，Docker43001249792字节。没有DDL、生产Token操作、模型请求或备份重跑。

完整阶段结果、失败保留、回退与归档见[发布记录](../releases/company-memory-updater-20261008-r1.md)。构建、清理、发布和归档均已终态；无活动runner，不重放intent。共享脏树未提交/推送，E盘仅同步本任务文档。
