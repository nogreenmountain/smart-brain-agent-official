# ClickHouse指标宽表缓冲窄范围发布

任务：overnight-operations-20261009。准备与自审：2026-10-09 18:48–18:49（Asia/Shanghai）。状态：18:50生产执行通过，效果观察进行中。

问题：pool2/ratio1已减轻CPU叠加，但system.metric_log的1136列Horizontal合并在创建全部输出流时仍超出3.6GiB。相同版本r3默认缓冲复现Code241，64KiB表级缓冲完成同数据合并；r4两路并发合并零Code241、全部数值列聚合一致，真实system.metric_log配置重载/测试重启/测试回退保持UUID及历史行。见[诊断与自审](../plans/2026-10-09-clickhouse-wide-buffer.md)。

## 固定目标与变更

- 原CH CIDf0a0f6eb8827c8a84c908f89eb3fa8169e95d0bcfcf2dfe3e90882d8bffe6653、imagecd450891db46cc6ffe313ca2b0fb7dbfb897a6873ca74a724cbe050a2cf62621、StartedAt2026-10-09T09:49:40.337495161Z/PID930830。
- 原backup-disk.xml SHAecf3efd265105bff68ee400364c073f53e256da913b9255d418f7e253ee284b1、inode5374067/1001:1001/0664。
- 仅system.metric_log表级max_compress_block_size=65536；同文件原inode追加metric_log.settings包含原index_granularity8192与新缓冲。SYSTEM RELOAD CONFIG，无生产容器启停、镜像/CPU/内存/日志保留/业务表变更。新SHA执行后填写。
- 发布脚本promote_ch_metric_buffer_r2.py固定意图防重放、双锁与backup20/四盘/内存门禁、限时SQL。其余环境不变。

## 验证与回退门禁

完整容器Config/HostConfig/Image指纹与代际、metric及业务表UUID/结构/元数据行数、host/实际XML/预处理设置、8公网入口、个人current绑定/预算、edge双视图及备份。效果至少两个完整5分钟后继窗口，历史累计错误保持，不用清零冒充修复。

发生错误时确认原UUID再RESET SETTING，恢复原inodeXML字节并重载一次，不重启或循环尝试。r4仅证明测试回退；生产回退尚未执行。全库checksum、完整PG/冻结恢复/30真实员工容量不包含在本次验收。

## 实际结果

18:49:58–18:50:00，双锁、backup20登记、四盘及内存门禁通过，Docker43156217856/cold271852048384字节、MemAvailable7715618816字节。只执行目标ALTER和原inode配置追加/重载，XML新SHA **e14fd07b4f175eccaab22c1dfde8d5bb08ea377fdfceb8828e06db7dd56643cd**，metric UUID157524f1-02f8-4e4b-a5b2-5a9c0d0ce335保持。没有生产重启或实际回退。

18:51独立复核：1025个容器完整Config/HostConfig/Image指纹和全部启动代际/RestartCount保持，39运行，CH仍PID930830/17:49启动；23个非system业务对象UUID/结构hash保持，4个有数据对象元数据行数未减少；metric_log未更名。8公网200/匿名401、个人current精确绑定/8执行24等待DB3、edge双视图及备份20登记通过。所有隔离CH容器停止。

发布时Code2417705、最新错误18:49:57；18:51仍7705，metric active parts约323→38，较大Vertical合并进度0.659/约11.4MB跟踪内存，读取/写入2249547行。仅短窗口改善，两个完整后继采样窗口与整夜仍待；不能称所有内存/容量问题已解决。18:51cold270819864576字节（252.22GiB）、Docker43153403904（40.19GiB），继续薄储备预警，不进一步大测试/归档。

证据：.artifacts/overnight-operations-20261009/ch-{wide-buffer-r3,buffer-persistence-r4,metric-buffer-r2-result,metric-buffer-r2-verified}.json；远端对应限权证据保留。r3/r4、发布runner全部终态，不重放；原observer/heartbeat继续。

18:58：18:57计数仍7705/最后18:49:57，无新增；首个跨发布的18:54采样仍有旧错误，两个完全后继窗口待核对。修复及当前XML/manifest/release-lock/AI-DEPLOY已在official分支codex/overnight-operations-20261009推送，提交778349b18d8b00d635cf276051abd51b254a1b64远端一致，main不变。23部署工具测试/sources通过；文档镜像已核对，有限heartbeat ACTIVE读回。本阶段没有新增大归档，薄储备继续观察。
