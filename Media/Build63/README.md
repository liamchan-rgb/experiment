# Build63 · 1.6.37 上臂衣片返修

[直接IPA](../../Downloads/MeadowJourney-b63.ipa) · [正常全身动图／站姿](../../Art/Review/Battle/armor-fit-r2/README.md) · [包校验](package.json)

撤回Build62上臂衣片相关内部美术通过，旧稿保留。皮甲旧袖子横向偏离完整大臂，符文甲上臂衣片尾部留有蓝布残角；主线程将原材质重新贴合固定肩(117,141)→肘(128,158)，皮甲单独收齐短袖口并清除重复亮边，符文甲收齐超出真实臂形的蓝布。只替换两张ArmNearUpperWardrobe。22个其他护甲映射／猎弓图、hero-gait与运行时层序／骨架、三武器Rig/JSON逐字节保持，原双手／握点／头脸／前臂／护肩／下摆／步态／玩法不改。

主线程亲审六状态整身1×/2×、三通用武器全部462实际GIF解码帧和四武器板；权杖idle/attack0/attack1整人RGBA相同。主GIF选抬臂更充分的短剑，固定全程调色板避免二次编码闪色，时长保持3800ms。8个公开媒体完整GET逐字节匹配，独立GIF浏览器推进已核。没有App／模拟器／实机运行，没有智能体／整人图像生成，新美术用户认可null。

Intel设备Release [40826021957](https://github.com/liamchan-rgb/experiment/actions/runs/40826021957)成功，实际编译源 `07dd70c85a307ee94c9f682f1c5b3e5ae1571a48`。132纯测试／五旧检查与九组Mac/Linux数据导出一致；全部66护甲资源名已编入，包内原武器JSON／当前步态／原目录逐字节匹配；版本／arm64与iPhoneOS／权限／Metal／经典ZIP2.0／CRC已核。IPA 48,938,928字节，SHA256 `1926d4db68de0748dd111ebf37b047631396785045d53eb19c297b4684717fec`。直接IPA完整公开GET回执另记public-downloads.json。

后两项：力量徽章／行动戒指装备槽与属性反馈；B2背包装备界面及存档。本轮只返修，不自动开始。实机由用户测试。
