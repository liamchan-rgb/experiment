## build66 · 魔剑士三技能 · 1.6.40

[直接下载 MeadowJourney-b66.ipa](MeadowJourney-b66.ipa) · [正常GIF／站姿](../Art/Review/Battle/spellblade-demo-v1/README.md) · [包校验](MeadowJourney-build66.json)

小队演练P1默认魔剑士，“演练设置”可切回冒险者／重置；初始P2先行动，结束P2后轮到P1。营地衣装／装备／存档格式保持。符文斩2AP／2D12+2，对敌刻印斩裂并使自己恢复4／护盾至4；符文庇护2AP，所选地点存活队友恢复8／护盾至6；战斗符文1AP，该地点队友护盾至4／增伤+3两轮，三技各2次。增伤施放当轮不减时长，强盾不降级。

连续符文刻印、交错斩裂、青紫白命中光、弹跳碎片与地面照明；辅助符文按实际受益者独立展开／退场。8点治疗的绿色交叉双螺旋按sqrt(8/4)比4点加粗增亮。悬停骰子与强度压暗，确认只冻结一次回执，命中才提交；伤害绑定真实命中，辅助数字位于人物左下避开血条。怪物死亡同步隐血条／伤害数字与向右吹散。复用既有完整guard姿态曲线，不改任何人物／衣装／武器PNG、握点、Rig、步态或原规则。

本轮为独立职业演练，营地存档仍P1冒险者，选魔剑士不会改写档案，每场HP／补给重置；旧单人仍固定5伤＋装备增伤。未制作魔剑士新皮肤。帧率目标60，未测设备实际FPS。离线预览由原图集和生产字段合成，场景光影／UI近似，不是UIKit或设备录屏。安装与实机操作由用户测试。

源6371e680b640e83be57c50e0dd01814d82f98eed，Intel设备Release 40850367339成功，1.6.40/build66；162纯测试／五原检查／13组Mac/Linux导出在1e-6内一致，旧11组无回归。402原资源／规则／步态路径保持，708构建相关路径匹配源提交。66护甲资源、两饰品图标、三武器JSON、当前步态、原目录逐字节／资源名已核，版本／经典ZIP2.0／CRC／权限／arm64／Metal已核。IPA 49443349字节，SHA256 0390e647d1005820baccbfae264d6f0d757583c6c5638cd76f2b46b840de3255。

## build65 · P1行囊、装备与存档 · 1.6.39

[直接下载 MeadowJourney-b65.ipa](MeadowJourney-b65.ipa) · [正常GIF／界面](../Art/Review/Equipment/camp-inventory-v1/README.md) · [包校验](MeadowJourney-build65.json)

地图顶部“行囊装备”进入P1原生三栏界面：当前衣装／站姿与8帧正常步态、血条与黄色菱形AP、三装备槽；背包五类筛选／实际数量；详情原规则换装比较或P1/P2道具目标，主按钮固定底部。原.useItem／.rescue执行道具与AP，换装不补HP/AP。营地初建一次性补给，读档不重发。原人物／武器／护甲／动作像素及hero-gait、原规则目录不改。

Application Support/MeadowCamp/camp-v1.json保存三槽、两衣装、营地库存／资源／原操作档案。原子写入成功后原GameEngine才提交，写失败不改变装备／物品／衣装；重启在地图首帧前恢复并一次同步图集。JSON导入校验营地／目录／版本／外观并保留旧配置，导出可分享；坏档原文件保留，明确临时试装，点按保留旧档后才启用保存。

当前行囊仅P1，P2可作道具目标且地图外观保持。林地单人／小队仍独立演练，HP与补给每场重置，不扣营地库存；旧单人仍固定5伤＋装备增伤。存档不含道路位置或战斗中途续战，不冒称正式桌游全进度迁移。Build64无持久配置，不能恢复此前未保存的会话选择。

源90eb1f675d0cb9b1e5c8bcf2bc2421e74c7d912e，Intel设备Release 40843673369成功，1.6.39/build65；150纯测试／五原检查及11组Mac/Linux导出在1e-6内一致（含7营地投影／安全区布局）。新UIKit控制器／CampInventorySession已编入，原66护甲资源与两饰品图标、三武器JSON／当前步态／原目录、版本／经典ZIP2.0／CRC／权限／arm64／Metal已核。IPA 49391101字节，SHA256 5dd41203ba5264c5dfc138ddafa7412d3613dc658a5b8aa9e1cf218c941d561a。

## build64 · 两饰品接入 · 1.6.38

[直接下载 MeadowJourney-b64.ipa](MeadowJourney-b64.ipa) · [正常GIF／站姿](../Art/Review/Battle/accessories-demo-v1/README.md) · [包校验](MeadowJourney-build64.json)

营地→P1装备→饰品。力量徽章伤害＋2；行动戒指基础AP＋1（冒险者3→4），上限仍8；两件共用原单一accessory槽，换装不补HP/AP。共用单人／小队常驻小图标及悬停／点按详情，小队黄色加值与真实回执一致，行动菱形读实际属性且保留本轮容量。原人物／武器／动作／原规则目录不改，图标复用原B2素材。旧单人仍固定5伤＋永久装备增伤，非完整骰子规则迁移。仅P1营地借用，完整背包／存档待下项。

