# 猎弓 A：近侧拉弦、远侧持弓

用户选择 A 作为姿势依据；成品动作待复审。root 独立制作与审核，未委派智能体。

- 近侧手拉弦、肘向后，远侧手持弓，前后袖面用明暗区分。
- 弓专用连续袖形/袖口/手形，骨骼角度过渡保持上臂与前臂长度；不再旋转原持剑袖子留下接痕。
- 补齐旧袖下缺失的衣料，保留原头脸/头发、领口和腰带像素；旧肩部孤点通过显示裁切移除；原资源PNG均未改写。
- 箭尾/弓弦汇到近侧手；放弦回弹与手向后跟随分开，原1.048秒命中和D8规则保持。

`bow-body-normal.gif`：整身；`bow-normal.gif`：整场。各190帧×20ms=3.8秒，离线50fps美术合成，不是运行App或设备60fps实测。root检查实际解码联系页、30个六动作整身姿势及场景样本；通过107纯测试、五项原独立检查与项目绑定检查。UIKit适配仅语法检查，本轮没有完整Xcode编译、新IPA或设备/模拟器/App运行。旧私人v7审核页仍是旧候选，不作为本轮入口。

`pixel-components.json` 是辅助扫描，不能替代审美判断。726姿势中，待机和射击没有小孤点；64个受击/倒地采样仍有原腿部旋转形成的单像素（y≥184），已记录，不声称所有动作无残留。

复现（Swift工具链就绪）：

```sh
swift run --package-path Vendor/ClassroomGameCore MeadowSupportReviewExport Art/Review/Battle/hunting-bow-pose-a-r1
python3 scripts/review-hunting-bow-pose-a-r1.py --prepare
# 生产光效导出器：由Sources/Game/MeadowBattleEncounter.swift和scripts/export-smooth-status-review.swift编译
# field-export <目录>/dice-light-requests.json <目录>/dice-light-samples.json
python3 scripts/review-hunting-bow-pose-a-r1.py --only bow
python3 scripts/review-hunting-bow-pose-a-details-r1.py
python3 scripts/verify-hunting-bow-pose-a-r1.py
python3 scripts/review-hunting-bow-pose-a-stills-r1.py
```

仅重导动作几何可在导出器末尾加 `--bow-only`，先前整场回执样本仍须存在；命中/起点改变则须全导。
