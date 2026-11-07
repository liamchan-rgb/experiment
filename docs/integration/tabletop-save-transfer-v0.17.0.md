# 人物与行程存档导入导出

## 人物与行程存档导入导出 · 课堂v0.17.0/build22（2026-11-07）

本轮执行用户“开始下一步”，完成上次第一项存档导入导出。教师档案窗口右上“导入导出”，各人物/行程槽也可单独导出；单个或勾选多个槽组成JSON，系统“文件”窗口由用户选择保存位置。当前游戏进度需先存到行程槽；导出不覆盖工作档或槽，取消也无游戏副作用。人物仅含原姓名/现有装扮，行程保留完整地图/队伍/战斗队列/RNG/移动条/道路/镜头/历史，槽标题及原保存时间不变。

导入先读文件并校验，支持统一version1备份及旧人物槽/人物档案/行程槽/地图工作档四种JSON。预览来源、条目选择、逐类目标槽和已有标题，重复/非法目标拒绝，确认框逐项列来源→目标与覆盖数量。只写所选槽，不立即替换当前行程；之后返回档案页点读取才应用。安全作用域和后台文件处理，128MiB限制，错误/取消可见；从文件窗口返回保留选择和目标。私有表单/文件窗口不进公开渲染树，不额外生成地图或规则引擎。

覆盖前保存所有目标原始字节，包括损坏文件，再写pending日志后逐文件原子写；失败回滚整批，应用中断后下次槽读写先恢复原状态，原为空槽删除中断写入。恢复失败保留日志并阻止返回半份数据。导入页可从最近20份覆盖前备份重新进入预览，旧文件不删除；坏历史备份独立列错，原损坏字节仍保留，不声称修复坏原件。既有12人物/8行程槽、P7、历史与公开布局保持，无新美术，基础衣装标签更正但旧blue值兼容。

新增21专项。本地及实际CI完成389规则/后台+6绘本核心零失败，另4本地Python工具检查；设备Release实际编译`46ae062fbb17663f4b015b9ab847dbd4f67c8289`，run42392999420 attempt1。版本0.17.0/build22，最低iPadOS27.0、SDKiphoneos27.2，CRC/经典ZIP2.0/arm64/755/Metal/568源资源SHA/281编译名称/3挂载JSON通过，可执行文件不同build21。初稿run42392920498在补文件窗口返回状态保护后被新构建取代，未交付。未运行App/模拟器/实机，实际系统文件供应商/触摸/菜单/弹窗/投屏/性能由用户安装复核。

正常GIF为8秒、100×80ms离线流程示意，主线程四阶段接触表与逐帧解码已检查，不是App/UIKit截图、触摸或性能数据；示意文件窗口不进入游戏素材。源码快照`611acfbadd47300c0da04279e6605f65e7be3c82`与实际编译提交分开，标签`archive-save-transfer-meadow-v0.17.0-20261107`。完整源码/Git bundle/IPA/诊断/GIF已存archive-assets，逐文件ZIP/独立bundle恢复和fsck/全部公开文件GET通过，归档run42393595270；main只放索引。直接IPA完整GET200，62797083字节，SHA256`76915e2623346b619791927b4d52c8a70979ab004f220a5429922987ac694af2`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/10fcb0e9376f1c8ba7cf261955153a839aba5446/archive-save-transfer-meadow-v0.17.0-20261107/ClassroomStage2-v0.17.0-unsigned.ipa) · [正常速度导入导出示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/10fcb0e9376f1c8ba7cf261955153a839aba5446/archive-save-transfer-meadow-v0.17.0-20261107/save-transfer-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/save-transfer-meadow-v0.17.0-20261107.json)

experiment本体仍Build95，只同步本轮记录；不自动读取/上传教师设备内真实资料。后两步：行程与历史分类筛选；教师常用课堂配置预设复用。本轮未自动启动这两项。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/save-transfer-v0.17.0.md
