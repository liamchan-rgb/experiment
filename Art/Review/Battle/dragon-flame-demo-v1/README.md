# 龙焰 V2 全场美术审核

完整正常速度预览：[`dragon-flame-normal.gif`](dragon-flame-normal.gif)。关键帧：[`dragonFlame-hover.png`](dragonFlame-hover.png)、[`dragonFlame-impact.png`](dragonFlame-impact.png)、[`dragonFlame-recovery.png`](dragonFlame-recovery.png)、[`dragonFlame-tail.png`](dragonFlame-tail.png)。

预览按生产战斗回执、角色姿势、实际投影骰面和两只怪物的节点目标记录合成，画面保留地图、战斗场景、状态条、行动顺序、骰子与技能卡。特效从伤害命中回执开始；存活目标呈现受击与火焰余波，血量归零的目标同时进入现有的粒子消散动画。火焰帧按固定中心锚点逐帧播放，并叠加红橙金余烬、地面接触火星、目标暖光和场景光照。

源战斗数据为 270 帧、60 Hz；GIF 以 50 帧/秒播放，整段时长仍为 4.5 秒。GIF 以 10 毫秒为时间单位，无法精确表达 1/60 秒。它是离线整场景美术审核图，不是 UIKit、模拟器或设备录屏。实机安装和运行由用户检查。

原始导出：[`dragon-flame-frames.json`](dragon-flame-frames.json)、[`dragon-flame-light-requests.json`](dragon-flame-light-requests.json)。本地复核命令：`python3 scripts/review-dragon-flame-demo.py --dragon-flame-only`。

自动检查：`python3 scripts/verify-dragon-flame-assets.py` 对比源表、20 张原始帧和 App 资源目录的像素；macOS 工作流运行龙焰规则测试及 60 Hz 战斗数据导出。IPA 与最终检查结果会记入 [`docs/dragon-flame-delivery.md`](../../../../docs/dragon-flame-delivery.md)。
