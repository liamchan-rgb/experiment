# 技能精灵表像素重构 v1

左 = 旧表(交叉淡入+平滑缩放)，右 = 新表(逐帧保持+最近邻)，均按规格 fps 实速播放，叠加混合。
来源: `scripts/battle-vfx/`(`python3 build.py --assets` 直接写入 Assets.xcassets，帧数/fps/单元尺寸/锚点全部不变)。
五张: starlightPulse, rally, sweep, dragonSoulWard, dragonScaleWard。
