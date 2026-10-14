# 安然 · 林间行旅 1.2 验收版

原生 Swift / UIKit / SpriteKit iOS 游戏 Demo，支持 iPhone / iPad、iOS 15 及以上，横屏、离线运行，无第三方运行依赖。安装名称为 `MeadowJourney`，便于 SideStore 重签。

## 动态场景

场景由 `SceneMap.json` 和独立资源搭建：地表纹理、两类阔叶树、松树、三类岩丘、营地、塔楼、栅栏、灌木、花草和独立蓝旗。120 个核心物件位置经过配置，额外花草按固定种子布置。旧整图背景已移出 App 的运行资源。

实时效果包括双层流动雾、光束、移动云影、统一太阳方向的物体轮廓投影、树冠与花草风动、飘动蓝旗和空气微粒。人物投影随当前步态变化，脚底与树根有独立接触阴影；投影高处逐渐柔化，树影保留叶隙。素材保留像素画的形体明暗；环境效果在运行时计算。人物和环境按脚底位置排序，UI 标签单独显示。

三位人物各有 1536 × 1536 动作图集，四个朝向，每个方向包含待机及三帧行走。步态按行走距离推进，正面和背面的左右脚交替接触，侧面交换近腿与远腿的明暗。缩放保持手指下的地图位置，iPad 通过上下扩展环境显示完整核心构图。

## 操作

- ▶ / Ⅱ：沿道路巡逻或暂停，继续时保留已经指定的目的地。
- 点选 P1 / P2 / P3，再点道路：沿连接的道路最短路径移动并停下。
- 点问号：选中旅人抵达探索点后解锁地点并产生微光。
- ↻：恢复初始人物位置、镜头与探索状态。
- ＋、双指缩放和拖动：调整镜头。
- 点“安然”查看说明；长按“安然”切换帧率、物件数、纹理预算与进程内存显示。

## iPad / SideStore 验收

[直接下载 1.2.0 IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/feat/layered-living-scene/Downloads/MeadowJourney-v1.2.0-unsigned.ipa)。在 Safari 保存到“文件”，再打开 SideStore → My Apps → ＋ → 选择带 `v1.2.0` 的文件重签。版本为 **1.2.0（build 5）**，安装后名称为 MeadowJourney。包标识与旧版相同，可以覆盖更新。

这批安装包和原生录像来自 [已成功的构建 38567622574](https://github.com/liamchan-rgb/experiment/actions/runs/38567622574)，源码为 `e9e7819`。改动保留在 [PR #3](https://github.com/liamchan-rgb/experiment/pull/3)，主分支当前仍交付 1.1.0。

最新 CI 产物也在 Actions 页：`MeadowJourney-unsigned-IPA` 是包含 IPA 的 Artifact ZIP；`ios-visual-review-*` 包含 iPhone / iPad 原尺寸截图、iPad 动态录像和 RuntimeMetrics.json；完整 Xcode 测试结果在 `ios-test-results-*`；`xcode-build-logs-*` 即使失败也上传。

运行指标中的纹理数值为基础 RGBA 解码预算，约 42.4 MiB；进程内存单独实测。CI 的帧率与内存来自 macOS 的 iPad 模拟器，真机指标可在你自己的 iPad 上长按“安然”查看。

## 构建

打开已提交的 `MeadowJourney.xcodeproj`，共享 Scheme 为 MeadowJourney，不需要 XcodeGen 或 CocoaPods。

```bash
xcodebuild build -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO
```

PR 新建、更新、重新打开、转为待审时自动在 macos-15 / Xcode 编译。工作流选择或创建兼容 iPhone 和 iPad，验证路线、目的地保留、方向资源绑定和两种设备的界面，记录 iPad 动态演示、四方向步态与静止镜头光雾，最后构建设备 Release archive 和未签名 IPA。`pipefail` 保留构建失败状态。

```bash
xcodebuild archive -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath build/MeadowJourney.xcarchive \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO
bash scripts/package-ipa.sh build/MeadowJourney.xcarchive build/MeadowJourney-unsigned.ipa
```

资源说明见 [docs/ASSETS.md](docs/ASSETS.md)。静态检查：`python3 scripts/validate-project.py`。修改项目绑定后可运行 `python3 scripts/generate-project.py`。

## 此次交付状态

1.2.0 已通过原生编译、18 项模型/资源/实际渲染检查，以及 iPhone 与 iPad 各 2 项交互测试。上次的 SpriteKit → Metal 纹理采样兼容问题已修复，实际渲染检查确认光雾像素变化、正背面不同的双腿接触姿势，以及随腿部姿势变化的投影。

[动态录像与原尺寸截图](Media/README.md)、[SideStore 安装说明](Downloads/README.md)与 [迭代进度记录](docs/ITERATION_STATUS.md)一起保存。录像整理任务处理已有验收资料，保留原尺寸；步态录像保留原始时间轴，长预览的时间比例另有记录。源码、构建与 IPA 的 SHA-256 见 `Media/BuildInfo-v1.2.0.json`。

已成功构建的录像附件可通过手动运行 `iOS Build and Visual Demo`，填写 `review_run` 为成功构建编号来整理，原始像素尺寸与来源记录保留；留空则执行完整 iOS 构建。
