# 安然 · 林间行旅 1.1

原生 Swift / UIKit / SpriteKit iOS 游戏 Demo，支持 iPhone / iPad、iOS 15 及以上，横屏、离线运行，无第三方运行依赖。安装名称为 `MeadowJourney`，便于 SideStore 重签。

## 动态场景

场景由 `SceneMap.json` 和独立资源搭建：地表纹理、两类阔叶树、松树、三类岩丘、营地、塔楼、栅栏、灌木、花草和独立蓝旗。141 个物件位置经过配置，额外花草按固定种子布置。旧整图背景已移出 App 的运行资源。

实时效果包括双层流动雾、光束、移动云影、缓慢变化的物件投影、树冠与花草风动、飘动蓝旗和空气微粒。素材保留像素画的形体明暗；环境效果在运行时计算。人物和环境按脚底位置排序，UI 标签单独显示。

三位人物各有 1536 × 1536 动作图集，四个朝向，每个方向包含待机及三帧行走。缩放保持手指下的地图位置，iPad 通过上下扩展环境显示完整核心构图。

## 操作

- ▶ / Ⅱ：沿道路巡逻或暂停，继续时保留已经指定的目的地。
- 点选 P1 / P2 / P3，再点道路：沿连接的道路最短路径移动并停下。
- 点问号：选中旅人抵达探索点后解锁地点并产生微光。
- ↻：恢复初始人物位置、镜头与探索状态。
- ＋、双指缩放和拖动：调整镜头。
- 点“安然”查看说明；长按“安然”切换帧率、物件数、纹理预算与进程内存显示。

## iPad / SideStore 验收

[直接下载 1.1.0 IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/main/Downloads/MeadowJourney-v1.1.0-unsigned.ipa)。在 Safari 保存到“文件”，再打开 SideStore → My Apps → ＋ → 选择带 `v1.1.0` 的新文件重签。版本为 **1.1.0（build 3）**，安装后名称应为 MeadowJourney。

最新 CI 产物也在 Actions 页：`MeadowJourney-unsigned-IPA` 是包含 IPA 的 Artifact ZIP；`ios-visual-review-*` 包含 iPhone / iPad 原尺寸截图、iPad 动态录像、RuntimeMetrics.json 和 Xcode 测试结果；`xcode-build-logs-*` 即使失败也上传。

运行指标中的纹理数值为基础 RGBA 解码预算，约 42.4 MiB；进程内存单独实测。CI 的帧率与内存来自 macOS 的 iPad 模拟器，真机指标可在你自己的 iPad 上长按“安然”查看。

## 构建

打开已提交的 `MeadowJourney.xcodeproj`，共享 Scheme 为 MeadowJourney，不需要 XcodeGen 或 CocoaPods。

```bash
xcodebuild build -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO
```

PR 新建、更新、重新打开、转为待审时自动在 macos-15 / Xcode 编译。工作流选择或创建兼容 iPhone 和 iPad，验证路线、目的地保留、方向资源绑定和两种设备的界面，记录 18 秒 iPad 动态演示，最后构建设备 Release archive 和未签名 IPA。`pipefail` 保留构建失败状态。

```bash
xcodebuild archive -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath build/MeadowJourney.xcarchive \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO
bash scripts/package-ipa.sh build/MeadowJourney.xcarchive build/MeadowJourney-unsigned.ipa
```

资源说明见 [docs/ASSETS.md](docs/ASSETS.md)。静态检查：`python3 scripts/validate-project.py`。修改项目绑定后可运行 `python3 scripts/generate-project.py`。
