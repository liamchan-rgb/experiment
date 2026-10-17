# 1.6.1（build 26）步态复核

[下载 IPA](../Downloads/README.md) · [正常速度录像](iPad-Gait-Normal-b26.mp4) · [四分之一速度录像](iPad-Gait-Quarter-b26.mp4) · [鞋部朝向和连续样本](Build26-Gait/README.md) · [16 项原生、3 项 iPad UI 检查](Build26-Gait/CloudValidation.json)。

本版保持鞋子原画里的朝向，去掉会把鞋扳歪的通用旋转，仅随踝点平移。云端 UI 测试遍历八个方向和每方向 24 姿势；四分之一速度实景录像覆盖三位人物、全部八方向，每位人物每方向抽样 12 次。正常速度录像因捕获启动晚于方向计时器，缺少“上”方向，完整方向对照请看慢速录像。云端为 iPad Pro 13-inch（M4）模拟器、iOS 18.5；未测试物理 M1 iPad／iPadOS 27.2，也未运行 iPhone 测试。

可换装开源角色系统调研见[骨骼方案评估](../docs/CHARACTER_RIG_EVALUATION.md)。其他版本资料保留在各自目录。
