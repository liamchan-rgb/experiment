# 左下中性动作模组 r1 · 当前候选

[正常行走GIF](walk-120ms.gif) · [正常起停GIF](start-stop-120ms.gif) · [全身站姿](idle-review-2x.png) · [全部13姿势1×](all-poses-fullbody-1x.png) · [全部13姿势2×](all-poses-fullbody-2x.png) · [具体美术复核](art-review.md) · [技术检查](validation.json) · [重导一致性](reexport-validation.json)

本轮用户要求“Ok开始左下方动作模组的制作”。先建立左下中性分层底模和动作；不继承旧整张人物步态或上斜的美术认可。修复、登记、逐帧检查均由主线程完成，没有使用智能体。

行走01–08每帧120ms，循环960ms。起停22帧：首尾站姿480ms，其余20帧120ms；包括两帧起步、两个行走循环及两帧收步。所有预览都为正常速度，没有新增慢速版本。最终HTTPS和校验回执见delivery.json（发布后写入）。

逐侧追踪肩—肘—腕和髋—膝—踝—足，全部13姿势使用公共装配器，源图/当前帧RGBA一致。原中性、上斜换装及旧左下等6052份文件保持。源稿和分层文件在`Art/Templates/P1-Neutral/down-left/walk-r1/`。当前仅底模动作，独立五官/发型/衣物/背剑尚未制作或验证。查看工具只能展示静帧，已查完整帧序和GIF时序，不声称连续播放器验收；无App、模拟器、实机或IPA工作。
