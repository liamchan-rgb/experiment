# P1 行走外观美术交付标准 v1

本标准面向**在目前的人物身体和行走动作上新增外观**的 agent。当前制作基线为2026-10-25交付的 build39（1.6.13）：同一身体、八方向、站姿＋八帧行走＋两帧起步＋两帧收步。先读本文件，再读[可直接复制的 agent 任务书](AGENT_BRIEF.md)。[机器可读规格与基线摘要](contract.json)、[交付记录模板](handoff-template.json)用于记录，不能代替实际装配和人工美术审核。

**当前完整覆盖是每方向13姿势、八向104条绑定，不是旧草案的72条。** 可以复用图片，但不能少交绑定。此标准说明当前资源如何制作与交付，不把仍为draft的全局人体profile擅自改成locked，也不把新外观、隐藏人体完整性或实机效果自动记为通过。

## 1. 从这些实际文件开始

| 用途 | 当前依据 |
| --- | --- |
| 唯一共用身体 | [base/asset.json](../../Parts/P1-v1/eight-way-v1/base/asset.json)，ID `p1-eight-way-base-v1` |
| 当前104姿势、头变换、关节/足点、逐帧遮挡 | [motion.json](../../Integration/P1-modular-eight-way-v1/motion.json) |
| 当前资源登记 | [catalog.json](../../Integration/P1-modular-eight-way-v1/catalog.json) |
| 头部导板、五官区域、保护眼窗、槽位定义 | [profile.json](../P1-Parts-v1/profile.json)、[asset.schema.json](../P1-Parts-v1/asset.schema.json) |
| 源方向与统一方向的注册/相位关系 | [authoring.json](../../Integration/P1-modular-eight-way-v1/authoring.json)、[mapping.json](../../Integration/P1-modular-eight-way-v1/mapping.json) |
| 可直接对照的独立部件 | [eight-way-v1](../../Parts/P1-v1/eight-way-v1/)；其中每包104条绑定 |
| 已接入demo的两套数据预设 | [selection.json](../../Integration/P1-modular-demo-v1/selection.json)、[导入说明](../../Integration/P1-modular-demo-v1/README.md) |
| 当前整身、正常速度与技术检查依据 | [八向资源审核](../../Review/P1/modular-eight-way-v1/)、[实际导入/控制器审核](../../Review/P1/modular-demo-v1/)、[build39来源](../../../Media/Build39/package.json) |

新任务先记下身体清单、motion、profile、schema及输入素材SHA256。`contract.json`保存本版摘要；如果后续主线主动升级基线，应明确更新版本和差异，不能忽略摘要变化。旧图集和失败稿可作历史对照，不能覆盖上述当前基线。不要运行旧导出脚本把当前身体/九个既有资源包重写一遍来“登记”新外观。

身体清单摘要不能单独证明身体PNG没被改；contract另附当前九包目录树摘要与算法，涵盖实际PNG、可编辑文件和清单。新资源放在新目录，不写回该冻结目录。

## 2. 要交多少资源

| clip | frame | 每方向绑定数 | 节奏 |
| --- | --- | --- | --- |
| `idle` | `0` | 1 | 站姿 |
| `walk` | `1..8` | 8 | 每帧120ms，循环960ms |
| `walk-start` | `1,2` | 2 | 各120ms，接本方向指定行走入口 |
| `walk-stop` | `1,2` | 2 | 各120ms，从本方向指定行走出口退出 |

八个方向必须明确提供：`down`、`down-left`、`left`、`up-left`、`up`、`up-right`、`right`、`down-right`。这是顺时针展示次序；运行图集的行序不同，见第6节。

只生成一件衣服，就交这件衣服的完整资源包，不必同时重画发型、五官、裤靴或身体。已有部件通过清单组合复用。完整可使用外观包须覆盖104条绑定；阶段性单方向稿必须标清部分覆盖，不能进入完整八向预设或以自动镜像/缺帧回退冒充齐全。

