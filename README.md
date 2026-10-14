# 安然 · 林间行旅

参考提供的金绿色林间地图制作的原生 iOS 游戏 Demo。Swift + UIKit + SpriteKit，无第三方运行依赖，支持 iPhone / iPad、iOS 15 及以上，横屏运行。所有源码、参考图、生成的原始素材、打包资产和 CI 配置都保存在本仓库。

## 操作

- **▶ / Ⅱ**：三位旅人沿土路往返，或暂停。
- **点选人物，然后点土路**：让选中的人物沿道路移动到点击的位置并停下。人物显示 P1、P2、P3 标记。
- **↻**：恢复样例中的人物位置、暂停状态和缩放。
- **＋**：循环放大；也可双指缩放、双指拖动。
- **问号**：触发林间微光。左上角“安然”可查看操作说明。

初始构图保留蓝旗营地、两座塔楼、土路、岩丘、花草和暖色光照。背景与人物分离，行走使用透明帧动画，路线由地图中的土路折线定义。宽屏会等比例填满屏幕，按钮适配安全区。

## Xcode 工程

打开 `MeadowJourney.xcodeproj`，选择共享 Scheme **MeadowJourney**。工程已提交，可直接构建，不需要 XcodeGen、CocoaPods 或网络下载依赖。

```bash
xcodebuild build \
  -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO
```

目录：`Sources/` 包含 App、游戏与 UI；`Tests/` 验证路线投影、恒速移动、端点反弹和指定位置停止；`UITests/` 验证播放、暂停、缩放、复位，并保存界面截图。`Art/` 保留原图和生成素材，资产说明见 [docs/ASSETS.md](docs/ASSETS.md)。

## GitHub Actions

[iOS Build and Visual Demo](.github/workflows/ios.yml) 在每次 PR 新建、更新、重新打开、转为待审时运行，也支持 main 分支推送和手动触发。使用 **macos-15** 和 Runner 默认的 Xcode，并记录具体版本。

1. 检查实际 `.xcodeproj` 与共享 Scheme，编译 Swift 模拟器版本。
2. 根据所选 Xcode 的 SDK 选择兼容的已安装 iOS Runtime，选择或创建 iPhone 模拟器；缺少 Runtime 时下载对应平台，再执行路线单元测试和 UI 测试。
3. 构建设备 Release archive，打包未签名 IPA。
4. 上传 `xcode-build-logs-*`、`ios-visual-review-*`、`MeadowJourney-unsigned-IPA` 三类 Artifact。即使构建失败，已有编译日志与测试结果仍上传；`pipefail` 保证 `tee` 不会掩盖失败。

## SideStore 视觉验收

在成功的 Actions 运行页面底部下载 **MeadowJourney-unsigned-IPA**，解压 Artifact ZIP 得到 `MeadowJourney-unsigned.ipa`。在已配置好的 SideStore 中导入这个 IPA，由 SideStore 使用你的 Apple ID 重签后安装。应用离线运行，没有 App 扩展或特殊签名权限。

这是**未签名的真机 arm64 IPA**，不能直接点开安装，也不是模拟器包；不需要在此仓库存放 Apple 证书。截图位于 `ios-visual-review-*` 中，原始测试报告可在 Xcode 打开 `.xcresult`。

本地打包：

```bash
xcodebuild archive \
  -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Release -destination 'generic/platform=iOS' \
  -archivePath build/MeadowJourney.xcarchive \
  CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO
bash scripts/package-ipa.sh build/MeadowJourney.xcarchive build/MeadowJourney-unsigned.ipa
```

静态检查：`python3 scripts/validate-project.py`。若维护工程文件，可用 `python3 scripts/generate-project.py` 重生成同一组确定性 target ID 和共享 Scheme。
