# 3D 战斗场景（HD-2D：3D 场景 + 像素人物）

模型：Quaternius「Stylized Nature MegaKit」免费版（CC0 1.0），原始包放在仓库 Release `art-nature-megakit` 里，不进 git。

准备：
```
curl -L -o kit.zip https://github.com/liamchan-rgb/experiment/releases/download/art-nature-megakit/Stylized.Nature.MegaKit.Standard.zip
unzip kit.zip -d <某目录>
ln -s <某目录>/glTF scenes3d/models
ln -s ../node_modules/three scenes3d/three
python3 -m http.server 8765 --bind 127.0.0.1   # 在 scenes3d 里
```
然后用无头 Chromium（Playwright，`--use-angle=swiftshader`）打开 `index.html?w=1920&h=1152&t=0&cam=0` 截图；`window.stage` 给出各站位的屏幕坐标。

`meadow.js`：林间营地。地面贴图程序生成，树石草花按规则摆放（舞台中间留空），太阳 + 软阴影 + 雾，后期移轴景深、泛光、调色、暗角。

## 像素风（已存档，不再继续）：物体像素化，雾 / 景深 / 光不像素化

```
index.html?w=1920&h=1152&px=6&mode=albedo   # 低分辨率像素块：物体本身（描边、明暗分档），无雾
index.html?w=1920&h=1152&px=6&mode=depth    # 全分辨率深度（RGB 打包）
python3 tools/scene_compose.py albedo.png depth.png 0.3 200 out.png 40
```
`px=6` 时场景像素和人物像素一样大（1920 宽）。合成时物体限色、最近邻放大，雾、景深、光池、光束、泛光、暗角在全分辨率上按真实距离平滑叠加。

## 卡通渲染（当前方向）

```
index.html?w=1920&h=1152&style=toon
```
代码在 `toon.js`：
- 光照分 3 档（暗 / 半调 / 亮，硬边）；
- 环境光统一偏冷蓝，所以暗档和投影是冷色；
- 树冠用球形法线，草花用朝上的法线；
- 树皮、石头、地面贴图混一部分低精度 mip，压平成色块；
- 另渲染「法线 + 深度 + 描边权重」图，按深度跳变画外轮廓、按法线突变画内折线；
- 手绘感：线条位置抖动、笔压粗细、远处变细变淡、偶尔断笔，线色取底色压暗偏冷紫（彩色墨线）。

预览：`vfx-preview/meadow3d-toon.png`。

## 怪物：苔石魔像（代码建模）

```
index.html?style=toon&monster=golem               # 站在怪物位 m1 的战斗全景
index.html?style=toon&monster=golem&shot=monster  # 近景；&rot= 转朝向，&t= 待机动作时间（2.4 秒一循环）
```
`golem.js` 参考素材包石头的做法（形体干净 + 手绘贴图）：
- **形体**：每个能动的部件（躯干连头、左右手臂、下身）是一整块。做法如下：
  - 用 SDF 把椭球平滑融合在一起；
  - 用随机平面凿出切面和硬棱，眼窝和心核的坑直接挖出来；
  - 用 marching cubes 转成网格，法线取距离场梯度。
- **表面**：在着色器里逐像素画，不用顶点色。内容包括：
  - 石色斑驳和少量细裂纹；
  - 凸棱提亮、凹处压暗（曲率来自距离场的拉普拉斯，写在 `aCurv` 属性里）；
  - 朝上和凹处的苔藓：硬边，加一圈黄绿毛边；
  - 从心核往外的发光裂纹，会脉动。
- 通过 `toon.js` 的 `userData.toonPatch` 挂进同一套卡通光照和描边。
