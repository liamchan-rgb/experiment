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

## 像素风（物体像素化，雾 / 景深 / 光不像素化）

```
index.html?w=1920&h=1152&px=6&mode=albedo   # 低分辨率像素块：物体本身（描边、明暗分档），无雾
index.html?w=1920&h=1152&px=6&mode=depth    # 全分辨率深度（RGB 打包）
python3 tools/scene_compose.py albedo.png depth.png 0.3 200 out.png 40
```
`px=6` 时场景像素和人物像素一样大（1920 宽）。合成时物体限色、最近邻放大，雾、景深、光池、光束、泛光、暗角在全分辨率上按真实距离平滑叠加。
