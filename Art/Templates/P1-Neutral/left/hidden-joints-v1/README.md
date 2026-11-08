# P1 向左中性人体隐藏关节补全 v1

本目录的离线生成器默认读取 `walk-r3-complete-transitions`，也支持 r2 或同结构姿势底包，输出同槽隐藏 underlay。当前已导出全部13姿势，输出目录名沿用 source pose index，方便主候选按原姿势读取。

每姿势包含躯干、双臂、双手和双腿共7张 256×256 RGBA PNG。主装配按原 `drawOrder` 在每个可见槽之前画同槽 underlay。`geometry.json` 固定记录关节坐标、姿势phase、近远侧顺序、几何mask和材料色板。

补片由固定解剖几何生成。手臂沿肩→肘→腕绘制连续caps，近侧左臂只用左手槽固定肤色色板，远侧右臂只用右手槽色板；腕口有匹配同侧肤色的连接cap。腿根由髋→膝绘制厚实连续cap，使用同侧肤色色板，不复制另一条前景腿像素。躯干采用独立的颈根、背心和短裤几何岛；颜色只取躯干槽中央局部颈/背心/短裤区域的固定swatch，躯干补片以纯材料色生成，不复制会包含手臂纹理的合成图。`geometry.json` 和 `verification.json` 记录并核对每槽允许的材料色板。

只导出会被当前姿势后续不透明槽遮住的补片像素。近侧肩补片不会盖住白背心，固定姿势下原有非透明RGBA逐像素不变，新增可见像素为0。原 r2/r3 输入目录只读；本目录不修改主exporter、profile或项目文档。

## 重导

默认读取r3（当前先排除仍在返修的9、12姿势）：

```sh
python3 Art/Templates/P1-Neutral/left/hidden-joints-v1/export_hidden_joints.py --exclude-indices 9,12
```

显式读取r2：

```sh
python3 Art/Templates/P1-Neutral/left/hidden-joints-v1/export_hidden_joints.py --base Art/Templates/P1-Neutral/left/walk-r2-head-motion
```

指定base需含 `authoring.json`、`registered/`，以及分姿势层和合成帧。脚本优先使用 `source/visible-layers/` 与 `source/visible-frames/` 作为合入 underlay 前的不可变快照；这两目录不存在时才回退到 `layers/`、`frames/`。当前r3验证使用了两个快照目录。重导时色板提取、遮罩、合成核验和关节探针都不会读取已合并补片，不会逐次扩大遮罩或污染选色。过渡姿势肩、肘、髋取自r3 `authoring.json`；手腕中心和脚底标记取自 `source/transition-authoring.json`，因此09/12修订后的手腕导板可复现。该source记录缺失时再回退到r3 authoring和固定姿势导板。

`verification.json` 验证原图可见RGBA、同侧肢体色板归属和局部接缝。局部探针把臂图在肩根/腕口作±1、±2px八向偏移，腿只检查髋根；只统计不透明关节核心，不把轮廓抗锯齿、膝踝旧位置或任意动作当成关节缺口。当前13姿势原可见RGBA逐像素保持一致、额外可见像素为0、同侧色板检查通过，局部探针均为0新增透明核心像素。该结果不代表任意骨骼旋转或八方向动作完成。
