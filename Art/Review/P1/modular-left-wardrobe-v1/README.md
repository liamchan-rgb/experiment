# 向左独立外观 v1 · 内部复核后提交

当前只审核向左这一方向。两套衣型使用同一身体、步态、三发型/两五官、共用裤靴和背剑；用户对新增外观的认可为空。

[正常行走动图](outfits-comparison-120ms.gif) · [正常起停动图](start-stop-comparison-120ms.gif) · [两套站姿](outfits-comparison-2x.png) · [六组头部全身](head-combinations-fullbody-1x.png) · [13姿势](thirteen-poses-fullbody-1x.png)

动图由实际公共compositor输出：行走8×120ms；起停22帧，首末idle各480ms，其余20帧120ms。起停只演示idle00→walk01及walk08→idle00的作者路径。

[完整美术复核](art-review.md)、[全部组合/贡献](audit.json)、[清单/重导/时间核对](checks.json)、[来源与范围](../../../Templates/P1-Wardrobe/left/v1-independent/README.md)。`render-audit.py`复现全部72组合/936图；`verify.py`另检查10清单、264导出文件两轮一致与四个GIF帧时长。没有运行App、模拟器、设备或制作IPA。

浏览器HTTPS直链与响应/哈希核对在发布后记入delivery.json。
