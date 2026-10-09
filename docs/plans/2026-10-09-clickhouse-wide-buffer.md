# ClickHouse宽表合并缓冲诊断与候选

制定、自审：2026-10-09 18:38（Asia/Shanghai）。沿用本晚运维授权，业务截止10-10 08:30；本阶段尚未生产变更。

## 当前证据

18:34–18:36：CH24.12.6.70、原CID/image及17:49启动身份保持。metric_log共1136列，其中1132个64位整数；325个active parts，310个Compact。此前捕获32/33-part Horizontal合并。默认vertical最小131072行，未达到阈值的Wide输出合并会同时写全部列。

最新Code241堆栈分类集中于MergeTreeDataPartWriterWide、Stream、WriteBufferFromFile及createMergeTreeDataPartWideWriter，无Reader/ColumnVector类别；分配失败发生在创建输出列流。该版本官方源码的Wide构造器对所有输出列addStreams，每列创建文件buffer和压缩buffer，均使用max_compress_block_size；MergeTree表0表示继承全局1048576。单个1136列Horizontal输出仅这两层缓冲就约2.22GiB，两任务超过既有3.6GiB内部限额。不同阶段叠加仍须实验区分，不能仅靠计算宣布确认。

假设排序：①宽表全部输出列预分配压缩/文件buffer；②多part读取块叠加；③部分历史稀疏列产生额外序列化流。先用相同镜像、合成1136列、Compact输入→Wide Horizontal输出，单独改变表级max_compress_block_size区分①与②。原pool2/ratio1保持。

## 隔离实验

- 新唯一r3测试容器，原镜像、无网络/端口、restart=no，2GiB硬内存/内部1.5GiB、0.5CPU，不挂生产数据。不复用或重跑原r1/r2。
- 32个400行合成Compact parts，共12800行；输出超过Wide格式门槛且低于vertical行数门槛。记录默认合并Code241/堆栈类别，再仅将该测试表max_compress_block_size从继承1MiB改65536，验证相同数据正常合并、count及所有数值列聚合保持。
- 实验前重新满足40/20/250/250GiB储备、MemAvailable≥6GiB、backup inactive/no job/无pending。数据加日志有界256MiB，时间有界；异常停止测试容器并保留证据，不循环重启，不删除。
- 如未复现默认错误，或候选未合并/数据不一致，保留失败并继续只读诊断，不发生产。

## 生产候选门禁

仅实验确认后设计最小目标表变更及部署一致性。优先表级metric_log max_compress_block_size=65536，避免影响业务表、降低日志保留或扩大内存。必须验证实际system日志表配置/重启行为，不让配置变化自动将历史表更名；必须保存原表元数据设置、文件、回退方法和全容器基线，并在backup→maintenance双锁内重新检查储备。未验证之前不ALTER TABLE、不改XML、不重启生产。

潜在代价是压缩率和文件IO变化；候选记录输出体积、算法、内存与耗时，发布后至少两窗口观察错误增量、parts推进与储备。夜间小样本不替代完整冻结恢复或30真实员工容量验收。

## 自审

通过有界隔离实验；尚未批准具体生产脚本。实验针对已捕获输出分配错误，一次只改表级buffer，保留原失败和2/1局部改善。当前磁盘余量薄，任何资源门禁失败立即停止后继测试/发布。

## 18:48候选结果与生产方案补充

r3实际复现32 Compact→Wide Horizontal在默认缓冲触发Code241；单改max_compress_block_size=65536后同12800行、1132列聚合SHA完全相同，合并成1个Wide。r3累计错误1→2含默认在途任务收尾，不能据此说候选阶段零错误。

新r4使用4GiB容器/3.6GiB内部限额（与生产一致，启动仍要求6GiB可用并保留2GiB），256MiB足迹预算、240秒时限。两个1136列/32parts同时Horizontal合并均完成，合计跟踪内存采样最大966438014字节，Code241=0；两个数据聚合SHA与r3相同。真实system.metric_log ALTER→配置重载→测试重启，UUID保持、没有metric_log_N，表级设置与新配置一致；RESET SETTING→原配置→测试重启同样保持UUID/行数。这是测试容器实际回退，不是生产回退。r3/r4均已停止/no保留，实际足迹66.8/145.7MB，不重跑。

批准以下最小生产路径并自审通过：不再重启CH，仅ALTER TABLE system.metric_log MODIFY SETTING max_compress_block_size=65536，同时在现有backup-disk.xml原inode追加metric_log.settings = index_granularity = 8192, max_compress_block_size = 65536，再SYSTEM RELOAD CONFIG。XML当前没有metric_log块，预处理当前metric_log没有engine/自定义settings/TTL/order/storage_policy，默认结构已核对；显式index_granularity与原表一致。r4证明同一原表在当前运行及下次重启继续使用，避免单独ALTER后未来自动更名。

生产脚本必须双锁、backup20登记、最新磁盘和内存门禁，核对原CID/image/StartedAt、宿主与实际XML ecf3efd2及inode/权限/属主。保存当前全部容器Config/HostConfig/Image指纹和启动代际、各非system表UUID/结构hash/active parts行数、metric_log原UUID和结构hash及配置原字节。记录不可重复intent；SQL有锁2秒/执行5秒上限，失败按实际元数据确认后RESET原缺省并恢复原文件/重载一次，不循环重启。验证原metric UUID和所有业务表/容器代际、入口/edge/backup，再看至少两个完整后继窗口的Code241增量/合并推进/空间。

回退无生产数据恢复/删除，恢复原表缺省和原XML，pool2/ratio1保留。配置操作仅数百字节，不build/大归档；储备失败不执行。更小块可能影响压缩率和IO，整夜观察，不承诺所有历史错误一次解决。