源221af86cf549dddd125b5c3c8dca7a230427074d，Intel设备Release 40838235939成功，1.6.38/build64；140纯测试／五旧检查及10组Mac/Linux导出一致，两新饰品图标与66护甲资源名编入，包内三武器JSON／当前步态／原目录逐字节匹配，版本／经典ZIP2.0／CRC／权限／arm64／Metal已核。IPA 49302869字节，SHA256 fee9d7d9ae5206aa3955fce1366d3476d7fc18700129cfa9cdf76ceed23caaec。

## build63 · 上臂衣片贴合／蓝布残角返修 · 1.6.37

[直接下载 MeadowJourney-b63.ipa](MeadowJourney-b63.ipa) · [正常全身动图／站姿](../Art/Review/Battle/armor-fit-r2/README.md) · [包校验](MeadowJourney-build63.json)

两张上臂衣片重新贴合原肩肘轴，修正皮甲错位与符文甲蓝布残角。132纯测试／五旧检查、Intel Release 40826021957、九组导出与包校验通过。48,938,928字节，SHA256 `1926d4db68de0748dd111ebf37b047631396785045d53eb19c297b4684717fec`。主线程返修／美术审核，实机由用户测试。

## build62 · 护甲手腕／袖口／下摆返修 · 1.6.36

[直接下载 MeadowJourney-b62.ipa](MeadowJourney-b62.ipa) · [正常动图／站姿](../Art/Review/Battle/armor-fit-r1/README.md) · [包校验](MeadowJourney-build62.json)

皮甲前臂和手腕补齐、符文甲袖口收窄、两甲独立下摆覆盖裤腿。132纯测试／五旧检查、Intel Release 40810525755、九组跨平台导出和包校验通过。48,940,192字节，SHA256 `cbce9fa2caeb669f4c427b054d5e0562192449d70beeeebacb7fa9a4f8a777ad`。主线程自行返修与美术审核，实机由用户测试。

## build61 · 皮甲／符文甲装备与战斗挂载 · 1.6.35

[直接下载 MeadowJourney-b61.ipa](MeadowJourney-b61.ipa) · [正常动图／站姿](../Art/Review/Battle/armor-demo-v1/README.md) · [包校验](MeadowJourney-build61.json)

营地P1→护甲切换皮甲／符文甲／原衣装。八向行走、四武器战斗挂载、原生命上限＋4／＋8；穿戴不回血、卸下截断。132纯测试／五旧检查、Intel Release 40742600629、九组导出和包校验通过。48,929,910字节，SHA256 `f63797f5ebb4abc9c213b4189f99121c427fa136087dca5970529656134300fe`。美术由主线程审核，安装与实机运行由用户测试。

## build60 · 权杖首帧与腿部遮挡修正 · 1.6.34

[直接下载 MeadowJourney-b60.ipa](MeadowJourney-b60.ipa) · [正常动图/首帧对照/站姿](../Art/Review/Battle/legendary-staff-layering-r1/README.md) · [包校验](MeadowJourney-build60.json)

修正待机杖杆被裤腿挡断、下端宝石悬空，以及起手/收势时层序和补底闪动。人物、握点、动作曲线和玩法保持。128纯测试/五旧检查、设备Release 40721530191、九组导出和包校验通过。38,263,628字节，SHA256 `c9719a152b96c9b64231542b16a6fb1c2b24305d6d2b0f8d35467299d57c938d`。主线程只做美术和包检查，实机交给用户。

## build59 · 传奇权杖施法与投射 · 1.6.33

[直接下载 MeadowJourney-b59.ipa](MeadowJourney-b59.ipa) · [正常整身/战斗/状态/站姿](../Art/Review/Battle/legendary-staff-demo-v1/README.md) · [八向背负](../Art/Review/P1/legendary-staff-demo-v1/README.md) · [包校验](MeadowJourney-build59.json)

营地 P1 武器菜单选择传奇权杖，进入林地战斗；小队先结束P2行动再操作P1。小队普攻原1D20、强击仍1D6+2、自然20原规则，蓝白弧线投射与落地碎光；两衣装八向背负及四武器切换。单人保留旧固定5伤练习。

38,262,895字节，SHA256 `a83dd2d3dd8c01a0a62c779902c18ac0eda9af4e33d07ee146afd46246fc9c9a`。128纯测试、五旧检查、Release 40714973471、九组Mac/Linux数据和资源/经典ZIP2.0/CRC校验通过。未运行App/模拟器/实机，由用户安装验收。

## build58 · 重剑动作与装备切换 · 1.6.32

[直接下载 MeadowJourney-b58.ipa](MeadowJourney-b58.ipa) · [正常整身/战斗/状态/站姿](../Art/Review/Battle/great-sword-demo-v1/README.md) · [八向背负](../Art/Review/P1/great-sword-demo-v1/README.md) · [包校验](MeadowJourney-build58.json)

营地P1武器菜单选择重剑，进入林地战斗；小队先结束P2行动再操作P1，可用原规则1D12普攻和原1D6+2强击。短跳贴近、握点挥击、接触停顿、回跳复位、宽剑不遮脸；两衣装完整八向背负及短剑/猎弓/重剑切换。旧单人仍固定5伤演练，本轮不虚称迁移正式规则。

36,838,157字节，SHA256 `d82ac2d6da8fa5ec8980c64532ee320919b154843d08f56c2b4a45eb5f2dabe3`。120纯测试、五旧检查、设备Release 40684811523、七组Mac/Linux数据及资源/经典ZIP2.0/CRC校验通过。未运行App/模拟器/实机，由用户安装验收。

