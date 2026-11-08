# 人物自定义接入课堂

## 人物自定义已接入课堂 · v0.19.0/build24（2026-11-08）

用户“接到人物自定义”本轮已落实到课堂运行端。教师“管理→人物档案/行程槽→人物档案”可选六发型、四五官、星辉甲B天仪礼甲/龙纹甲B龙翼巡游甲。hair/face稳定ID可独立混搭，旧body/outfit及旧档保持兼容；人物槽、新行程、完整行程、历史/导入导出与P7保留同一选择。探索、背包、战斗与阴影共用人物记录，装扮不改属性、武器仍跟装备；公开端不显示教师编辑器。

美术固定来源`13cbe2e250a74a1a8e5c4a0dd026c866fd2cdfa8`，F1为原正面盖耳r4；不再用r3短发。5406源依赖Git blob/SHA核对，派生130图像名/260文件，旧175c7dfc全局基线保留，逐文件混合来源；829资源SHA、411编译资源名、3骨架JSON通过。原八向104姿势、起停/120ms与四武器七状态不改。正侧面近臂/袖前景沿原层次；native弓新rest头跟一次torso。换装时仅合成所需图集，无逐帧CPU重合成。实际App组件4992全身对比RGBA零差异；源战斗PNG未重画，正常GIF2700ms/80实际帧、独立浏览器11个不同采样。主线程看整身总览与首中末实际GIF，不把机械穷举当全部人工目检。

真实设备Release编译`40335ca5f8c6ba876d59c279f2b05c8a20dec30a`、run42480618163 attempt1，413规则/后台+6绘本核心零失败，另8工具检查。CRC/经典ZIP2.0/arm64/755/版本0.19.0/build24/Metal/全部来源资源与骨架检查通过，二进制不同build23。源码快照`01c222385be32310334b45ae38c0dcfab65d1db1`与编译提交分开；标签`custom-appearance-meadow-v0.19.0-20261108`，源码/图集/JSON/工具/Git bundle/IPA/GIF永久存archive-assets，独立bundle恢复/fsck/逐项公开GET通过。直接IPA再次完整GET200、78656566字节、SHA256`94aae4eb1b3449ebf4768b665bd251e65a99c8cbc96d1b2a3db302bcf2a881de`。归档run42481372759，回执收尾不递归存档。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/1bd467d43e70d7dcb8f00decece403a104a4144c/custom-appearance-meadow-v0.19.0-20261108/ClassroomStage2-v0.19.0-unsigned.ipa) · [正常速度全身GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/1bd467d43e70d7dcb8f00decece403a104a4144c/custom-appearance-meadow-v0.19.0-20261108/custom-appearance-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/custom-appearance-meadow-v0.19.0-20261108.json)

仍无App/模拟器/实机运行、无子智能体；真实iPad点选/存取/跨场景与电视/性能由用户反馈。experiment本体仍Build95，仅美术源与本轮课堂对接日志；已交付IPA为课堂端，不冒称experiment单机demo重打新包。后两步：按安装反馈复查人物一致性；教师常用课堂配置预设。缺独立体型只标注。

实现： https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/custom-appearance-v0.19.0.md
