# 六种怪物 · 正常速度美术检视 v1

本轮资源/注册/动作均为候选，用户认可null。[正常GIF](bestiary-normal.gif) · [MP4](bestiary-normal.mp4) · [受击注册整场](incoming-registration.jpg) · [三敌站位](three-enemy-formation.png)。

GIF为六种同屏批量概览，正常6.4秒，无慢动作；同一Swift MonsterVisualSpec/PartyVisual导出每种320×20ms样本，静止重复帧在GIF中合并延长，不加速。浏览器独立GIF已确认可解码并推进；不运行游戏/App/模拟器/实机。影片是离线合成，非UIKit录屏；环境光影/UI近似，未叠加正式战斗全部照明/粒子反馈。角色原图/武器骨架未重画，32个原画参考输入逐字节与上轮发布树相符。

阶段：待机→短出招/回位→受击→施法姿态→向右吹散退场。普通攻击/施法仅表面形变，不是完整四肢骨骼行走；弓手和魔龙的远程投射从实际弓/口部出发，其他近身按前缘接触。死亡各自独立剪影、40帧、首帧原身体/末帧透明，不套鹿身体。血条在死亡开始时消失。

主线程查看24张全身接触表覆盖336常规源姿态、六张2×关键姿态、整场各阶段与接敌图；全部240死亡源帧/完整GIF解码作技术检查。六个受击点都在原画不透明身体上；近战新增脚底约束，维持原地面关系，不把主角抬到首领胸口。原攻击模组到命中点的相对关系仍保留。这里不声称每个GIF帧全分辨率人工连续播放验收，也不声称设备60fps实测。

IPA中的检视入口：开始新行程设置→怪物动作检视。该界面只看外观，不关联行程资源；正式战斗在编辑地点选择六种已登记怪物时使用对应资源，普通最多3只、首领1只。默认地图随机投放仍旧鹿灵/鹿王，下轮再接随机遭遇组合。原鹿资源保留。

重导：先 swift run --package-path Vendor/ClassroomGameCore MeadowSupportReviewExport 本目录/data --monster-only；再 python3 scripts/review-monsters.py 本目录/data/monster-frames.json。需Pillow/NumPy/SciPy（重建源图集）及ffmpeg。源母版与动作重建见Art/Monsters/bestiary-v1。浏览器检查仅针对独立GIF。
