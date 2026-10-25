# build45 / 1.6.19 — 统一60帧目标

战斗display-link显式minimum/maximum/preferred=60；地图MTKView与步态SKView明确60。动态环境背景跟随每次提交的scene时间样本，不再将静止地图的光影/雾更新限制在30Hz；无环境的静态步态底图保持缓存。位置、动作步相与光影按时间/距离推进，速度和原资源不变。

这是一项运行时帧率配置修订，不代表实机已经稳定60fps。不运行App/模拟器/实机，用户测试实际帧率。地图长按左上“安然”可显示实际更新FPS；战斗实际display-link间隔与更新CPU写Documents/BattleFrameTiming.json，build从Bundle读取，非GPU计时。沿用原战斗美术，不将50fps离线GIF称为实机60fps录像。

沿build44-r1经典ZIP2.0无压缩打包；先前SideStore读取错误未确认根因或重试安装结果。旧包保持。纯Swift、设备Release和包/下载核验待完成。
