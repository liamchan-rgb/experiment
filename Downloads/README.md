# SideStore 安装与迭代包

[最新取证包：1.5.7 build 20，iPad GPU 分通道诊断](MeadowJourney-build20.json)。此包用于取得真机证据，尚未确认修复 GPU 超时。

直接下载：[MeadowJourney-b20.ipa](https://raw.githubusercontent.com/liamchan-rgb/experiment/feat/layered-living-scene/Downloads/MeadowJourney-b20.ipa)。在 Safari 下载后保存到「文件」，再打开 SideStore → My Apps → ＋，选择 MeadowJourney-b20.ipa 重签安装。安装名 MeadowJourney，包标识 com.liamchan.experiment.meadow，支持 iPadOS 15 及以上，可覆盖已有安装。

测试前从后台完全关闭 MeadowJourney，再打开。应用自动按 A／B／C 阶段检查；失败时点“复制诊断”，将文字粘贴到对话。若卡死或被系统退出，下次打开会先显示保留的记录，先复制再重新诊断。[详细取证说明与证据边界](../docs/GPU_DIAGNOSTICS.md)。

[来源与校验值](MeadowJourney-build20.json) · [迭代日志](../docs/ITERATION_STATUS.md)。build 20 的 iPadOS Release 归档和 IPA 完整性检查通过；云端只打包，模拟器及测试任务已跳过。尚未得到物理 iPad 的本轮诊断结果。SHA256SUMS 保存历次包的校验值。

历史版本：[build 19](MeadowJourney-build19.json) · [build 18](MeadowJourney-build18.json) · [build 17](MeadowJourney-build17.json) · [build 16](MeadowJourney-build16.json) · [build 15](MeadowJourney-build15.json)。build 19 的同进程降级未解决用户实机问题，失败反馈已记入日志。通用 MeadowJourney-unsigned.ipa 暂保留 build 9，当前请使用上面的 build 20 专用文件。
