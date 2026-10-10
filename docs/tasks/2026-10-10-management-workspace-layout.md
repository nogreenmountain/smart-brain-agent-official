# 管理工作台布局与操作优化

任务 `management-workspace-layout-20261010`，负责人Codex。创建时间2026-10-10 10:03（Asia/Shanghai）。阶段：已验证；部署范围：本地候选，生产未部署。

用户要求减少项目列表大面积留白，整体调整管理工作台布局并优化操作逻辑。用户已选择“紧凑侧栏＋详情”，即左侧项目筛选/列表，右侧详情；创建项目按需打开，概览、成员与规则分区切换。本次不修改后端权限或数据模型，不实现另一任务中的AGENTS模板覆盖接口。

权威工作树：`C:\Users\test\.codex\worktrees\deb4\智慧大脑agent - 服务器端`，分支`codex/project-memory-no-adapter`，基线`431022b`。既有dirty修改保存，不整体提交/推送；文档镜像E盘。

## 设计与实施步骤

1. 以当前React页面和纯合成API夹具启动本地浏览器，记录列表卡与右侧详情高度、桌面/移动布局。当前结构为`items-stretch`、列表`h-full`与336px固定列表，嵌套创建/Profile列，Profile含完整AGENTS指导，易拉长左栏留白。
2. 改为紧凑左侧项目导航（分类、搜索、自然高度列表、我的项目快速入口），右侧当前项目详情；移除与右侧内容等高的项目卡约束。创建操作按需打开，保留创建权限、精确分类、确认删除/迁移/审批规则。
3. 详情分为概览、项目成员、AGENTS规则；全项目审批明确标注，持续可访问。切项目不保留旧项目的危险操作确认，窄屏自然堆叠，无横向溢出。
4. 先行为Red后Green，修改原布局耦合断言以验证新用户流程；执行相关专项、TypeScript与构建。用实际本地候选浏览器对桌面、较窄桌面、手机和项目数量边界核对截图/几何指标。
5. 自审与独立审阅；记录实际变更、证据和部署状态。生产发布需实时容量/维护门禁及当前发布来源核对，不能沿用到期夜间授权或重放旧发布。

## 验收标准

- 项目列表不因右侧长内容拉伸成大块白卡；少量项目按内容高度显示，多项目可滚动。
- 当前项目选择明确；搜索和分类可定位项目，列表空态给出下一步。
- 创建按需打开且成功后选中新项目；取消不创建。
- 项目概览/成员/规则可切换，权限边界、跨项目审批、知识库跳转保持。
- 桌面与375px手机无横向溢出，长项目名可读；无新增浏览器错误。
- 合成数据仅在本地路由夹具，不能复活刚封存的测试账号/项目或写生产数据。

## 2026-10-10 12:24 验证完成（本地候选，未部署）

核对时间：12:02–12:24（Asia/Shanghai）。本轮只改管理工作台前端与本地合成夹具，生产未部署、未启动生产模型或写生产数据。

实现文件：`smartbrain-dashboard/app/(with-shell)/admin/page.tsx`、对应 `page.test.tsx`。以本轮真实基线备份 `.artifacts/management-workspace-layout-20261010/baseline/` 比较，未把既有 dirty 修改计入本轮。当前源码 SHA256：page `F8CDFED451CAE2967152BB649537525A68A374BBC0FD452B7FEF7E6D77146DE8`，测试 `853D9BA24DEB60A4BBACB37EFE7759019FA6FE23700AF4DE53AF3B14E6D66228`。

页面采用紧凑“左侧项目列表＋右侧详情”：左侧分类/搜索/状态筛选、自然高度项目行、长列表滚动和“我的项目”入口；创建项目按需弹窗；右侧概览、项目成员、AGENTS 规则分区。搜索不改当前详情，切换项目会清理删除/迁移确认和旧作业状态；延迟记忆读取按项目请求代次丢弃；删除使用 functional setter；异步恢复/迁移完成后只在用户仍查看原项目时更新选择。创建成功同步目标分类与新项目、清除旧筛选；目录刷新失败时保留已创建项目并明确提示，避免重复提交。弹窗支持打开聚焦、Tab 循环和 Esc 返回触发按钮。

验证记录：

