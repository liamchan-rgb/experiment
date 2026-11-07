# 上斜外观 v3 · 后颈黑线修正候选

用户指出此版后颈色块不均匀，主线程撤回内部美术通过，资源保留。新修订见[后颈v4](../modular-upper-wardrobe-v4/README.md)。

用户指出v2后颈有黑线，主线程独自修复并审核。原v2对该处漏检的内部美术通过撤回；v3不继承用户认可。

- [正常行走GIF](outfits-walk-120ms.gif)：8×120ms，上排绿衣棕发、下排蓝衣银发，左列左上、右列右上。
- [起停GIF](outfits-start-stop-120ms.gif)：22帧，首末480ms，其余120ms。
- [整身站姿](outfits-idle-2x.png)、[交叉发色](cross-combinations-2x.png)。
- [主线程具体复核](art-review.md)、[源修复范围](source-repair.json)、[组合检查](validation.json)、[重导记录](reexport-validation.json)、[47项回归](regression.json)。

各方向/衣型目录有13姿势原帧及1×/2×整身表，combinations/有16组合208张装配；nape-before-after-sequence.png是辅助定位的局部序列，不代替整身复核或GIF。查看器不能连续播放，不宣称连续播放器验收。artApproval=null；无App/实机/IPA工作。

## 已验证浏览器直链

- [outfits-walk-120ms.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/eededb5c11a548cf9f0aad856782ba8e2b8b9b08/Art/Review/P1/modular-upper-wardrobe-v3/outfits-walk-120ms.gif)
- [outfits-start-stop-120ms.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/eededb5c11a548cf9f0aad856782ba8e2b8b9b08/Art/Review/P1/modular-upper-wardrobe-v3/outfits-start-stop-120ms.gif)
- [outfits-idle-2x.png](https://raw.githubusercontent.com/liamchan-rgb/experiment/eededb5c11a548cf9f0aad856782ba8e2b8b9b08/Art/Review/P1/modular-upper-wardrobe-v3/outfits-idle-2x.png)

三份文件HTTP200、MIME及哈希与本地一致，GIF时序与循环标志一致，见delivery.json。美术提交 `eededb5c11a548cf9f0aad856782ba8e2b8b9b08`。
