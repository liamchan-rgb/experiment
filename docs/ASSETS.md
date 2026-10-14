# 画面资产

- `Art/Reference/sample.jpg`：用户提供的 1280 × 720 视觉样例。
- `Art/Generated/meadow-background.png`：基于样例清理 UI、人物、标签后的背景，保留营地、塔楼、道路、草地、岩丘和暖色光照。图像生成会有少量纹理差异。
- `Art/Generated/heroes-source.png`：生成的 4 列 × 3 行透明人物行走动画，三行分别对应 P1、P2、P3。
- `Sources/Resources/Assets.xcassets`：实际随 App 打包的地图、1024 × 768 动画表、营地图标和启动颜色。

`scripts/prepare-assets.py` 使用 Pillow 将各帧非透明内容归一化为 160 像素高，脚底统一在单元格 y=224；SpriteKit 使用 64 × 64 的单元格显示人物，实际人物约 40 个地图像素高。脚底坐标是移动逻辑的锚点。重生成资产需要 `python3 -m pip install Pillow`，正常 Xcode 编译不需要 Pillow。

地图以样例的 1280 × 720 坐标系绘制。宽屏设备使用等比例填满，顶部和底部可能裁掉少量环境；按钮独立遵循设备安全区。缩放不改变路线坐标。