**104条绑定不等于必须画104张不同图片。** 短发/五官等可以每方向一张96局部图，被13姿势引用并随原头变换轻摆；会变形的袖子、裤腿、靴面、衣摆等必须提供实际适配的逐姿势内容，不能把一张静止衣服贴给所有帧。复用必须在全部姿势装配后仍成立。

## 3. 画布、坐标和禁止事项

- 输出为透明 **RGBA PNG**；动作部件使用固定256×256画布，头部局部资源使用固定96×96画布。左上原点，x向右、y向下，保留透明边距，不碰画布边界。透明像素的RGB清零；保留需要的正常半透明边缘，不靠粗暴阈值啃掉轮廓、金边或眉口线。
- `pose-map` 是已经注册的256整画布；`head-local` 按该帧 `headToCanvas` 放置。颈根、关节、足点、头部位置和轻摆均读当前motion；不要自行估计中心，也不要为贴合新衣服移动身体或冻结头部。
- **从当前统一模板制作时，注册平移和步相旋转已经做过，不可再套一次旧方向registration或walkSourceOrder。** 从历史源稿迁移时才按明确记录转换一次，并保留源坐标、映射和摘要。
- 身体、体型、头皮/耳朵/颈部肤色、已有动作、相位及遮挡顺序保持。不得按外观ID换身体、缩头、拉腿、改眼位，或向旧部件加配套补丁才能显示新外观。
- 禁止按alpha外接框自动裁切/居中/塞目标框、独立拉伸宽高、逐帧自动缩放、用材质颜色猜运行时语义区域。离线导出若使用较大工具导板，只能用**事先固定并记录的整张导板变换**，不逐角色/部件拟合。
- 新画稿保持现有像素密度、轮廓厚度、整体比例和固定左上光源。可以换版型/发型/配色，不能同一件衣服在另一个方向变成不同长度、不同结构，或走路时材质亮度闪烁。
- 人物PNG不烘焙地面椭圆/投影；地面投影由显示与阴影共用的alpha生成。衣物自身的体积阴影可以画在衣物材质里。

## 4. 部件必须真正独立

当前快线使用下列在全部104姿势中已有的槽位。一个PNG只包含自己负责的部件，manifest不得越权，也不得同时选两个占同一槽位的包。

| 新增类型 | `part` / `mode` | 当前槽位 | 必须排除的内容 |
| --- | --- | --- | --- |
| 头发 | `hair` / `head-local` | `hair.front` | 脸皮、耳朵、颈皮、眼眉鼻口、配套头形 |
| 五官 | `face` / `head-local` | `face.eyes`、`face.brows`、`face.nose`、`face.mouth` | 头皮/脸颊/下颌/耳朵色块或新的面部轮廓 |
| 上衣/外套 | `outfit` / `pose-map` | `outfit.torso`、`outfit.sleeve.left`、`outfit.sleeve.right`、`outfit.hem.front` | 手、裸体胳膊、裤靴、背剑或另一衣型残留 |
| 裤靴 | `outfit` / `pose-map` | `outfit.pants.left`、`outfit.pants.right`、`outfit.boot.left`、`outfit.boot.right` | 皮肤腿、手、上衣、地面阴影 |
| 背负武器 | `weapon` / `pose-map` | `weapon.back`；声明 `carryProfile: back-scabbard` | 身体/衣服、手和地面投影，不依赖握持socket |

表中的上衣四槽/裤靴四槽是当前完整包布局；若明确交较小部件包，可只声明自己拥有的合法槽，但选择矩阵必须补齐其余衣物，且无重复槽。例如只交鞋时，不能再同时选择包含同一双靴槽的完整lower包；可用明确的裤子分包或交完整新lower解决，不能改旧lower来迁就新鞋。

无独立衣摆的上衣可以显式绑定透明256 PNG；纯背向 `up-left/up/up-right` 的四个五官层按当前导板绑定透明96 PNG，这是正确隐藏，不是缺眼睛。其他方向的五官不得丢失，前发不得覆盖profile的保护眼窗。合法领口露颈与正常耳根要保留，不把所有皮肤都补成衣服。

