# 后颈连续肤色 v4

用户指出v3修补处色块不均匀。根因是只替换原暗色像素，较亮的补色以离散点落在旧阴影中，形成补丁边界。v3内部美术通过撤回，原文件保留。

v4从原r6源重新处理，将头颈交界作为连续区域取新绘制肤色场；源区域边缘采用2px合成权重过渡。头部区域仍限于与原颈部重叠的范围，颈部排除背心/透明背景。只调整颜色，原alpha、头形、人体/四肢、矩阵和所有动作保持，六件独立外观包继续复用。

source/generated.png由图像工具根据紧凑头颈导板重绘连续暖肤色阴影，按固定64×32全画布登记，左右各32×32片置于原112,112坐标。不是逐帧临时补色，也没有全图模糊。source区域配置见authoring.json，实际源像素范围见审核目录source-repair.json。

两个共同底模r8-nape-gradient独立保存，不覆盖原r6/r7。脚本：export-upper-nape-gradient.py、verify-upper-nape-gradient.py、reexport-upper-nape-gradient.py。新修订待用户评价。