## build57 · 猎弓完整状态动作 · 1.6.31

[直接下载 MeadowJourney-b57.ipa](MeadowJourney-b57.ipa) · [正常速度新动作/射击/战斗/站姿](../Art/Review/Battle/bow-actions-r7-demo-v1/README.md) · [包校验](MeadowJourney-build57.json)

新增防御、受击、胜利、跪地撑地和反向复起，保留认可版射击；单人与小队共用独立部件。营地武器选择猎弓后进入林地战斗；小队先结束P2行动，再操作P1。35,465,853字节，SHA256 `2351cc1a16b4fd801866d80a52d33e895d2548e17a8905bd35b1be6cbbce478b`。114纯测试、五旧检查、设备Release 40667152183、资源和经典ZIP2.0/CRC核验通过；无App/模拟器/实机运行，由用户安装验收。

## build56 · 认可版猎弓完整射击接入 · 1.6.30

[直接下载 MeadowJourney-b56.ipa](MeadowJourney-b56.ipa) · [包校验](MeadowJourney-build56.json) · [正常整身/整场动图与站姿](../Art/Review/Battle/reviewed-bow-r7-demo-v1/README.md)

P1 营地菜单→武器→猎弓；进入林地战斗，单人或“小队支援”查看抬弓搭箭、拉弦、放箭和收势。小队先结束 P2 行动再操作 P1。单人与小队共用用户已认可的 r7 原生独立部件，保留原规则和结算时刻；飞行箭长与人物尺度一致，影子随当前姿势。实机安装/运行由用户测试。

34,539,875 字节，SHA256 `5f41b1dcf96f3e855bc87595b66f901f2a1166ad7495fbec22c7591e21f58247`。设备 Release 40656603531、111 纯测试/五原检查、资源/经典 ZIP2.0/CRC/平台与权限核验通过；Mac/Linux 五组导出数据一致，包内新版动作 JSON 逐字节一致。未运行 App/模拟器/实机，不宣称设备 FPS 已测。

## 历史 build55 · 旧猎弓动作（用户已判退）

[MeadowJourney-b55.ipa](MeadowJourney-b55.ipa) · 1.6.29/build55，直接 IPA。P1 营地装备猎弓，在战斗及小队支援中查看持弓、拉弦、放箭与收手。保留项目原头部；近侧手拉弦，远侧手握弓。设备 Release 归档、包完整性和动作数据一致性已检查；实机安装与运行由用户测试。[包校验](MeadowJourney-build55.json) · [正常动图与审核](../Art/Review/Battle/hunting-bow-a-project-r1/README.md)。

## build54 猎弓持弓候选（用户指出动作问题，待返修）

用户已指出此版持弓手/拉弦手做反且有杂色像素，动作未获认可；先审阅新姿势草图。历史文件 [MeadowJourney-b54.ipa](MeadowJourney-b54.ipa) · 1.6.28/build54。P1 营地菜单选择猎弓，林地战斗 / 小队支援查看持弓、拉弦及放箭。设备 Release 归档与包检查通过；安装和实机画面由用户测试。[包校验](MeadowJourney-build54.json) · [正常动图与审核](../Art/Review/Battle/hunting-bow-grip-r1/README.md)。

## 历史交付：build53 猎弓

[MeadowJourney-b53.ipa](MeadowJourney-b53.ipa) · 1.6.27/build53，直接IPA。[校验记录](MeadowJourney-build53.json)。营地P1→武器→猎弓；林地战斗→小队支援查看真实1D8普通攻击（P2先行动）。旧单人保留简化固定5伤练习。设备归档/包校验通过，实机安装与运行由用户测试。美术正常GIF见Art/Review/Battle/hunting-bow-demo-v1与Art/Review/P1/hunting-bow-v1。

# SideStore 安装与迭代包

## 历史版本：训练短剑与连续停骰 · 1.6.26 build52

