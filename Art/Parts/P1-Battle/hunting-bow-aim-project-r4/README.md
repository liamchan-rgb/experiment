# 猎弓第一关键帧 r4 · 恢复原外套的衣料与结构

用户要求按既有模组修复衣物，继续保持手/手臂不变。本轮基于原战斗外套的布料像素、衣领、包边、衣摆和腰带细节重建躯干；补画旧持剑袖子遮住的窄门襟，调整衣身松量，避免大色块和过度收尖的轮廓。

原生资源维持 256×256 分层。torso.png / pose.json 是本轮衣身；drawing-hand.png、grip-hand.png、farArm.png、nearUpperArm.png、nearForeArm.png 及所有关节位置逐字节沿用 r3。source/hash 和冻结范围在 authoring.json；实际合成顺序与项目来源在 assembly.json。

复现：先执行 `python scripts/author-bow-jacket-r4.py` 重建衣身资源，再执行 `python scripts/review-bow-aim-project-r4.py` 导出透明 assembled.png 及整身预览。素材来源是原项目 PNG，不使用图像生成。

仅一张静态关键帧候选，未迁移运行时连续动画，待用户审核；无新动作、IPA、App/模拟器/实机运行，不委派智能体。