若长发需要逐帧变形，可使用schema允许的hair `pose-map`，仍须完整104绑定并验证眼窗/遮挡；不能强行把它当刚性短发。`hair.back`、`outfit.hem.back`虽在通用schema中存在，**当前八向motion并非全部支持这些槽位**。需要新增槽/持握武器/披风层序时应作为明确的动作合同扩展另行记录，不能暗改当前motion然后声称新外观零动作修改接入。

### 肢体、衣物与遮挡质量

- 以角色自身左右命名，不以屏幕左右命名。逐侧检查肩—肘—腕、髋—膝—踝—脚趾；肩口/腋下/袖口、臀与大腿根、裤口/靴口都要完整。整个人alpha连通，不能证明单侧手臂/腿链没有断裂。
- 袖子与对应胳膊/手共用姿势依据；裤腰随骨盆，左右裤口分别随对应大腿，靴面/鞋底随足姿。禁止“腿动裤子不动”、裤腿块状拉伸、手漂到袖外、靴筒吞掉膝盖。
- 按每个姿势原 `drawOrder` 合成；同一个全局层序不能替代八方向遮挡。不得把手臂残线混进头层、白背心边混进袖层、武器混进衣摆。
- 默认武器背负，保持**同一物理右肩→左髋的斜背关系**。左右视角投影可以不同，不能机械整图镜像后换肩，也不能为避开袖子改成脊柱式竖背。检查剑柄/护手/鞘尖及头发/肩袖遮挡，不能只验证武器PNG非空。
- 镜像只是一种离线制作方法：同时处理角色左右语义、近远层次、头局部挂点和光照。新外观通常直接跟当前统一姿势制作，不应再次镜像motion、关节或支撑标签。

## 5. 文件交付目录与清单

建议新包放 `Art/Parts/P1-v1/<新外观>-v1/`，新审核放 `Art/Review/P1/<新外观>-v1/`；不覆盖既有包或失败稿。

```text
<新外观>-v1/
  asset.json                 # 与现有schema完全一致，104条显式绑定
  authoring.json             # 固定注册、拆分规则、输入与导出方法
  source/                    # 未修改原稿、工具提示词/工具原图、导板与输入摘要
  editable/                  # 可编辑分层源，如ORA/带嵌入图层的SVG；不是只有整人合成图
  png/<direction>/<clip>/...  # RGBA部件；可按清单复用路径
```

`asset.json`必须有 `schemaVersion/id/version/part/compatibility/mode/slots/directions/clips/sourceFiles/bindings`。兼容值固定为 `rig:p1-chibi-v1`、`bodyProfile:p1-standard`、`actionSet:locomotion-v1`；`id`是唯一查询键，不能触发外观专属引擎逻辑。`sourceFiles`中的文件真实存在；`bindings[].layers`与声明slots一致；路径相对包目录且不越界。

可复制对应的真实[头发清单](../../Parts/P1-v1/eight-way-v1/hair-chestnut/asset.json)、[五官清单](../../Parts/P1-v1/eight-way-v1/face-blue/asset.json)、[上衣清单](../../Parts/P1-v1/eight-way-v1/wayfarer/asset.json)、[裤靴清单](../../Parts/P1-v1/eight-way-v1/lower/asset.json)、[背剑清单](../../Parts/P1-v1/eight-way-v1/weapon/asset.json)作结构参考，但必须换成新ID/路径及真实新画稿，不能把复制改名当作新外观完成。

在新审核catalog中保留原base/复用资源条目，再加入新manifest；使用当前motion装配。全身图集仅是预览/运行导入产物，不能替代独立部件、清单、源稿和可复现导出步骤。

## 6. 方向、步相和demo图集契约

当前统一 `walk01..04` 对应全局phase0..3（角色右脚支撑），`walk05..08`对应phase4..7（左脚支撑）。不按画面最低的脚猜支撑，因为视角深度不同。入口/出口从现有authoring读取；下表是当前快照，**不是要求重排新外观的帧**。

