# P1 向下独立衣物与短剑 v1 · 持握要求修订

用户反馈“剑没有握持感”，当前转入[同组握持修订v2](../v2/README.md)。本目录及ZIP保留原交付快照，以下为当时制作记录。

用户于 2026-10-19 认可[三发型×两五官](../../../P1-Modular/down/v1/approval.json)。本组在同一中性人体上新增一套森林绿短外套、深灰裤装、棕色踝靴和一把独立短剑；当前只回审这组向下衣物／持握，不把自动检查当作美术认可。

[正常速度循环](walk.gif) · [站姿对照](review.png) · [00–08 编号图](poses.png) · [衣物／武器独立层](independent-parts.png) · [六种头部搭配](heads-dressed.png) · [验证记录](validation.json) · [完整源文件与工具包](../../../../Prototypes/P1-Wardrobe-v1.zip)

循环左至右：共同底模／空手、穿衣／空手、穿衣／持剑。三列使用同一身体与动作，只播放 01–08，每帧 120 ms、周期 960 ms，不提供新的慢动作。PNG／GIF 可直接查看，iPad 无需运行本地 HTML；历史在线换装演示尚未更新。

## 实际资源

- [`outfit-forester`](../../../../Parts/P1-v1/outfit-forester/asset.json)：躯干、左右袖子、前衣摆、左右裤腿、左右靴子八层，九姿势共 72 张 256×256 透明 PNG、九份 ORA／SVG。服装无头、手、皮肤或身体底片。上衣主体与肩部衣料复用同一画稿，按已认可身体做整数位移；袖子和裤腿逐帧绘制；靴子统一复用00的同一对完整画稿，按足底点做明确整数放置，少量横向贴合偏移写入authoring.json，鞋型／大小／足底高度不跳变。独立裤装原稿补齐腰部／踝部隐藏连接，分区及位置写入 authoring.json，不在运行时补画或猜色。
- [`weapon-short-sword`](../../../../Parts/P1-v1/weapon-short-sword/asset.json)：一张 64×96 透明 PNG，九个绑定复用；实际剑柄中心 pivot=(32,26)，挂到 `grip.right`，由原手层盖住剑柄。握点来自这把剑自身，不要求配套手臂或身体。
- 三发型×两五官×衣物开关×短剑开关，共 24 种搭配、216 个站姿／动作输出。包含裸体持剑，证明剑不依赖外套；头部、衣物、武器各自不随其他选择变化。

十五份图像工具原始输出、真实提示词、参照及摘要见各包 generation.json。第2、3、6、7帧有局部贴合修订，旧稿保留在drafts。最终弃用逐帧生成的靴子，选同一对完整画稿保证鞋型和足底；早期靴子变体仅保留制作历史，不参与运行。原已认可素材未覆盖。整画布固定注册，禁止内容外接框适配或独立缩放脚。

## 本轮发现并修正的底模分层问题

长裤试穿暴露出原中性第 7 帧前景右腿层夹带 48 个后腿像素，导致后腿长裤被皮肤盖住。另存[共同底模 walk-r2](../../../P1-Neutral/down/walk-r2/README.md)，把这段像素归到左腿层；仅两张图层变化，九张合成人体逐像素、原 PNG 字节完全相同。所有 24 种搭配（包括不穿衣）统一使用 r2，无外观 ID 条件底模。

原 walk-r1 和头部资源保持不变。新 motion.json 的全部姿势、关节、握点、角度和层序与旧头部模块相同，**只更换 baseManifestSHA256 钉住修正后的公共底模**。因此本轮不宣称衣物接入过程“身体／动作文件零修改”；[接入记录](integration-after.json)明确记录公共底模分层修正和清单摘要更新。装配器与规范未改。[第三发型零代码证明](../../../P1-Modular/down/v1/integration-after-third.json)继续有效。

## 用原装配器挂载

在仓库或完整包根目录安装 Python 3、Pillow、NumPy、jsonschema：

```sh
python3 scripts/compose-character-parts.py \
  --catalog Art/Templates/P1-Wardrobe/down/v1/catalog.json \
  --motion Art/Templates/P1-Wardrobe/down/v1/motion.json \
  --base p1-neutral-down-walk-r2 \
  --asset p1-hair-silver-v1 --asset p1-face-blue-v1 \
  --asset p1-outfit-forester-v1 --asset p1-weapon-short-sword-v1 \
  --direction down --out /tmp/p1-wardrobe
```

删除衣物或武器参数即可分别关闭；选择其他发型／五官只换对应 ID。新资源按同一合同交付 PNG 和清单，再向 catalog 登记；无需改装配器。衣物必须提供九姿势映射，一张任意衣服图不会自动得到动作。

```sh
python3 scripts/export-wardrobe-part.py Art/Parts/P1-v1/outfit-forester
python3 scripts/export-wardrobe-part.py Art/Parts/P1-v1/weapon-short-sword
python3 scripts/package-wardrobe-review.py
python3 scripts/validate-wardrobe-review.py
```

最后一条完整历史保护检查需要完整仓库；下载包可独立运行装配命令、资源检查和 19 项装配器测试。完整历史原图仍以仓库为准。

## 验证与边界

两件实际资源及修正公共底模通过合同检查；216 个输出／横条与实际合成一致。身体八层在所有新组合中不变，部件不互相依赖；九姿势的肩、袖口、腰部和裤靴隐藏重叠均至少跨两行强 alpha 像素。九次实际握点落在原手层和剑柄内，手掌前景遮挡通过。衣物、武器、公共底模共 19 份 ORA 重合成与 PNG 一致，SVG 嵌入图逐像素一致。

100 份冻结工具／标准／原人体／头部文件、732 份此前 PNG／GIF 均不变；正常 GIF 八帧、120 ms、无限循环、帧序与量化后像素通过。完整验证范围及源稿摘要见 validation.json、integration-before.json／after.json 和各包 generation.json。

当前只有一套衣物和一把剑，尚未验证第二种衣物版型或其他持握类型。其他七方向中性人体、八方向换装和正式应用仍待推进；生产入口继续拒绝草案及不完整方向。未执行绘画软件 GUI 往返、原生构建或实体 iPad 测试。本组认可后先做第二套不同版型衣物的替换验证。
