# 上斜后颈修正 v3

原共同底模头部下缘与颈部描边在露出的后颈处叠成硬黑线。新共同底模r7仅修复该交界的颜色，不改变人体形状。原r6及所有v1/v2外观文件保留。

source/保存无发头颈导板、接缝标记与图像工具原稿。authoring.json限定修复源区域：左上x130–140,y123–131，右上x115–125,y123–131；仅原暗色源像素取新绘制颈部颜色。头部修复区还必须与原颈部不透明区域重叠，保留头部外轮廓。原稿只用于颜色，不采纳图像工具重绘的头形。头部源4+4像素、躯干颈部10+9像素，共27枚源像素调整，透明度全部保留。

base-up-left/base-up-right含新的共同底模清单、局部源补丁和逐帧PNG、ORA/SVG。头部96×96源继续使用原headToCanvas；躯干颈部补丁通过原共同shirt UV输出。全部外观统一使用r7，不根据外观ID切换身体。六件衣发裤靴/背剑资源保持原版本，公共装配器不修改。

导出：python scripts/export-upper-nape-repair.py；检查：python scripts/verify-upper-nape-repair.py；重导：python scripts/reexport-upper-nape-repair.py。新修订未获用户美术认可。
