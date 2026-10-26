# build53 猎弓候选美术审核

地图P1菜单→武器→猎弓；林地战斗→小队支援，P2先行动，结束P2回合后操作P1。小队普通攻击使用原目录1D8/射程1，强击仍为1D6+2，1AP/每场2次。营地受控借一把弓，无经济/目录改动；原.equip处理库存，禁止战斗换装，重开保持选中装备。

[射击整场](bow-normal.gif) / [强击远射](bow-heavy-normal.gif) / [击杀](bow-lethal-normal.gif) / [正常整身持弓](bow-body-normal.gif) / [站姿](bow-standing.png)。前三段各190帧20ms，整身190帧20ms，3.8秒。八向行走与起停见[人物审核](../../P1/hunting-bow-v1/README.md)。根线程查看21页570整场解码帧、7页190整身解码帧、30六动作关键姿势1×/2×和6整场样本1×/2×；检查不是连续播放或设备验收。新美术认可null。

原身体/五官/腿部动作不重画，弓臂复用刚性臂骨和原袖/手纹理；独立弓、弦、箭，原地架弓→拉弦→释放→手部跟随→收势；同一1.048秒命中提交一次真实GameCore结果，骰子确认连续0.32秒转正不重掷。初稿发现后腕超长、弓上端遮脸、固定后袖/旧手/腿部误归属袖口残像，均由根线程亲自返修。仅在新BodyCore/WardrobeCore/FarThighWardrobe副本退休固定旧臂像素，旧原文件保持。抽离采样器导入和Dictionary.values两次编译问题见迭代日志。

来源：生产Swift输出dice-frames/bow-poses，生产光场dice-light-samples，与原规则实际回执；离线Pillow合成，字体/混合/地图/光影/UI近似，不是UIKit或实机录屏，不证明设备60FPS。没有App/模拟器/实机运行。击杀夹具目标3HP，默认敌人仍18HP；旧单人保持固定5伤简化演练，不宣称已迁移正式规则。完整背包/装备/存档UI、其余6基础装备仍待做。

复现：Swift Package MeadowSupportReviewExport→本目录；review-hunting-bow-demo.py --prepare；export-smooth-status-review.swift生成字段；review-hunting-bow-demo.py与--stills。新部件导出命令scripts/import-hunting-bow-demo.py。详情见review.json/preservation.json，归档与包验收Media/Build53。
