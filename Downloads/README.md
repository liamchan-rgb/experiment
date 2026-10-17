# SideStore 安装与迭代包

[最新迭代包：1.5.9 build 22，栅栏接地校准与左上角放射光束](MeadowJourney-build22.json)。沿用用户已确认能打开地图的 build 21 单视图组合结构，本轮视觉效果待用户反馈。

直接下载：[MeadowJourney-b22.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b22.ipa)。在 Safari 下载后保存到「文件」，再打开 SideStore → My Apps → ＋，选择 MeadowJourney-b22.ipa 重签安装。安装名 MeadowJourney，包标识 com.liamchan.experiment.meadow，支持 iPadOS 15 及以上，可覆盖已有安装。

测试前从后台完全关闭 MeadowJourney，再打开。应用自动运行 A／B 分通道检查、C00 连续 60 帧组合检查，再进入 C02 实际单视图地图；失败时点“复制诊断”，将文字粘贴到对话。若卡死或被系统退出，下次打开会先显示同版本保留的记录，先复制再重新诊断；升级前的记录另存，避免把 build 20 错误当作本轮结果。[详细取证说明与证据边界](../docs/GPU_DIAGNOSTICS.md)。

[来源与校验值](MeadowJourney-build22.json) · [迭代日志](../docs/ITERATION_STATUS.md)。build 22 的 Release 编译归档和 IPA 完整性检查通过；云端只打包，模拟器及测试任务已跳过。60 帧检查在应用内执行，本轮尚未得到 build 22 的物理 iPad 运行结果。SHA256SUMS 保存历次包的校验值。

历史版本：[build 21](MeadowJourney-build21.json) · [build 20](MeadowJourney-build20.json) · [build 19](MeadowJourney-build19.json) · [build 18](MeadowJourney-build18.json) · [build 17](MeadowJourney-build17.json) · [build 16](MeadowJourney-build16.json) · [build 15](MeadowJourney-build15.json)。用户已确认 build 21 可在此前报错的 M1 iPad Pro 进入地图，尚无长时间帧率／发热量测。通用 MeadowJourney-unsigned.ipa 暂保留 build 9，当前请使用上面的 build 22 专用文件。