地图P1菜单可装备/卸下训练短剑，八向背负与战斗剑层/阴影同步；空手禁用普攻。骰子确认锁值后0.32秒连续减速转正，保留无字幕、黄色菱形与死亡隐条。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b52.ipa) · [包校验](MeadowJourney-build52.json) · [正常动图/站姿](../Art/Review/Battle/training-sword-smooth-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b52.ipa
```

32,901,808字节，SHA256 `5c1bf5b2c1053cbabc05c9c168797f8f08fdf99db5982ab333052b7147eb767c`。103纯测试、五旧检查、设备Release40281675931与包校验通过；安装/实机操作/FPS由用户测试。

## 历史版本：停骰摆正与战斗状态 · 1.6.25 build51

确认骰子正向停稳、移除下方重复数字；怪物死亡同刻隐藏血条；单人/小队行动点统一黄色菱形（亮起可用、暗空心已耗）。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b51.ipa) · [包校验](MeadowJourney-build51.json) · [正常动图/站姿](../Art/Review/Battle/upright-dice-hud-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b51.ipa
```

31,878,628字节，SHA256 `0121c60bd65e150dd4b02e913ad76a9fd82dbe1a75d24da9fa68e2ae4a0e9523`。98纯测试、五旧检查、设备Release40278764694与包结构/CRC通过；安装/实机操作/FPS由用户测试。

## 历史版本：确认停骰与击打点数字 · 1.6.24 build50

确认技能立即停稳本次骰值，命中才扣血/提交；固定方块去下方字幕，伤害数字从击打点出现。治疗强度与粗细/华丽层次标准已记录，原螺旋保持。

[直接IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b50.ipa) · [包校验](MeadowJourney-build50.json) · [正常动图/站姿](../Art/Review/Battle/confirm-impact-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b50.ipa
```

31,878,612字节，SHA256 `ee3e6dcd9c253a374ed117aa2aeabe294cfbe68dabbbf432c28a8f9041c05cc9`。97纯测试/五旧检查/设备Release40272222309及包结构/CRC通过，无App/模拟器/实机，安装/操作/FPS由用户测试。

## 历史版本：突袭与交叉螺旋回血 · 1.6.23 build49

突袭已接入游侠技能栏：按原规则2AP、每场2次，伤害2D8＋2、自身恢复3。演出为预备→快速突进/三道淡残影→双斩痕/受击局部爆光与落地光粒→回位；两道斩痕仅一次原核心结算，目标受击与施法者回血分开注册。最后敌人死亡时仍完成本人回血与回位，满血不额外触发回血光效。原身体/攻击姿势重定时复用，不声称重绘人物或已完成八件装备。

回血双螺旋绕身上升，固定值选中即显，骰子动画隐藏类型文字。入口林地战斗→小队支援→P2突袭。

[直接下载 MeadowJourney-b49.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b49.ipa) · [包校验](MeadowJourney-build49.json) · [四正常GIF/站姿](../Art/Review/Battle/ambush-helix-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b49.ipa
```

31,878,244字节，SHA256 `c4dae118ee027eb2c6e595ad34bede6bd734f84ddb65b05a09f844cdc2d1d65d`。94规则/适配/几何测试、五旧检查、设备Release40268729691与包CRC/资源校验通过，经典ZIP2.0封装。未运行App/模拟器/实机，真实安装、操作、稳定FPS由用户测试。

## 历史版本：多面骰真实翻面 · 1.6.22 build48

D4/D6/D8/D12/D20与兼容D10按各自面形三轴翻转，数字随面旋转/遮挡，回执到达后减速落面；实际公式决定骰型/颗数，固定加值单独标记。入口：林地战斗→小队支援。D4/D10离线图库不是新增默认武器，多骰图只审公式。

[直接下载 MeadowJourney-b48.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b48.ipa) · [包校验](MeadowJourney-build48.json) · [四正常GIF/站姿](../Art/Review/Battle/poly-dice-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b48.ipa
```

31,844,500字节，SHA256 `2f4bf3dbf66522c5dea71e55b93343f3734241d04c3148ce1d93ae2b3b7d155f`。90规则/几何测试、旧五检查、设备Release40264624021与包结构/CRC通过；经典ZIP2.0兼容封装。未运行App/模拟器/实机，实际安装/输入/FPS由用户测试。

## 历史版本：共享UI与头顶骰子 · 1.6.21 build47

多人战斗已恢复单人同款左右地图/战场、回合进度条、技能卡与生命/护盾/AP条；四单位进度token与当前行动者状态同步。预备人物光效改头顶持续摇动骰子，仍按技能固定强度压暗。红伤害、黄增伤、绿恢复、蓝护盾，援护绿蓝同时出现；确认后沿人物前冲跟随，命中回执到达后0.36s平滑停稳，保持可读后淡出。

[直接下载 MeadowJourney-b47.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b47.ipa) · [包校验](MeadowJourney-build47.json) · [五正常GIF/站姿](../Art/Review/Battle/dice-party-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b47.ipa
```

31,791,196字节，SHA256 `be893efe718c77d250d4b323b268fb5791dc00b730f68c44fc0b2e45daf6525e`。84规则/适配测试、旧五检查/设备Release40217822252与包完整性通过；经典ZIP2.0兼容封装。目标60，未运行App/模拟器/实机，真实安装/输入/FPS由用户反馈。

## 历史版本：小队支援 · 1.6.20 build46

本轮B0/B1小队支援已接入：援护、振奋、三种药水与复活石，2玩家/2敌目标、真实buff/AP/次数/库存与一次结算。入口为林地战斗→左上“小队支援”，原单人演练保留。正式盾max、buff轮数、救援2AP/半血/下轮行动由原GameCore执行。角色/步态与原资源10806路径保持，原13核心源文件/目录SHA匹配；两个P1与训练鹿灵复用不算新职业皮肤/正式怪完成。

[直接下载 MeadowJourney-b46.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b46.ipa) · [来源与校验](MeadowJourney-build46.json) · [五正常GIF/站姿](../Art/Review/Battle/party-support-demo-v1/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b46.ipa
```

31,740,108字节，SHA256 `3cd7c942e82d91a238ba9f11f4921c88f24a640734fbb38154f1e008f04e855d`。79规则测试/五既有检查/设备Release归档40212372613与包结构通过，经典ZIP2.0封装。目标60，未运行App/模拟器/实机，安装、操作与真实性能待用户反馈。

## 历史版本：统一60帧目标 · 1.6.19 build45

地图/步态/战斗显式60，移除静止地图动态光影/雾的30Hz门控；动态背景随每次提交样本刷新。移动/动作速度与美术保持。目标60不是实机测量结果；地图长按左上“安然”查看更新FPS，战斗诊断写Documents/BattleFrameTiming.json。

[直接下载 MeadowJourney-b45.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b45.ipa) · [来源与校验](MeadowJourney-build45.json) · [构建说明](../Media/Build45/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b45.ipa
```

30,293,018字节，SHA256 `67a5ad78757864506d53f7b8477ec80b90ea340ceaa7ebf0b08ff3bafe9a3d07`。归档40201819354/五项纯Swift/包完整性通过；经典ZIP2.0无压缩封装。未运行App/模拟器/实机，实际FPS与安装待用户测试；此前SideStore错误未确认根因。原美术预览见下方build44链接，不把离线GIF称为实机60fps录像。

## 历史安装兼容重封装：1.6.18 build44-r1

用户SideStore报“Archive appears to be corrupt”。原公开IPA重新下载与归档字节一致、CRC通过，未本地复现设备错误。现用经典ZIP2.0无压缩重新封装，所有App文件/权限逐字节保持，版本仍build44，不是美术改版；真实安装待用户确认。

[直接下载 MeadowJourney-b44-r1.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b44-r1.ipa) · [完整校验/说明](MeadowJourney-build44-r1.json)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b44-r1.ipa
```

30,292,842字节；SHA256 `945bdd2f930f4944a30e4e76a07d33d3e159944e26c6af7d61222f16ac103449`。重新下载这个新文件名再导入SideStore，勿复用旧文件。

## build44 原归档与美术预览

护盾施法渐入，回血光缕连续转向、星点稳定；目标更新60Hz，死亡粒子重新60Hz采样。减少逐帧光池/投影重算，记录真实帧间隔供后续实机判断。深绿金边与米白大粗字，HP/盾/AP条；护盾小方框hover/focus/tap看说明。原战斗数值/人物/行走/运镜保持。

[直接下载 MeadowJourney-b44.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b44.ipa) · [来源校验](MeadowJourney-build44.json) · [圆盾正常GIF](../Art/Review/Battle/smooth-status-demo-v1/shield-follow-normal.gif) · [回血正常GIF](../Art/Review/Battle/smooth-status-demo-v1/recovery-normal.gif) · [强击正常GIF](../Art/Review/Battle/smooth-status-demo-v1/strike-death-normal.gif)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b44.ipa
```

30,292,842字节，SHA256 `b2f1587658e56e6019c3b448310da16297a453ce1f4cb13bd648c02e5736791c`。归档40182000958/五项纯Swift/包完整性通过；无App/模拟器/实机执行，用户测试帧率与操作。正常50fps动图为生产轨迹/素材的离线光照及UI近似，非UIKit录屏，不能作为实机60fps测量。沿用SideStore重签。[交付回执](../Art/Review/Battle/smooth-status-demo-v1/delivery.json)。

## 历史版本：圆盾跟随、回血与技能动态 · 1.6.17 build43

大圆盾完整包住人物/持剑，直接挂人物同步移动；回血增加绿金盘旋、上升粒子、恢复短亮核和地面绿光；强击改扫动主弧/回声/光浪分阶段。依据用户视频的技能/光影参考，运镜和原数值/动作/行走保持。

[直接下载 MeadowJourney-b43.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b43.ipa) · [来源校验](MeadowJourney-build43.json) · [圆盾正常GIF](../Art/Review/Battle/skill-flow-demo-v1/shield-follow-normal.gif) · [回血正常GIF](../Art/Review/Battle/skill-flow-demo-v1/recovery-normal.gif) · [强击正常GIF](../Art/Review/Battle/skill-flow-demo-v1/strike-death-normal.gif) · [说明](../Media/Build43/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b43.ipa
```

28,133,914字节，SHA256 `40092768e150fd663d62181b95347be7d8ff95a2e6817b118e177cc98c33957f`。归档40179386404/五项纯Swift/包完整性通过；无App/模拟器/实机执行，用户复测。动图为同源素材/生产轨迹的离线照明近似，非设备录屏。沿用SideStore重签。[实际下载回执](../Art/Review/Battle/skill-flow-demo-v1/delivery.json)。

## 历史版本：发光粒子、地面碰撞与圆盾 · 1.6.16 build42

受击/怪物死亡增加发光粒子、局部环境暖光与落地反弹/溅光；圆盾颜色更鲜明、破裂蓝碎片更明显，鹿灵撞在盾前。数值、原强击与致死同事件右吹保持。

[直接下载 MeadowJourney-b42.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b42.ipa) · [来源校验](MeadowJourney-build42.json) · [正常受击/死亡GIF](../Art/Review/Battle/particles-round-shield-demo-v1/heavy-strike-normal.gif) · [正常圆盾GIF](../Art/Review/Battle/particles-round-shield-demo-v1/shield-normal.gif) · [说明](../Media/Build42/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b42.ipa
```

27,661,018字节，SHA256 `128f620175ec552817ec17779c52f8b8df6e2461066ab8e6dfd1a0934fd71de5`。设备归档40175880891/五项纯Swift/包完整性通过，无App/模拟器/实机执行；动图为共享素材/生产粒子轨迹的离线照明近似，用户测试实际画面/输入/帧率，沿用SideStore重签。[实际下载回执](../Art/Review/Battle/particles-round-shield-demo-v1/delivery.json)。

## 历史版本：强击冲击与护盾演出 · 1.6.15 build41

强击强化胸腹爆光、开放冲击弧/方向喷射/地面光浪，加深暗场、100ms停顿和世界轻震/短推近，HUD固定。护盾透明中心分展开/持续/格挡涟漪/耗尽碎裂；仍有盾值时保持。原数值、致死同帧右吹和出招无脚下环保持。

[直接下载 MeadowJourney-b41.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b41.ipa) · [来源校验](MeadowJourney-build41.json) · [强击正常GIF](../Art/Review/Battle/impact-shield-demo-v1/heavy-strike-normal.gif) · [护盾正常GIF](../Art/Review/Battle/impact-shield-demo-v1/shield-normal.gif) · [交付说明](../Media/Build41/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b41.ipa
```

26,986,898字节，SHA256 `c5361f015e4edaaa261992306ee3833d872a37ccc737f58b3c684a05f167e4cd`。设备归档40173101137与五项纯Swift检查/包完整性通过；无App/模拟器/实机运行。动图是同源素材/生产时钟的离线美术审核，用户复测实际画面与操作。安装沿用SideStore重签。实际GET核对见 [回执](../Art/Review/Battle/impact-shield-demo-v1/delivery.json)。

## 历史版本：战斗光效接入 · 1.6.14 build40

技能卡固定强度预示，强击发光同步压暗；接触时统一扣血/数字/HP0向右吹散，不等动作收尾，施放后光圈退出。强击仍为5伤害/1AP，键鼠焦点/悬浮与触屏按住预示已接线。

[直接下载 MeadowJourney-b40.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b40.ipa) · [来源与校验](MeadowJourney-build40.json) · [正常离线GIF](../Art/Review/Battle/effects-demo-v1/battle-demo-normal.gif) · [交付说明](../Media/Build40/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b40.ipa
```

25,176,986字节，SHA256 `2ed99a131c16c1030d22dc9a90070945009c04c6c2c76a9c56268d84a27267be`。进入“林地战斗 → 开始遭遇 → 选中鹿灵 → 强击”；三次后结束回合，下一轮第四次致死。最终设备归档40167117136及五项纯Swift检查通过，未运行模拟器/App/实机；实际光效、输入和性能由用户反馈。下载链接实取核对见 [回执](../Art/Review/Battle/effects-demo-v1/delivery.json)。

## 历史版本：新分层八向人物接入 · 1.6.13 build39

主地图点“P1 衣装”切换“林间绿衣”/“行旅蓝衣”，同一身体、显示与阴影同步，转向保留步相。起步/收步采用专用帧；停步会先在原地完成到指定出口的循环余段，再收脚。

[直接下载 MeadowJourney-b39.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b39.ipa) · [来源校验](MeadowJourney-build39.json) · [正常八向起停GIF](../Art/Review/P1/modular-demo-v1/demo-eight-way-start-stop-120ms.gif) · [交付记录](../Media/Build39/README.md)

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b39.ipa
```

23,616,706字节，SHA256 `9d68ac09c8e46c592a4a5fa9f1ddad837c57c06b430506fc34ada2449b5e112d`。Xcode16.4设备Release归档/四项纯Swift检查与包完整性通过，沿用SideStore重签安装；未运行模拟器或实机，实际显示/阴影/操作由用户反馈。已匿名GET直接IPA，HTTP200/application/octet-stream/23,616,706字节/SHA256一致；[回执](../Art/Review/P1/modular-demo-v1/delivery.json)。

## 历史版本：左上落脚过渡修订 · 1.6.12 build38

P1左上动画第02姿势增加左脚下降接地前的过渡，右脚继续支撑，再接第03姿势承重。120ms正常节奏保持，运行图集与足底数据同步；只修改左上02，保留原稿与历史修订。build37的可交互林地战斗仍包含在包中。

[直接下载 MeadowJourney-b38.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b38.ipa) · [构建校验](MeadowJourney-build38.json) · [美术与交付记录](../Media/Build38/README.md)

可直接复制到浏览器：

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b38.ipa
```

已实际匿名GET：HTTP200、application/octet-stream、24,201,944字节，SHA256 `d36b0a78bb48345fd829ce3967d139faeb3d604020c4250cdabca485ae5673fe`，与设备归档一致。下载即原始IPA，沿用SideStore重签安装。Xcode16.4设备Release归档39742884627、三项真实Swift检查和IPA完整性核对通过；完整人物、正常速循环及道路离线合成由主审检查。未运行模拟器／实机，实际运动和截图由用户复测。

## 历史版本：道路步态修复与可交互战斗 · 1.6.11 build37

P1道路步速对齐正常120ms姿势，移动投影同步脚底、停止清旧相位；四个斜向沿生产道路合成正常速动图复核。新增P1对鹿灵的完整局部遭遇，支持选靶、AP／生命／护盾、技能、敌方回合、胜负、重试；人物关节与鹿灵冲撞动作、命中／防护／回血反馈已接入。

[直接下载 MeadowJourney-b37.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b37.ipa) · [构建校验](MeadowJourney-build37.json) · [美术与交付记录](../Media/Build37/README.md)

可直接复制到浏览器：

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b37.ipa
```

已实际GET核对HTTP200、application/octet-stream、24,200,213字节，SHA256：`0bc40e083b12b0ee7f7ccd424cb2dc8c07a1c7381300697454c4c78d2e04ccfd`。下载即原始IPA，沿用SideStore重签安装。进入 **林地战斗 → 开始遭遇 → 点选鹿灵 → 点击下方技能**；行动点用尽后点结束回合。

Xcode16.4设备Release归档39735185139、三项真实Swift逻辑／姿势回归与IPA完整性核验通过；完整人物／正常速动图由主审检查。未运行模拟器或实机，设备帧率、触控和实际观感由用户安装后反馈；这是独立简化遭遇，未连接桌游背包／存档。

## 历史版本：斜向步态首尾修订 · 1.6.10 build36

四个斜向只替换08末帧，接顺07→08→01→02；右上修订保留同一支撑脚，另三个方向也检查完整人物过渡。站姿、01–07、四正交方向与P2／P3保持原稿，正常每姿势120ms；单靴足底坐标同步到前景／阴影数据。战斗维持已认可的v9静态呈现，下一张迈步关键帧美术单独审核。

[直接下载 MeadowJourney-b36.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b36.ipa) · [构建校验](MeadowJourney-build36.json) · [动图与修订记录](../Art/Integration/P1-diagonal-loop-v2/README.md) · [战斗下一张关键帧](../Art/Parts/P1-Battle/right-step-contact-v1/review.png)

可直接复制到Safari：

```text
https://raw.githubusercontent.com/liamchan-rgb/experiment/fix/build33-face-grounding-camera/Downloads/MeadowJourney-b36.ipa
```

已实际GET核对：HTTP200、application/octet-stream、23,592,463字节，文件SHA256与设备归档一致：`bd486f94ea64153e9fcf1ff593cf2b2495c48c1766862854ab6e818ac8738cec`。下载即原始IPA，无需解压。沿用SideStore重签安装，进入主地图的步态演示检查四斜向。设备Release归档39560271325通过，本轮未运行模拟器或物理设备，实机观感由用户截图验证。

## 历史版本：Meadow Journey 战场观感试验包 · 1.6.8 build 33

人物改为侧向持剑备战，独立叠放头发、五官、衣物和短剑；鹿灵改为四蹄落地的警戒站姿。调整双方像素尺度、逐脚接触影、轮廓投影与背景虚实；两种回合共用等比取景，修正怪物回合上下黑边。地图仍以原 Meadow Journey 为基准。

[直接下载 MeadowJourney-b33.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/meadow-battle-scene-v0.1/Downloads/MeadowJourney-b33.ipa) · [真实 iPad 截图](../Media/Build33/README.md) · [构建校验元数据](MeadowJourney-build33.json) · [制作日志](../docs/ITERATION_STATUS.md)

未签名，最低 iPadOS 15，arm64。Safari 下载并保存到“文件”，用 SideStore → My Apps → ＋ 重签安装；打开主地图 →“战斗预览”。IPA 23,079,780 字节，SHA-256 `b149816658ff8cf61f8a548f53320fbdea9b5d301d89c56b30099004f069d19d`。ZIP CRC、ZIP_STORED、无 Zip64／额外字段、版本号、设备平台、Metal 库与0755执行权限均已核验。

[最终 iPad 专项 39421546572](https://github.com/liamchan-rgb/experiment/actions/runs/39421546572) 通过4项原生与2项 UI 检查（0失败），实际三态截图已导出并自审；[设备归档 39422558233](https://github.com/liamchan-rgb/experiment/actions/runs/39422558233) 来自同一源码 `cd86161fd817eda49e3750570060e5b644abcb01`。当前仍是静态美术／布局实验，真实战斗规则和完整动作未接入；新增美术未记为用户认可，未在物理 iPad 上验证安装。

## 历史版本：Meadow Journey 战场布局试验包 · 1.6.7 build 32

左侧继续显示 experiment 的 Meadow Journey 地图；右侧战场改为同一套营地林地环境，人物取自地图图集，并配套一只暖棕／苔绿的林地鹿灵样例。整体保持 build31 已确认的地图／战场三态布局和混合回合轨道。

[直接下载 MeadowJourney-b32.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/meadow-battle-scene-v0.1/Downloads/MeadowJourney-b32.ipa) · [构建与校验元数据](MeadowJourney-build32.json) · [战场合成预览](../Art/Scenes/MeadowBattle/enemies/forest-warden-v1/review-composite.png) · [战场布局说明](../docs/MEADOW_BATTLE_LAYOUT.md)

IPA 为 23,798,348 字节，SHA-256：`b767b974b147a881c309626bc2bc3cdd8d59c4a4d107354d0e7b97a9014a88d3`。包标识 `com.liamchan.experiment.meadow`，版本 1.6.7（32），最低 iPadOS 15，arm64，支持 iPad。已检查 IPA CRC、ZIP_STORED、无 Zip64／额外字段、Metal 库和 0755 执行文件；IPA 未签名，用 SideStore 重签安装。Safari 下载后保存到“文件”，再打开 SideStore → My Apps → ＋，选择 IPA 重签安装。进入主地图 →“战斗预览”，切换探索、玩家回合和怪物回合查看三态。

最终专项工作流 [39300527243](https://github.com/liamchan-rgb/experiment/actions/runs/39300527243) 在 iPad Pro 13-inch（M4）模拟器、iOS 17.5／Xcode 15.4 上通过 4 项原生检查和 2 项 UI 检查（0 失败）。[设备归档 39301837295](https://github.com/liamchan-rgb/experiment/actions/runs/39301837295) 从源码 `c58dea84d773c219fd78432937be737b4537d69b` 构建，含该提交中的林地鹿灵资源。Xcode 15.4 不支持独立导出 `.xcresult` 附件，原始测试结果仍保存在工作流工件；另提供[离线战场合成预览](../Art/Scenes/MeadowBattle/enemies/forest-warden-v1/review-composite.png)，该图不是模拟器截图。完整来源与校验记录见[build32 元数据](MeadowJourney-build32.json)。

此包是战场美术／布局试验，不连接桌游真实战斗状态、技能结算或存档。右侧鹿灵为单帧、尚未获用户审美审核的样例，仍没有敌方动画；未在物理 iPad 上实测安装。

## 历史版本：Meadow Journey 桌游布局试验包 · 1.6.6 build 31

按桌游已确认记录安排共用顶部、中间等高地图与战场、整屏连续混合回合轨道及紧凑技能／物品详情。顶部可切换探索、玩家回合、怪物回合；探索展开地图，怪物回合收起详情并增高地图与战场。素材、色调和环境效果继续以 Meadow Journey 为基准。

[直接下载 MeadowJourney-b31.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/meadow-battle-scene-v0.1/Downloads/MeadowJourney-b31.ipa) · [玩家回合实际截图](../Media/MeadowBattle-b31/player-turn.png) · [全部三态截图](../Media/MeadowBattle-b31/README.md)

IPA 为 17,242,444 字节，SHA-256：`e2c84b63e53e8141cddcb159a88f3cb4d56eb6297675a75658f3465ff9f3ddab`。已检查包内版本、真机 arm64、iPad 支持、Metal 库、0755 可执行权限、ZIP CRC 和 ZIP_STORED。[构建与完整性元数据](MeadowJourney-build31.json)。

用 SideStore 重签安装，进入主地图 →“战斗预览”，顶部切换三种布局状态；“返回地图”退出并恢复原来的镜头和缩放。3 项原生布局／相机检查与 2 项 iPad UI 检查通过，含三态切换、十单位轨道、公开资源无AP、地图边缘纹理及相机恢复；三张原始截图已逐一目视核对。

这是布局演示：轨道7玩家＋3敌方、技能和空背包为只读样例，尚未接真实桌游回合、技能结算或存档；右侧人物仍是单帧候选，敌方仍为占位。完整步态套件未重跑，历史失败记录见[迭代日志](../docs/ITERATION_STATUS.md)；物理 iPad 和电视尚未测试。

旧原型保留：[build 30 左栏适配修复](MeadowJourney-build30.json) · [build 29 初始战场](MeadowJourney-build29.json)。

上次完整通过 iPad UI 套件的正式基线仍是 build 28：

**1.6.3 build 28**：修正三位人物在八个行走方向中两只鞋分别向外撇的问题，使鞋尖更一致地朝向前进方向。“原图 / 分层蓝靴对照”仍是附带的换色小样，仅覆盖 P1 向下方向。

[直接下载 MeadowJourney-b28.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b28.ipa)

IPA：16,806,354 字节，SHA-256：`e99c0e9754dd3ea4875566603df82273b49365474b8069a7e0693e25fad0cd0f`。已检查 ZIP CRC、ZIP_STORED、无 Zip64／额外字段、真机 arm64、0755 执行权限、Metal 库，以及包内蓝靴图集和对照入口代码。安装包未签名，使用 SideStore 重签；安装名称 MeadowJourney，包标识 com.liamchan.experiment.meadow，最低 iPadOS 15。沿用原 SideStore 账号和安装方式更新即可，不需要先删除旧版。

Safari 下载后保存到“文件”，再打开 SideStore → My Apps → ＋，选择该 IPA 重签安装。

安装后进入主地图 →“步态测试”，依次选择八个方向，检查 P1、P2、P3 的鞋尖是否一同朝向前进方向、交替时有没有反转或鞋腿断缝。可切换四分之一速度、暂停和单步定位问题。完整步骤见[鞋向实机测试说明](../docs/GAIT_TEST.md)。

[正常速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Normal-b26.mp4) · [四分之一速度录像](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Media/iPad-Gait-Quarter-b26.mp4) · [鞋部方向连续抽帧](../Media/Build26-Gait/README.md) · [可换装骨骼方案评估](../docs/CHARACTER_RIG_EVALUATION.md) · [迭代日志](../docs/ITERATION_STATUS.md)。

[本次构建 39051625894](https://github.com/liamchan-rgb/experiment/actions/runs/39051625894) 的设备 Release IPA、八方向 iPad UI 检查和实际地图录像均已通过：模拟器逐个切换八个朝向，并逐帧检查每方向 24 张步态姿势；另保存了正常／四分之一速度地图录像。测试设备为 iPad Pro 13-inch（M4）模拟器、iOS 18.5；物理 iPad 的安装与运行观感仍需本地确认。

[来源与完整性元数据](MeadowJourney-build28.json) · [IPA SHA-256 列表](SHA256SUMS)。

历史版本：[build 27](MeadowJourney-build27.json) · [build 26](MeadowJourney-build26.json) · [build 25](MeadowJourney-build25.json) · [build 24](MeadowJourney-build24.json) · [build 23](MeadowJourney-build23.json) · [build 22](MeadowJourney-build22.json)。
