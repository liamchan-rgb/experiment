# up-left r6 · 指定起停路径

同一中性身体，保留r5认可的idle00/walk01–08，新增walk-start01/02、walk-stop01/02。13姿势按存储序号00–12输出；公共合同中的frame为各clip内序号，不能把存储09误当walk-start帧9。

身体/短裤连接域与近远层级沿用r5；左上用authoring.json中的transitionPoses记录关节幅度、足部抬升与支撑顺序，右上用mirror-authoring.json指向左上候选并交换左右语义、关节、脚底/支撑及头部局部矩阵，继续使用固定光照源UV。没有换身体或运行时外观ID分支。

新过渡没有继承r5的美术认可；只覆盖idle00接walk01和walk08回idle00。完整隐藏人体和独立外观另行验证。审核与动图：`Art/Review/P1/neutral-upper-transitions-r6/`。复现用仓库根目录的`python scripts/reexport-upper-transitions.py`。
