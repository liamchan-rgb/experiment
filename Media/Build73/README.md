# Build73 · 可控随机地图与林地预览

[直接IPA](../../Downloads/MeadowJourney-b73.ipa) · [正常速度行走GIF](../../Art/Review/Map/random-map-v1/walk-normal.gif) · [4/10/30节点全图](../../Art/Review/Map/random-map-v1/comparison.png) · [实现与限制](../../docs/planning/random-map-v1/implementation.md)

1.6.46/build73。原地图左下“随机地图”进入；可设4—30总节点，起点固定1，普通战斗、Boss、奖励和空地点分别精确配置，Boss允许0。各类总和不符显示差额并禁用生成。可设额外道路/种子，主动采用建议才重分配数量；后台生成缩略道路，再进入与原地图共用渲染流程的林地预览。返回设置保留本次结果，主地图和营地档案不被预览改写。

已完成M1生成器/M2设置及林地预览，角色可按原动作沿真实道路走。当前节点仅为地点类型预览，战斗/奖励不结算；没有正式探索会话、完整行程存档或节点后台编辑。后两项为M3共享正式探索引擎/遇敌/奖励与地图存档，再M4单节点怪物与奖励编辑。

179项Swift测试在Linux和Mac通过；648组数量/种子检查，78组实际SceneDefinition/道路平滑/巡逻/道路交叉/占地检查，9组导出；独立临时构建重导数据逐字节一致。13个原规则/目录源文件不变。主线程查看三张整场1×与16关键帧、10页最终GIF解码接触表400帧（240×135），未声称每帧全分辨率/连续播放。预览用生产布局与原PNG离线合成，道路材质/光影/UI近似，不是Metal/设备录屏。

Intel设备Release工作流41776982266成功，源7c558bed56b8057300433d1222e9aeaaca04fa9f。包内版本、CRC、经典ZIP2.0、arm64、执行权限、地图UI/生成器链接、Assets.car/Metal、原SceneMap/hero-gait与规则目录均核对；详见verification.json。IPA 59177013字节，SHA256 3a49e18944e09494a5a424ba9965c4d99b68e317097c265519a3eb0a71d1d546。未运行App/模拟器/实机，安装与实机画面由用户验证，认可null。

公开IPA/动图/全图完整GET均为200，大小与SHA256匹配本地；动图400帧×20ms、循环已核。[公开下载回执](public-downloads.json)。直接下载为IPA，不提供外层ZIP。
