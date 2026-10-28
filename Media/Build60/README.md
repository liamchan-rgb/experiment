# Build60 · 1.6.34 权杖首帧遮挡修正

[直接IPA](../../Downloads/MeadowJourney-b60.ipa) · [正常整身/战斗/首帧对照/站姿](../../Art/Review/Battle/legendary-staff-layering-r1/README.md) · [包校验](package.json)

用户指出Build59首帧法杖与腿错位，主线程确认并撤回该待机画面的内部放行。修正idle的武器后置层序，待机、起手、收势共用manifest层序，杖杆在腿前、手在杖前，阴影与离线渲染同用；同时统一关节补底显隐，消除髋部8像素闪动。待机/attack0/attack1整人RGBA一致，关节曲线/时序/图案/玩法保持。

主线程亲审两只正常GIF全部380实际解码画面20页、首帧原尺寸/放大全身及六状态30姿势1×/2×，前后对照左侧来自已经交付的Build59像素。离线合成不是UIKit/设备录屏，地图光照近似；新美术待用户反馈。没有App/模拟器/实机运行，没有智能体或整人图片生成。

源 `9ab46b21e0980d20f81021eb2c50c3f3dc62f00f`，Intel设备Release [40721530191](https://github.com/liamchan-rgb/experiment/actions/runs/40721530191)成功。128纯测试/五旧检查通过，Mac/Linux九组导出一致，新共用层序JSON包内逐字节匹配；版本、经典ZIP2.0/CRC/权限/架构/Metal/图集/当前步态和原目录均已核。IPA 38,263,628字节，SHA256 `c9719a152b96c9b64231542b16a6fb1c2b24305d6d2b0f8d35467299d57c938d`。公开完整GET回执见public-downloads.json。

后两项仍为皮甲/符文甲装备与战斗挂载；力量徽章/行动戒指装备槽与属性反馈。
