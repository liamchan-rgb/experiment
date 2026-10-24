# 上斜独立外观 v2 · 裤靴重做候选

用户指出v1腿部异常后，由主线程独自重做裤靴并审核。原问题版保留，内部美术通过已撤回；v2没有继承认可。

- [正常行走GIF](outfits-walk-120ms.gif)：8帧×120ms。上排绿衣棕发，下排蓝衣银发；左列左上、右列右上。
- [正常起停GIF](outfits-start-stop-120ms.gif)：22帧，首末480ms，其余120ms。
- [整身站姿](outfits-idle-2x.png)、[交叉发色](cross-combinations-2x.png)。
- [主线程具体修复与检查](art-review.md)、[全部组合检查](validation.json)、[源轮廓/颜色检查](source-audit.json)、[重导证据](reexport-validation.json)、[47项回归](regression.json)。

两个方向两衣型各13姿势的整身1×/2×图在对应目录，combinations/保留16组合208张实际装配结果。查看器只能逐帧，未声称实际观看连续播放器。当前为新外观候选，artApproval=null；无App/实机/IPA范围。

## 已验证浏览器直链

- [outfits-walk-120ms.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/04ce1ac1ef23f06fe34c96c3c63ef5ce770c3418/Art/Review/P1/modular-upper-wardrobe-v2/outfits-walk-120ms.gif)
- [outfits-start-stop-120ms.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/04ce1ac1ef23f06fe34c96c3c63ef5ce770c3418/Art/Review/P1/modular-upper-wardrobe-v2/outfits-start-stop-120ms.gif)
- [outfits-idle-2x.png](https://raw.githubusercontent.com/liamchan-rgb/experiment/04ce1ac1ef23f06fe34c96c3c63ef5ce770c3418/Art/Review/P1/modular-upper-wardrobe-v2/outfits-idle-2x.png)

三份文件HTTP200、MIME及哈希与本地一致，GIF时序与循环标志一致，见delivery.json。美术提交 `04ce1ac1ef23f06fe34c96c3c63ef5ce770c3418`。
