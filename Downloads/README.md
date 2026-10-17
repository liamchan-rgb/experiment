# SideStore 安装与迭代包

[最新修正包：1.5.8 build 21，单视图合成与连续帧诊断](MeadowJourney-build21.json)。此包根据 build 20 的 M1 实机证据调整渲染提交，尚待用户确认 GPU 超时是否消除。

直接下载：[MeadowJourney-b21.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b21.ipa)。在 Safari 下载后保存到「文件」，再打开 SideStore → My Apps → ＋，选择 MeadowJourney-b21.ipa 重签安装。安装名 MeadowJourney，包标识 com.liamchan.experiment.meadow，支持 iPadOS 15 及以上，可覆盖已有安装。

测试前从后台完全关闭 MeadowJourney，再打开。应用自动运行 A／B 分通道检查、C00 连续 60 帧组合检查，再进入 C02 实际单视图地图；失败时点“复制诊断”，将文字粘贴到对话。若卡死或被系统退出，下次打开会先显示同版本保留的记录，先复制再重新诊断；升级前的记录另存，避免把 build 20 错误当作本轮结果。[详细取证说明与证据边界](../docs/GPU_DIAGNOSTICS.md)。

[来源与校验值](MeadowJourney-build21.json) · [迭代日志](../docs/ITERATION_STATUS.md)。build 21 的 Release 编译归档和 IPA 完整性检查通过；云端只打包，模拟器及测试任务已跳过。60 帧检查在应用内执行，本轮尚未得到物理 iPad 的运行结果。SHA256SUMS 保存历次包的校验值。

历史版本：[build 20](MeadowJourney-build20.json) · [build 19](MeadowJourney-build19.json) · [build 18](MeadowJourney-build18.json) · [build 17](MeadowJourney-build17.json) · [build 16](MeadowJourney-build16.json) · [build 15](MeadowJourney-build15.json)。build 20 独立通道通过，但实际双视图地图随后 GPU 超时；真机证据已记入日志。通用 MeadowJourney-unsigned.ipa 暂保留 build 9，当前请使用上面的 build 21 专用文件。
