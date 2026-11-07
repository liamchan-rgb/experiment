# 制作流程：母版绘图与程序导出分工

两件甲分别选型、分别登记。Chat只执行C段；I段是项目Codex接收母版后的工作。**没有任何一步要求Chat手绘104个挂载姿势。**

| 步骤 | 执行者 | 做什么 | 必交产物与进入下一步的条件 |
| --- | --- | --- | --- |
| C0 读参考 | Chat | 打开五视角人体/关节、实际四层示例和技术复用图 | 实际已读文件与能力说明；不能读ZIP或输出真实分层时说明限制 |
| C1 选设计 | Chat、用户 | 每件A/B/C各正面/左下，保持同一人物 | 每件6张概念合成、结构差异说明；用户分别选择，选择不等于全部动画认可 |
| C2 正面母版样板 | Chat | 先衣身、左右袖甲，再前裙甲；仅front/idle0 | 4张256RGBA、真实可编辑源、完整人物1×/2×；修好服帖、肩腋腕、腰裙，不画动作 |
| C3 五视角母版 | Chat | 沿选定设计补左下、正左、左上、正背；front沿用C2 | 5×4＝20层母版与五视角整身；衣长/甲片/主题一致，侧背投影成立 |
| C4 母版交接 | Chat | 整理素材、色板、提示词、源稿与清单 | 20母版、master-manifest、palette、真实分层源与缺项记录；到此交回Codex，不填104帧运行清单 |
| I1 注册与模组适配 | Codex | 复用原关节/表面映射，登记新裁片与控制点；派生另三向，校正语义/光照 | 身体/动作/原资源不变；不对称或光照不能自动满足时，只请求/修必要右向母版 |
| I2 少量试导出 | Codex | 用程序出正下idle+8walk，检查肩甲/袖腕/胸腹/衣摆 | 9绑定、36层引用和正常8×120ms GIF，来自母版映射，不是Chat另画36张 |
| I3 批量导出与审核 | Codex | 批量出八向13姿势，完整组合、正常GIF、边缘与起停检查 | 单件104绑定/416引用、8向walk/起停；Codex先修明显问题，再交用户 |

## 每个母版视角的四部件步骤

1. 衣身：按本视角原颈根—胸腹—腰线画选定版型，定领口、胸侧、腰带；不要为了衣服重画身体。领口允许正常露颈，不能封死脖子。
2. 自身左袖：读shoulderLeft→elbowLeft→wristLeft，定肩口、肩甲、袖子、袖口。肩甲随这条臂链，不并入固定胸甲。原手不能画到袖子里。
3. 自身右袖：独立读右侧链条，不把屏幕左侧当成角色左；检查近远投影和隐藏接合。与左袖同设计但不是简单改名。
4. 前裙甲：上缘藏在腰带后，独立画腰裙衣片，不包含裤腰/裤腿；分片应为后续髋腿适配留活动结构。无该部件时才可说明原因并绑定透明母版。

这些是**五套静态母版**的步骤，动作随动由既有模组驱动。Chat不用逐帧重新标挂点，不用再画手、裤靴或步态。

## 常见问题怎样修

- 同方向多帧肩缝/袖口都出问题：Codex优先修母版接合、裁片或共用映射，再重导相关帧。
- 三个右向的装饰/光照不成立：补必要右向静态母版，或由Codex精修该方向；不要求Chat扩成104次手绘。
- 极少数姿势特例：允许Codex做有记录的局部帧修正，写进可重导的覆盖数据，不能下一次导出又丢失。
- 新甲需要披风/尾巴/新槽位：列为合同扩展；当前任务不偷偷改原身体/动作层序来迁就。

## 交接目录示例（Chat负责的部分）

```text
starlightArmor/                 # dragonArmor同结构
  master-manifest.json          # 5视角×4层，不是引擎asset.json
  masters/front/outfit.torso.png
  masters/front/outfit.sleeve.left.png
  masters/front/outfit.sleeve.right.png
  masters/front/outfit.hem.front.png
  masters/front-quarter-left/...
  masters/profile-left/...
  masters/rear-quarter-left/...
  masters/back/...
  editable/front.ora            # 每视角真实四层；或一个五组分层源
  editable/...
  source/palette.json
  source/prompts.txt
  source/originals/...
  review/five-view-1x.png
  review/five-view-2x.png
  handoff.json                  # stage=C4，未声称104姿势已经完成
```

交回以后，Codex才在新的运行资源目录生成asset.json及png/<direction>/<clip>/<frame>/…，保留原母版和全部输入摘要。不要把integration目录的832行输出计划当作绘图清单。