| 方向 | runtime facing | 图集/行（从0计） | entryPhase | exitPhase |
| --- | --- | --- | --- | --- |
| down | 0 | Directions/0 | 1 | 0 |
| down-left | 5 | Diagonals/1 | 4 | 3 |
| left | 1 | Directions/1 | 4 | 3 |
| up-left | 6 | Diagonals/2 | 4 | 3 |
| up | 2 | Directions/2 | 4 | 3 |
| up-right | 7 | Diagonals/3 | 0 | 7 |
| right | 3 | Directions/3 | 0 | 7 |
| down-right | 4 | Diagonals/0 | 0 | 7 |

起步两帧接统一 `walk(entryPhase+1)`，收步从统一 `walk(exitPhase+1)`退出。新外观跟随相同索引，不能把所有起步硬接全局phase0。移动中切向保持全局距离相位，不丢帧、复制帧凑数或改变120ms节奏。

需要demo接入时，导入后的每方向13源列从0计：`idle0 / walk1..8 / start9,10 / stop11,12`，每张图集3328×1024（13×4个256格）。运行24个距离刻度中每3刻度取一张P1步行图，虚拟帧25/26/27/28取源列9/10/11/12；前景、阴影和足点必须相同。不要从旧25列P2/P3图集推导P1格式，也不能只换显示而忘了阴影。

当前停步策略会在原地补到指定出口再收步，不是已有任意相位制动动画。新外观要覆盖现有指定起停，不把增加制动/新动作夹进外观制作。需要接入demo的任务才追加当前catalog/selection数据；保留旧登记，不修改旧条目或通用装配器、身体、motion、profile来迁就新ID。当前import/review脚本有固定基线路径与部分固定演示组合，不能只重跑旧脚本就说新包被覆盖；须在新审核catalog中实际选中新增ID，记录新选择和输出。

## 7. 必做检查与验收证据

1. **包检查**：逐新manifest执行 `python scripts/check-character-part.py <asset.json>`；完整方向/clip/frame/slot、图片模式/尺寸/边距、五官区/眼窗、路径和源文件全通过。`--schema-only`只验声明，不能算画稿通过。当前profile仍draft，不能为获得 `--production`绿灯改状态、删检查或放宽几何阈值。
2. **真实装配**：调用 `scripts/compose-character-parts.py` 或其 `Compositor`，用同一 `p1-eight-way-base-v1`、当前motion和新catalog实际选择新ID。不要只看生成工具原图。记录每个方向/clip/frame/组合的实际输出与SHA256。
3. **全组合与开关**：新增资源与所有声明兼容的现有头发、五官、上衣、裤靴、空背/背剑交叉装配。去掉发型应有完整头皮，去掉五官为空白脸，去掉上衣不残留袖子/手/剑，空背不留剑影。不能只挑最好看的两套。现有2上衣×2发色×2五官×2背负选择=16组合、1664次装配；增加第3件同类资源通常变成24组合、2496次装配。以实际资源维度计算，不抄旧计数；背向不可见五官可有相同像素，但须实际执行绑定装配。
4. **保护基线**：身体/motion/profile及旧部件摘要不变，新资源加入不改变旧搭配像素；允许增加catalog/selection数据，但不能用改旧身体、旧资源、层序或按ID分支来获得通过。检查无新增安全衣/短裤/裸体漏出，保留真正领口；检查原可见手和五官贡献、衣物/武器开关、鞋底/接缝和半透明边缘。自动颜色/连通数字只作辅助，不能代替逐侧链条审核。
5. **主线程人工复核**：主线程亲看所有新增相关搭配的全部当前姿势整身1×/2×，不能只放大脸。核眉眼鼻口/耳颌整体比例、头部轻摆、左右肢链、近远、衣摆/裤口/靴底、残像/断缝/跳亮和背剑。智能体/生成工具的“通过”不是交付许可；发现问题由主线程自己修并重审，不交给用户当第一轮质检。多搭配可拼图审核，必须如实列已看范围。
6. **最终动图**：从实际装配/实际导入格子生成正常全身GIF，步行8×120ms；指定起停可沿 `idle→start1/2→原入口开始的两圈walk→stop1/2→idle` 共22帧，首尾480ms、中间20帧各120ms；另查 `08→01`、所有起停边界、顺/逆向切向与全局步相。新画稿不能生成或用慢动作预览替代正常速度。工具只能静帧查看时，亲看实际GIF解码帧，明确记录，不能称连续播放已验收。
7. **可复现与发布**：记录重导命令并比较输出字节/像素摘要；新包/源稿/可编辑文件/清单/审核材料的远端依赖都存在。最终回复必须实际嵌入正常全身GIF，附可复制浏览器HTTPS直链和站姿PNG；实际GET核对200、MIME、SHA256、帧数、时序和循环，再记delivery回执。不能只交本机路径或“已合成”。更新 `docs/ITERATION_STATUS.md` 和当前人物审核记录；新美术认可默认 `null`，仅用户明确认可实际展示的范围后单独记录。

