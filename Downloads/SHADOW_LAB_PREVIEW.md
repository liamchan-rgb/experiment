# 三维阴影试验包

[下载 1.4.1 build 12 IPA](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b12.ipa)。

下载后保存到「文件 → 我的 iPad」，再在 SideStore 点「＋」选择新文件 MeadowJourney-b12.ipa。可覆盖安装。安装后点地图左上角「光影试验」。

本轮默认「轮廓投影」：使用素材透明轮廓裁切投影网格，树冠、塔楼与人物分别配置少量纵深，人物使用当前动画帧。底部可切换「轮廓投影／简模投影」作对照；「模型显示」显示对应网格。光向、投影开关、暂停、缩放和重新布局仍可使用。原地图尚未全量切换。

按用户要求，本轮不检查图片效果、不录制验收视频、不运行视觉像素对比；效果由用户安装后反馈。设备 Release 归档和 IPA CRC、arm64、Metal 资源及可执行权限校验已通过，基础 Metal 命令执行检查也已通过（1 项测试，0 失败，涵盖新旧模式及模型显示）。

包使用与已安装 build 11 相同的经典 ZIP_STORED 格式，无扩展字段。来源、大小与 SHA-256 见 [ShadowLab-build12.json](ShadowLab-build12.json)，[构建记录](https://github.com/liamchan-rgb/experiment/actions/runs/38764253674)。
