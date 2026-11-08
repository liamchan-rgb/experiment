# 上斜独立外观 v1 · 腿部待修

2026-10-24主线程重新检查确认裤靴比例/透视与腿部动作读法有问题，撤回原内部美术通过；见[具体复查](leg-reinspection-2026-10-24.md)。以下GIF为原问题版本，无新美术修订。

同一已认可r6底模上，左右上斜各提供绿色短上衣、蓝色分叉外套、共用裤靴、棕发、银发与独立背剑。六个资源包可交叉搭配；全部13姿势包含站立、八步态、两起步、两停步。

- [正常行走GIF](outfits-walk-120ms.gif)：上排绿衣棕发，下排蓝衣银发；左列左上、右列右上；8×120ms。
- [正常起停GIF](outfits-start-stop-120ms.gif)：22帧，首末480ms、其余120ms。
- [整身站姿](outfits-idle-2x.png)、[交叉搭配](cross-combinations-2x.png)。
- [主线程具体修复/检查](art-review.md)、[全组合技术记录](validation.json)、[重导记录](reexport-validation.json)。

各方向/衣型目录包含全部13帧与1×/2×整身联系表。combinations/保存16种组合的208张实际装配结果。rejected-first-assembly/保留内部判退首稿，不作为最终预览。

主线程亲自修复与逐帧检查，未使用智能体；当前查看器不能连续播放，未声称播放器验收。新外观未获用户认可，未接入App或打包IPA。

## 已验证浏览器直链

- [outfits-walk-120ms.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/719789d83e61466fafd19cdb9c01294001235807/Art/Review/P1/modular-upper-wardrobe-v1/outfits-walk-120ms.gif)
- [outfits-start-stop-120ms.gif](https://raw.githubusercontent.com/liamchan-rgb/experiment/719789d83e61466fafd19cdb9c01294001235807/Art/Review/P1/modular-upper-wardrobe-v1/outfits-start-stop-120ms.gif)
- [outfits-idle-2x.png](https://raw.githubusercontent.com/liamchan-rgb/experiment/719789d83e61466fafd19cdb9c01294001235807/Art/Review/P1/modular-upper-wardrobe-v1/outfits-idle-2x.png)

三份文件HTTP200、MIME及哈希与本地一致，GIF时序与循环标志一致，见delivery.json。美术提交 `719789d83e61466fafd19cdb9c01294001235807`。
