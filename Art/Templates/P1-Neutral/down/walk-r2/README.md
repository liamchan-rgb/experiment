# 共同中性底模 walk-r2 · 仅修正图层归属

长裤试穿时发现 walk-r1 第 7 帧的前景右腿层夹带后腿小段。将 48 个有 alpha 的像素归回左腿层，右脚仍在前景，姿势／关节／身体外形不变。

九张 frames PNG 与已认可 walk-r1 字节完全相同；用新八层实际重合成后逐像素相等。仅 `layers/07/body.leg.right.png`、`body.leg.left.png` 两层改变，其余 70 层逐字节一致。原包及其认可文件均保留；本记录不冒充新的用户美术认可。

此包作为本轮所有 24 种新搭配唯一公共底模，包括无衣物／无武器组合。没有按外观切换身体。新资源装配清单 ID 为 `p1-neutral-down-walk-r2`，动作只更新公共底模摘要，所有姿势字段保持原样。

[修正区域与验证](correction.json) · [实际衣物回审](../../../P1-Wardrobe/down/v1/README.md) · [原人体认可](../walk-r1/approval.json)

可在仓库根目录复现：`python3 scripts/repair-neutral-layer-ownership.py`。该脚本只做技术图层归属与可编辑文件导出，不生成或重画美术。
