# 安然 · 林间行旅

[最新 1.6.1 build 26：鞋部朝向修正 IPA](Downloads/README.md) · [正常／慢速录像与抽帧](Media/Build26-Gait/README.md) · [可换装骨骼方案评估](docs/CHARACTER_RIG_EVALUATION.md) · [迭代日志](docs/ITERATION_STATUS.md)

以下为 build 9 的历史版本说明。

原生 Swift / UIKit / SpriteKit iOS 游戏 Demo，支持 iPhone / iPad、iOS 15 及以上，横屏、离线运行，无第三方运行依赖。安装名称为 MeadowJourney，便于 SideStore 重签。

## 历史版本：build 9 改进

- 阳光改为清晰的移动光带，增强云影明暗变化；镜头固定、人物暂停时仍持续变化。
- 树冠采用根部固定的阵风摆动，最小缩放下也能观察，树影共享风动与太阳方向。
- 三位人物增加四种斜向朝向，形成八方向步态；按路程推进左右腿接触姿势，降低身体起伏。
- 重做花簇与灌木透明根部，去除连续草垫与背景色晕，减少零散植被密度。
- 保留屋脊旗杆、脚底投影锚点和接触阴影修复；继续使用现有 2.5D 轮廓投影。

场景由 SceneMap.json 与独立地表、树木、岩丘、营地、塔楼、栅栏和植被资源组成，人物与环境按脚底位置排序。双层雾、蓝旗和空气微粒持续运动。基础 RGBA 纹理预算为 55.14 MiB，进程内存另行采样。

## 安装

[直接下载最新 1.6.1 build 26 IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b26.ipa)。在 Safari 保存到“文件”，再打开 SideStore → My Apps → ＋，选择该文件重签安装。

[安装与校验说明](Downloads/README.md) · [录像与截图](Media/README.md) · [迭代记录](docs/ITERATION_STATUS.md) · [PR #3](https://github.com/liamchan-rgb/experiment/pull/3)

## 操作

- ▶ / Ⅱ：开始或暂停沿道路巡逻，继续时保留已指定目的地。
- 点选 P1 / P2 / P3，再点道路：沿最短路径移动并停下。
- 点问号：抵达探索点后解锁地点。
- ↻：恢复初始人物位置、镜头与探索状态。
- ＋、双指缩放和拖动：调整镜头。
- 点“安然”查看说明；长按切换帧率、物件数、纹理预算与进程内存。

## 验证与构建

安装包来自源码 `1fc2415` 与 [成功构建 38696431707](https://github.com/liamchan-rgb/experiment/actions/runs/38696431707)：25 项模型／资源／实际像素渲染测试、iPhone 与 iPad 各 2 项交互测试、原生录屏和设备 Release archive 均通过。构建来源与 IPA 校验值保存在 Media/BuildInfo-v1.3.0.json。模拟器数据与物理设备性能分开记录。

打开已提交的 MeadowJourney.xcodeproj，Scheme 为 MeadowJourney，无需 XcodeGen 或 CocoaPods。

```bash
xcodebuild build -project MeadowJourney.xcodeproj -scheme MeadowJourney \
  -configuration Debug -destination 'generic/platform=iOS Simulator' \
  CODE_SIGNING_ALLOWED=NO
```

PR 更新时在 macos-15 编译、测试与录制八方向移动和最小缩放静止镜头；最后构建设备 Release archive 与未签名 IPA。Actions 中的 MeadowJourney-unsigned-IPA 包含 IPA；ios-visual-review-* 保留原始资料，ios-compact-review-* 保留原尺寸压缩录像与来源记录。工作流可用 review_run 参数重新整理已有成功构建。

资源说明见 [docs/ASSETS.md](docs/ASSETS.md)。项目静态检查：`python3 scripts/validate-project.py`；资源预处理：`python3 scripts/prepare-assets.py`。
