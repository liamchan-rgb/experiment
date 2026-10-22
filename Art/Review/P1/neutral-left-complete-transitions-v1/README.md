# P1 向左底模 · 隐藏连接与起停过渡审核

[起步—行走—停步正常速动图](start-stop-120ms.gif) · [已认可循环对照](walk-120ms.gif) · [四张新增全身姿势](transition-poses-fullbody-1x.png) · [站姿](idle-review-2x.png)。每张动作120ms，起停展示首末站姿各480ms，没有慢动作版本。

本轮保留 r2 九姿势可见画面及头部摆动，增加隐藏肩髋/腕口连接和两起步、两停步关键姿势。新稿等待用户美术审核；r2 的认可只代表此前展示的外观与循环。

起步只覆盖 idle00 接 walk01，停步只覆盖 walk08 收回 idle00；其他步相的即时中断仍需单独处理。独立衣物/头部外观与运行接入不在本轮完成范围。

技术复核见 [transition-checks.json](transition-checks.json)，全身与分层美术检查见 [art-review.md](art-review.md)。[核对脚本](verify.py)会实际调用公共compositor、对照九张认可画面、检查头部局部挂载/头颈连通/脚底/ORA和重导一致性；这些不能替代用户美术认可。
