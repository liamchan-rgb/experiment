# Build75 · 不规则路网与建筑节点

[直接IPA](../../Downloads/MeadowJourney-b75.ipa) · [正常行走GIF](../../Art/Review/Map/random-map-v3/walk-normal.gif) · [10节点整图](../../Art/Review/Map/random-map-v3/map-10-overview.png) · [三规模/三种子](../../Art/Review/Map/random-map-v3/sizes-seeds.png) · [实现记录](../../docs/planning/random-map-v1/build75-organic-landmarks.md)

1.6.48/build75。修复Build74方格形制与建筑分离：不规则散点经物理排斥/Delaunay候选连接成真实道路，保留精确类型/环路配额；路径绕建筑、弯角圆滑，非邻接道路无假交叉。建筑x与道路节点一致，脚底在北侧26单位，道路到达点就是门前；点建筑/上方徽记走同一落点。徽记位于实际PNG轮廓上方14单位，缩略图正确显示营帐等资产真实比例，不再用旁边草地的独立圆点代表建筑。原地图左下“随机地图”进入，数量联动/整数滑块保留。人物/装备/动作/建筑原PNG与上游规则未重制。

182项Swift包测试在Linux/Mac通过；648规模/种子、24单类配额/最大环路、36方向退化案例、78生产适配/巡逻/门前对齐/建筑清障/无假交叉检查；九个导出布局132个徽记与真实PNG顶边逐一数值吻合。13上游源文件摘要保持。设备Release归档成功，包版本/CRC/经典ZIP2.0/无extra/arm64/执行权限/四建筑编入Assets.car/Metal/原SceneMap与hero-gait及规则目录均核，详见verification.json。

主线程独自检查三规模完整图、九布局对照、关键全帧及正常GIF实际解码400帧的10页接触表（240×135）；不称400帧逐像素全分辨率验收。GIF400×20ms/8秒由生产布局/道路/徽记/步态与实际PNG离线合成，光照/阴影/道路材质/UI近似，不是UIKit/Metal/设备截图，不测实机帧率。无App/模拟器/实机执行，安装操作交用户，新美术认可null。

源提交与已交付归档匹配，以verification.json记录的最终运行41811725340为准。旧回归脚本的道路DTO已同步sampled字段，并检查新道路不重复平滑/旧道路保留原行为。

仍是林地预览，正式探索战斗/奖励/战役存档未接入，不改原营地档。后两项：M3正式探索/结算与地图存档；M4单节点内容编辑。