装配命令结构如下（先准备真实新包和catalog，示例占位路径不代表已交付）：

```bash
python scripts/check-character-part.py Art/Parts/P1-v1/new-coat-v1/asset.json
python scripts/compose-character-parts.py --root . \
  --catalog Art/Review/P1/new-coat-v1/catalog.json \
  --motion Art/Integration/P1-modular-eight-way-v1/motion.json \
  --base p1-eight-way-base-v1 --asset p1-new-coat-v1 \
  --asset p1-eight-way-lower-v1 --asset p1-eight-way-hair-chestnut-v1 \
  --asset p1-eight-way-face-blue-v1 --asset p1-eight-way-weapon-v1 \
  --direction down --out Art/Review/P1/new-coat-v1/composed/down
```

需对全部方向和兼容组合执行，不只运行上述向下示例。新资源应增加实质不同的外观，证明无需外观专属引擎/动作修改；改名复制或只复用前两件的漂亮搭配不能冒充第三资源验收。

## 8. 最终交付清单与范围

- [ ] 新资源的八向104绑定、正确槽位/尺寸/透明PNG；原稿、提示词、可编辑分层、导出方法与输入摘要齐全。
- [ ] 新catalog真实选择新增ID；完整组合/开关/原像素保护/重导验证有输出；检查范围和计数如实填写。
- [ ] 主线程整身1×/2×及最终正常GIF逐帧审核完成，已修已知问题；附站姿、步行、指定起停和切向证据。
- [ ] 浏览器HTTPS实际GET通过，远端依赖齐全；填写[handoff-template.json](handoff-template.json)所列内容，未运行/未认可项保留false/null，空模板不能当验收结果。
- [ ] 日志、当前审核记录和交付回执同步到GitHub，原稿/旧认可/失败版本保留。

仅美术任务交资源与预览，不自动打IPA。用户任务包含demo/打包时再导入、核前景/阴影与运行索引，交**直接 `.ipa` HTTPS**，不交外层ZIP；设备编译可做，模拟器/实机运行仍按用户授权，当前由用户实机反馈。女性新体型、完整骨架重建、实时自由混搭、持握战斗和新制动动作不借新增行走外观之名自动扩展。


## 2026-10-26 猎弓携带合同扩展

新增carryProfile: back-bow，仍仅weapon.back、pose-map、完整八向104绑定、同一物理右肩到左髋、沿原drawOrder/身体动作。asset.schema.json与profile.json明确增加枚举，check-character-part.py对两种背负类型执行同一严格检查；没有删检查或放宽几何阈值。原冻结身体/动作/旧部件不改。猎弓可编辑SVG/PNG与导出源记录在新包hunting-bow-v1；这是一项明确的携带合同扩展，不将其误称为profile字节未变。新美术认可仍null。
