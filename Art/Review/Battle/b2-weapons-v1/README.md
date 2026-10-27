# B2 武器专属战斗演出候选

本批是固定战斗场景的离线美术预览，不读取 GameCore、不结算伤害、不代表装备已进入 demo。用户上轮认可的符文甲侧向袖腕范围另记于 `Art/Review/Equipment/b2-batch-v5/user-approval-profile.json`；不扩大为两甲整体通过。

- **重剑**：连续关节预备、短跳贴近、剑尖带动挥击与金色命中、怪物受击、粒子落地、短跳回位。自行拦下过挡脸的起手与滑步初稿；现有动作在靠近和回位时补足腿部过渡。
- **传奇权杖**：杖头发出青蓝光弹，飞向目标身体，命中发亮并留下短暂的地面粒子；场景压暗与局部照明随动作变化。

两段各 2.4 秒，GIF 以 20 ms 时间步采样，静止图像编码可合帧，正常速度循环；MP4 为 800×480、H.264、60 fps、144 帧。60 fps 仅指离线视频，不说明设备帧率。鹿灵为现有演示目标，不宣称正式怪物素材完成。两段用户认可均为空。

本人查看 GIF 实际解码后重剑 103 帧、权杖 115 帧的整场和完整人物联系页，及每段视频每 5 帧抽样的 29 帧；这不是连续播放或实机体验验收。初稿的命中光落在轮廓外，调整剑尖和投射终点后，命中点位于怪物可见像素内。`geometry.json` 额外逐个检查两段各 144 个 60 Hz 样本的人物/怪物实体重叠、武器/脸部重叠；几何检查不能取代审美判断。

源关键帧为 `Art/Scenes/MeadowBattle/b2-weapon-actions-v1/action-poses.json`，可执行 `python3 scripts/review-b2-weapons-actions.py --media` 生成预览，`python3 scripts/verify-b2-weapons-actions.py` 检查指定几何关系；依赖 Pillow、NumPy、SciPy、ffmpeg，GIF 优化依赖可选的 gifsicle。环境参考用户录屏的既有文字分析 `Art/Scenes/MeadowBattle/skill-flow-v1/reference-notes.md`，没有上传或复制录屏。

审核页使用两个独立条目，旧四件已认可资源保留、两甲其余范围待审；浏览器结果可导出，不会自动写回 GitHub。未修改原战斗运行逻辑，未执行 App、模拟器、实机，未制作 IPA。
