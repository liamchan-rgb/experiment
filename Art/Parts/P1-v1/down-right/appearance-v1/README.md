# 右下独立外观 v1 · 候选

复用已确认的右下中性r1镜像身体、13姿势及轻微头摆。新增8个独立包：棕发/银发、蓝/琥珀五官、绿短上衣/蓝分叉短外套、共用灰裤低靴、背剑。16搭配×13姿势=208实际合成图。

头部96局部反射且左右语义交换，origin为[84,61]，沿原右下headToCanvas及其源UV栅格校准；五官不包含脸皮，头发不包含脸/耳/头。衣物按左下原matte/姿势逐层反射并交换左右归属；近右肢在屏幕左、远左肢在屏幕右，原身体层相对层序保持。衣袖/裤口及靴子随原肩肘腕、骨盆/髋膝踝足，不压缩拉宽身体。

镜像后的头发/衣物用两张固定全画布imagegen颜色稿校正左上光源，经原源UV固定到表面，不导入生成稿的轮廓、人体、手或五官。source及每包source/original.png/prompt.txt保留，明暗参考限定同材质、距离≤2.5px；原轮廓/未匹配/隐藏位置RGB保留。12个源槽位alpha不变，最亮头发簇位于左侧，近右袖比远左袖更亮。

背剑沿同一物理右肩斜背，独立前视投影[108,122]→[139,179]，随原躯干刚性变换；并非把右肩翻成左肩，也不改成中轴竖背。头/躯干/衣物/腿真实遮挡剑鞘；已修掉部分姿势腿边一两像素闪出的剑尖，历史试稿留在审核目录rejected-probes。

公共装配器/合同代码未改，仅新增profile右下头导板。13空外观原图、1664身体层检查及14876旧文件保持，2496外观alpha反射检查通过。主线程已看8种带剑组合全部13帧整身1×/2×及实际GIF解码8帧；16组合技术检查见审核目录，不把静帧查看称为连续播放验收。新右下外观用户认可为空，无App/设备/IPA。

重现：`python scripts/reexport-down-right-appearance.py`。

[正常全身GIF](../../../../Review/P1/modular-down-right-appearance-v1/outfits-walk-120ms.gif) · [起停](../../../../Review/P1/modular-down-right-appearance-v1/outfits-start-stop-120ms.gif) · [站姿](../../../../Review/P1/modular-down-right-appearance-v1/outfits-idle-2x.png)