- `admin-layout-green-r4.log`：当时管理页 39 passed；最终 `focused-final-r2.log`：管理页41项与相关组件/API合计6 files、56 passed；`tsc-final-r2.log`：TypeScript `--noEmit` exit 0。
- `build-final.log`：Next 15.5.23 production build exit 0；仅保留既有 `PersonalApiKeys.tsx` hook dependency warning。
- `browser/acceptance.json`：开发模式 Playwright 合成 API，1440/1024/375 三种宽度、概览/成员/规则、筛选、取消创建、跨分类创建、30 项目滚动、空分类全局审批通过；无横向溢出、无 JavaScript 错误。最终几何：桌面左卡 676.5px、列表336px、列表下方34px（为计数/边框区域，不是空白拉伸）；单项目列表112px；手机规则页同样 overflow=0。
- `built-browser-qa.log` 与 `.artifacts/management-workspace-layout-20261010/built-browser/`：直接使用 `.next` 构建产物静态页面和本地合成 API，以上流程再次通过。未启动生产模式监听服务；一次尝试被本地自动审批策略以 `blocked by policy` 拒绝，开发模式和构建产物静态复核均已完成。

生产状态：未部署、未提交、未推送；C 工作树原有 dirty 修改保留。E 盘任务文档和 CURRENT 已镜像。后续如需发布，须另行取得发布授权并重新核对当前容量、备份、维护锁和源码来源。

## 证据与运行任务

证据目录：`.artifacts/management-workspace-layout-20261010/`。保留本轮前的两个源码基线、行为Red日志、最终专项与构建日志、开发/构建产物两套浏览器证据、`page-layout.patch`、`page-tests.patch`及镜像核对摘要。

14:40接续核对：两文件SHA仍与12:24候选一致，`git diff --check`通过；构建ID `ue4exIjY7R0btRUwMq912`，12:24静态构建浏览器报告为passed。3180无本轮监听进程，无浏览器验收runner残留；生产状态本次未核对，生产部署仍未执行。

## 2026-10-10 14:48 最终审阅修复与最终验证（本地候选，未部署）

核对时间：14:42–14:48（Asia/Shanghai）。14:42独立审阅在capacity中断前确认一项实质问题：删除请求在途时创建新项目，若随后目录刷新失败，创建fallback使用提交时`projects`闭包，已删项目会在UI复活。主代理以deferred删除/创建加catalog reject复现，Red保留于`red-create-delete-overlap.log`；独立审阅随后中断，未完整复核最终候选，不声明独立审阅通过，其余由主代理基线diff自审，见`final-review.md`。

最小修复：创建fallback改用`setProjects(current)`函数式更新且目录刷新失败时保留当前列表，只附加新项目；删除同时以functional setter移除“我的项目”快速入口中的相同ID。新增交错回归用例，验证已删项目不复活、其他项目保留、新项目选中、快速入口不留旧ID。

最终候选SHA256：page `CDB176B838F423D5D2491F88D2A4EC8DBF49BF1418C8DD4B12B552B3ED6DA3A1`，测试 `A8BBFEF29AE1E51302F7D19950E24FC86DCCEFCD49F23E1B1F00B274707B652D`；12:24的`F8CDFED…`/`853D9…`为上一候选，已非最新。本轮前真实基线仍保存在`baseline/`，`page-layout.patch`与`page-tests.patch`已按最终候选刷新。

最终验证：

- `focused-final-r3.log`：6 files、57 passed（其中管理页42项，含新交错回归用例），Duration 16.47s。
- `tsc-final-r3.log`：TypeScript `--noEmit` exit 0。
- `build-final-r2.log`：Next 15.5.23 production build exit 0，最终Build ID `bEv5Zbzl7T8Tu_7JqqN8j`；仅保留既有`PersonalApiKeys.tsx` hook dependency warning，无新增构建错误。`git diff --check`通过（仅LF/CRLF提示）。
- `built-browser-qa-r2.log`与`built-browser/acceptance.json`（14:48，result passed）：直接加载`.next`构建产物静态页与本地合成API、阻断一切非localhost请求；1440/1024/375几何、概览/成员/规则、搜索不改选择、状态筛选、弹窗键盘焦点、取消不写、跨分类创建并选中、单项目自然高度、30长名项目内部滚动、空分类全项目审批全部通过；各场景横向溢出0、JavaScript错误0，夹具仅1次预期变更写入。最终几何：桌面左卡676.5px、列表336px、列表下方34px为计数/边框区；单项目列表112px。

生产状态不变：未部署、未提交、未推送，既有dirty保留；本轮仅本地候选与合成数据，没有生产访问、模型调用或生产数据写入。
