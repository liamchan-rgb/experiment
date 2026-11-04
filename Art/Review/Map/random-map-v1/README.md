# 可控随机林地 v1 · Build73

[正常速度行走动图](walk-normal.gif) · [4/10/30节点对照](comparison.png) · [10节点全图](map-10-overview.png) · [30节点全图](map-30-overview.png)

这轮完成M1生成器与M2设置/林地预览：原地图左下“随机地图”进入设置，总数4—30，起点固定1，战斗/Boss/奖励/空地点配额分别输入；总和错误时不能生成。可改额外道路数量和种子，点击采用建议才覆盖手动数量；生成后查看缩略道路，再进入原生林地预览，返回设置保留当前结果。预览能沿道路行走、点击地点；战斗/奖励不结算，画面明确标识，原营地存档不被该预览改写。

生成器是独立Foundation/MeadowWorldSupport模块，沿邻接网格候选边随机取连通树及环路，节点位置抖动、道路弧线与布景随独立种子流变化。保留现有草地、树石、营地、行走和投影资源。地图逻辑与视觉道路共用端点，生成巡逻路线沿真实道路出入各分叉；固定出生和discoveries[1]不再用于生成图。此版不包含正式探索会话、怪物投放/奖励结算、战役存档或单节点后台编辑。

离线图来自实际Swift生成的地图、SceneDefinition适配、Trail.smooth曲线、JourneySimulation与AuthoredLocomotion采样，以及未修改的项目PNG。阴影、道路材质、环境光和UI由Pillow近似，因此不是UIKit、Metal或设备截图，不证明运行帧率。动图400帧×20ms=8秒，角色原画帧仍按已有步态推进，不是重制400张角色。主线程查看三张整场1×静帧、16关键采样和最终GIF实际解码的10页接触表（400帧，每格240×135）；未声称每帧全分辨率或连续播放器验收。首轮道路过于规整、营地出界/被树挡住、三人初始间距过近均已返修；保留旧候选源码提交，不发布旧IPA。

验证：179项Swift包测试；4—30各24种子共648图的配额/图有效性/循环数/可复现检查；78组正式平滑/适配/巡逻/道路交叉/占地检查，其中9组导出；独立临时构建重新导出的数据逐字节一致。见checks.json、tests.log、reproduce.log。设备Release编译/包校验和安装状态以Media/Build73的回执为准，美术认可仍为null。

重新导出：

```bash
swift test --package-path Vendor/ClassroomGameCore
bash scripts/check-random-map.sh Art/Review/Map/random-map-v1/data
python3 scripts/review-random-map.py
```

Python预览需Pillow与中文字体；可用MEADOW_REVIEW_FONT指定字体。主线人物/衣物/技能PNG与ClassroomGameCore原规则文件保持。本轮只做生成/预览，不以新地图预览冒充已接正式探索。

后两项：M3正式探索会话、遇敌/奖励与实际地图存档；M4单节点怪物/奖励编辑及明确的事件重置。
