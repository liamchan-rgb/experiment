> 用户再次指出右臂有问题；v2 仅补袖片未修正肩肘结构，已撤回内部放行。后续返修见 [v3](../hunting-bow-followthrough-r7-v3/README.md)，待复审。

# r7 后续动作 v2 · 右侧拉弦臂肩部/大臂显露返修

用户指出 v1 放下右臂时大臂和肩膀缺失。原因是近侧大臂一直放在躯干后面；源层虽然存在并与前臂重叠，最终合成仍被衣身遮掉。v1 的图层重叠检查不足以证明肩部在最终画面可见。

本轮补齐近侧肩头至肘部的独立前景袖片 nearShoulderUpper，放在 torso 后、nearForeArm 前；原后侧袖片仍保留在躯干后。满弓时新袖片被原前臂自然遮住，因此首个原生合成仍与 r7 完全相同。收手时新袖片随着同一个肩肘关节显露，无图层突切或透明度淡入。

- shoulder-upper-source.json：补齐的原生袖片几何与肩/肘连接点。
- frames/000..084：每帧完整 pose.json、nearUpperArm.png、nearShoulderUpper.png、nearForeArm.png、farArm.png 与透明 assembled.png。
- 其他共享衣身/手形/头部资源及弓/箭几何沿用 v1。
- 动作轨迹、所有关节姿势和弓/箭位置逐帧对比与 v1 完全一致；没有借修遮挡改变手形、臂长或时序。

复现：`python scripts/author-bow-followthrough-r7-v2.py`。85 个 20ms 原生采样帧，共 1.70 秒含停留；正常 GIF 单次播放，实际解码画面 43 个。

主线程检查整身及全部实际 GIF 解码联系页。除了肘/腕的源层相接，还检查收手后最终画面确实显示肩部袖片、肩到肘的袖身路径不断；记录见审核目录 validation.json。新动作待用户复审，未接 demo、打 IPA、图像生成或运行 App/模拟器/实机，不委派智能体。
