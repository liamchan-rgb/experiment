# Build56 · 认可版猎弓接入后审核

[正常整身动图](body-normal.gif) · [普通攻击整场动图](bow-normal.gif) · [击杀整场动图](bow-lethal-normal.gif) · [待机整身](body-standing.png)

主线程检查实际导出的三只正常GIF全部570帧/30页联系图，六种动作30个整身姿态的1×/2×图及整场关键画面。搭箭后手指/箭尾/弦心相接，近侧手拉弦/远侧手持弓；肩肘袖身不退回旧资源，射后接回待机。先修复中间稿准备动作挤在旧0.4秒停留后过急的问题，现从确认技能起准备，0.86秒出手和原命中/停顿不变。飞行箭保持原生73像素×人物尺度。

全部143个导入原生合成与用户认可源逐像素一致，235个独立部件小图去重装图集；没有导入整人动画帧。生产Swift导出3606姿势/原核心规则回执，使用与App相同原生部件和挂点。审核记录见 art-audit.json；每只GIF 190个20ms采样帧/3.8秒含停留，单次播放，重开链接可重播。

这是离线美术合成，字体/混合/地图/光影/UI近似；不是UIKit、App或实机录屏，不证明设备60FPS。原素材已获认可，运行时接入的用户认可仍为空；iOS设备Release归档和IPA包校验另见 Media/Build56。实机安装/操作由用户测试，无模拟器或设备运行。

复现：Swift运行 MeadowSupportReviewExport 到本目录，运行本审核脚本 --prepare；由 MeadowBattleEncounter.swift 与 export-smooth-status-review.swift 编译光场导出器，将 dice-light-requests.json 转成 dice-light-samples.json，再运行 scripts/review-reviewed-bow-r7-demo.py。原生导入脚本为 scripts/import-reviewed-bow-r7.py。
