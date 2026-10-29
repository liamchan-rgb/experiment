# Build63 上臂衣片返修

[正常全身对比](armors-body-normal.gif) · [站姿](armors-standing.png) · [皮甲四武器](leatherArmor-attack-normal.gif) · [符文甲四武器](runeArmor-attack-normal.gif) · [皮甲其他状态](leatherArmor-states-normal.gif) · [符文甲其他状态](runeArmor-states-normal.gif) · [场景](battle-normal.gif)

用户指出Build62皮甲右大臂与臂甲错位、符文甲上臂蓝布残角，撤回对应内部美术放行，旧稿保留。根因是旧衣片横向偏离补齐后皮肤的肩肘骨轴，分层切线只截断前臂，未清除上臂外侧旧残片。主线程把两件原上臂材质贴合固定肩(117,141)→肘(128,158)，皮甲单独收齐短袖口、清除重复旧亮边，符文甲裁掉伸出臂形的蓝布角。仅两张上臂衣片像素变化，其他22个映射护甲／猎弓图、manifest、运行时层序和骨架、三武器Rig与JSON逐字节保持。原手型／握点／头脸／前臂／下摆／护肩／行走／玩法不改。

主线程查看六状态全身1×/2×、三通用武器全部462正常GIF实际解码帧和四武器板，权杖首尾整人RGBA相同。纯资产回归见source-audit.json，不能以数值替代美术检查。Intel设备Release 40826021957成功，132纯测试／五旧检查／九组跨平台导出及包校验通过；八媒体完整公开GET与独立GIF浏览器推进已核。直接IPA完整GET回执见Media/Build63。新美术认可null，无App／模拟器／实机，无智能体或整人图像生成。

recovery-candidate.py是中断时尚未看图的旧试稿备份，不能代替当前scripts/repair-armor-fit-r2.py或标为用户认可。后两项仍为饰品槽及属性反馈、B2背包装备界面与存档；本轮只返修。
