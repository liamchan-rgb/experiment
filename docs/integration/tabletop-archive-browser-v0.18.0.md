# 行程/历史筛选与美术对接

## 行程/历史筛选与美术对接 · 课堂v0.18.0/build23（2026-11-07）

用户继续下一项并要求说明以后experiment的人物骨骼/配饰/技能特效/UI等如何接入课堂。课堂行程页支持标题/成员/队伍/种子搜索、探索/战斗/结算状态、1—7人数叠加、保存时间或原槽号稳定排序；原槽号不随列表重排。空槽和损坏提示单独保留，坏档不被筛选隐藏。历史支持战斗/移动/资源/组队/外观/配置分类，涉及人物/怪物、关键字/旧新姓名/原序号、升降序；后台索引、50条递增加载，查询不写档/推进RNG。回退继续使用原ID，保留所选条目、撤回其后全部原操作，包括筛选/分页隐藏项，确认显示原序号和总数，先备份再恢复并暂停。

完整美术协议已镜像在两仓库AGENTS入口：本仓库docs/integration/classroom-art-sync.md及模板classroom-art-update-template.json；课堂仓库docs/integration/experiment-art-sync.md及experiment-art-update-template.json。固定完整源SHA，成套盘点PNG/图集/骨骼锚点/配饰遮挡/姿态代码/技能时序/光照粒子/公开UI，按实际路径选择性合并；保留课堂教师私有权限、6学生+P7、绘本、固定画布/镜像、存档/规则，不整仓或旧Vendor覆盖。逐文件源提交与SHA、兼容标识、正常GIF、实际编译IPA和可恢复归档都要记录，不把混合来源冒记为一个新SHA。不自动热更新。

课堂tools/plan_experiment_art_update.py仅生成提交间增改删/目标映射/源旧新与课堂当前哈希/适配差异报告，不做apply。真实初始盘点固定experiment 331ccbc3a9dec4e275774396dee30999f407d9df，相对175c7dfc的37项差异全部为Media/Build95离线交付证据，无运行时资源/呈现代码变化。本轮没有导入新美术，也没有推进568源资源基线；experiment本体仍Build95。源协议在331ccbc独立提交，当前记录只同步课堂交付结果。

新增14Swift+4Python盘点专项，本地及实际CI完成403规则/后台+6绘本核心零失败，另8本地Python工具检查。设备Release实际编译`7b27d32e01582a96f4611538d9db5561663388f9`、run42396956759 attempt1，版本0.18.0/build23，最低iPadOS27.0、SDKiphoneos27.2；CRC/经典ZIP2.0/arm64/755/Metal/568源资源SHA/281编译名称/3挂载JSON通过，可执行文件不同build22。未运行App/模拟器/实机；实际iPad输入/长列表/电视隐私/性能由用户复核。8秒100帧正常GIF为离线筛选/协议结构示意，主线程四阶段接触表和逐帧解码已查，不是App/UIKit截图或性能/触摸回放。

源码快照`70e286f08f768bc7d40fd3fe9525de6b66c931d4`与实际编译提交分开，标签`archive-browser-meadow-v0.18.0-20261107`。源码/协议/工具/Git bundle/IPA/诊断/GIF永久保存在archive-assets，ZIP逐文件/独立bundle恢复与fsck/全部公开文件GET通过，归档run42397858759；main只放索引。直接IPA完整GET200，62916115字节，SHA256`79f4fc233667f31c85e681fe017094938282b8eac03d3dd703fb81e19c6d797a`。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/ec0c544576c2b55da4b91f00b23b7edf668fa4e7/archive-browser-meadow-v0.18.0-20261107/ClassroomStage2-v0.18.0-unsigned.ipa) · [正常速度筛选/对接示意GIF](https://raw.githubusercontent.com/liamchan-rgb/classroom-boardgame/ec0c544576c2b55da4b91f00b23b7edf668fa4e7/archive-browser-meadow-v0.18.0-20261107/archive-browser-normal.gif) · [可恢复存档/校验](https://github.com/liamchan-rgb/classroom-boardgame/blob/main/archives/archive-browser-meadow-v0.18.0-20261107.json)

后两步：教师常用课堂配置预设；有真实experiment交付后，按本协议接入首批美术更新。缺失美术只登记，不擅自补画，不自动读取或上传教师设备真实存档。

本轮本地GH_TOKEN过期，GitHub连接接口仍有效；已通过连接接口与仅本轮使用的publish-verified-build23工作流完成永久归档，收尾删除该临时工作流，无重复发布任务。命令行写权限未恢复，不输出凭据；后续写入可继续使用已连接接口。


实现说明：https://github.com/liamchan-rgb/classroom-boardgame/blob/feat/teacher-backend-meadow-v0.13/docs/integration/archive-browser-v0.18.0.md
