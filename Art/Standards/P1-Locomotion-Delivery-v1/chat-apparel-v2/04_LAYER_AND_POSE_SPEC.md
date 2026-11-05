# 给绘图Chat：五视角母版规格

## 先明确数量

每件甲只要求五个静态视角，每视角四层。**20张母版是美术输入；104姿势/416层引用是Codex之后的程序输出。** 不要求Chat逐帧重画或逐帧设计挂点。

| 母版view键 | 对应原人物静态参考 | 参考文件 |
| --- | --- | --- |
| `front` | down / idle / frame0，正面 | `examples/body-guides/front.png`与`front-joints.png` |
| `front-quarter-left` | down-left / idle / frame0，左下 | 同目录`front-quarter-left*.png` |
| `profile-left` | left / idle / frame0，正左 | 同目录`profile-left*.png` |
| `rear-quarter-left` | up-left / idle / frame0，左上 | 同目录`rear-quarter-left*.png` |
| `back` | up / idle / frame0，正背 | 同目录`back*.png` |

view表示母版观察方向；sleeve.left/right表示角色自身左右，不是一回事。正面对着我们时，自身左臂在画面右。关节导板青色是自身左肩—肘—腕，橙色是自身右链，白色是颈根，粉色是髋；标线只能在参考图里。

原down/idle0的左肩/肘/腕为(144,136)/(150,153)/(152,167)，右侧为(114,136)/(108,153)/(106,167)，颈根(128,132)。其余视角用各自导板。正左的motion未显式记录手腕，导板沿用现有cuff_marker从原手的实心像素定位，记录在examples/body-guides/joints.json；Chat不需要自己猜手腕。新母版已对齐静态参考时，不再加旧registration/bodyTranslation；也不套旧1774×887总图的裁片坐标。

## 四层怎么拆

| layer键 | 母版中画什么 | 禁止混入 |
| --- | --- | --- |
| `outfit.torso` | 衣身/胸腹甲、领口、腰带与扣件 | 独立随臂运动的肩甲、原手、裤子、背剑 |
| `outfit.sleeve.left` | 自身左肩口、肩甲、袖子/臂甲、袖口 | 自身右袖、手、底衣残边 |
| `outfit.sleeve.right` | 自身右侧对应部分 | 自身左袖、手、旧蓝衣残块 |
| `outfit.hem.front` | 独立护裙衣片；上缘藏在腰带后 | 裤腰/裤腿、武器、地面影 |

肩甲虽可被衣身局部遮挡，像素仍归对应袖层，不同时画在胸甲和袖甲上。母版留合理隐藏接合余量。远侧袖即使静态合成里看不见，也应依据正面结构补齐隐藏袖面，不能靠空白永久缺袖。无护裙设计时可明确声明该层透明及原因。

## 母版PNG硬规格

- 固定256×256，真实RGBA透明PNG；sRGB、straight alpha。保留完整画布和透明边距，左上原点，x向右/y向下。
- 对齐本view的原人物idle导板，不按alpha外接框裁切/居中，不拉宽拉高人物、不改关节或比例。
- alpha=0处RGB归零；必要半透明边缘保留，不粗暴阈值化啃掉金边/轮廓。
- 不画皮肤/手/头发/脸/裤靴/武器/背景/棋盘格/文字/水印/地面投影。源稿可有锁定人体参考层，导出衣物PNG时关闭它。
- 衣物自阴影允许，固定左上光，硬边与像素密度匹配原人物，不用光晕或随机纹样掩盖服帖问题。
- 只能交高分辨率整人概念图时标`design_only`，不能切成20张就称已对齐母版。Codex可继续固定注册/分层，缺项须列明。

## 文件名与清单

```text
masters/front/outfit.torso.png
masters/front/outfit.sleeve.left.png
masters/front/outfit.sleeve.right.png
masters/front/outfit.hem.front.png
masters/front-quarter-left/…四层
masters/profile-left/…四层
masters/rear-quarter-left/…四层
masters/back/…四层
```

`master-manifest.json`是母版交接清单，**不是引擎asset.json**。它登记五view原参考姿势、20层路径与真实存在的源稿/色板。见[蓝衣静态分层位置清单](examples/blue-coat-masters/master-manifest.json)、[待填模板](templates/README.md)。

源稿可以每view一个四层ORA/PSD/SVG，也可一个五组、每组四语义层的文件。不能把整个人嵌入一张图到SVG就称四层源稿，也不能只给空PSD文件名。

## 右向、动作与动画是谁做

Codex沿用现有五视角到八方向映射，校正左右、近远、光照与衣襟。确有无法由原母版得到的不对称设计或右向效果时，只补对应静态view；每个新增view最多四层，不重画全套动作。

动作沿用原motion：idle、walk8、start2、stop2，共13姿势/方向。Codex批量导出，优先修母版或共用裁片/控制参数；少数特例才记录可重导的局部修正。任意PNG不是零适配即可挂好，但也不需要重新手画每帧。

游戏移动×3不要求Chat改变八帧原画或时钟。正常walk GIF为8×120ms，指定起停沿原入口/出口，均由Codex真实导出后合成。详细输出规格在[integration](integration/README.md)，Chat无需制作这些运行文件。
