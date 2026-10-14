# iPad / iPhone 安装

[直接下载 MeadowJourney 1.0.1 IPA](https://github.com/liamchan-rgb/experiment/raw/refs/heads/main/Downloads/MeadowJourney-v1.0.1-unsigned.ipa)（约 9.9 MB）。

这是 1.0.1（build 2）修复版，IPA 的 `CFBundleName` 和 `CFBundleDisplayName` 都是 `MeadowJourney`，避免 SideStore 注册 App ID 时出现中文 `appIdName` 无效的错误。游戏内仍显示“安然”。旧下载链接也已更新到同一修复版。

1. 在 Safari 下载新版 IPA，保存到“文件”的“下载项”。
2. 打开已配置好的 SideStore → My Apps（我的应用）→ 右上角 ＋。
3. 在文件选择器中选中 `MeadowJourney-v1.0.1-unsigned.ipa`，等待 SideStore 重签并安装。

请选带 v1.0.1 的新文件，避免导入 iPad 上已经下载的旧包。SideStore 中应显示 `MeadowJourney`。

IPA 为未签名的真机 arm64 包，需要 iOS / iPadOS 15 及以上。私有仓库下载需要登录有仓库权限的 GitHub 账号。

若使用免费 Apple 账户，一般最多同时激活三个应用（包含 SideStore 自身）；需要留出一个安装名额。[SideStore 官方说明](https://docs.sidestore.io/zh/docs/faq)。

相关名称兼容问题：[SideStore #1489](https://github.com/SideStore/SideStore/issues/1489)。Xcode 编译、7 项测试和设备 archive 验证：[成功的 Actions 运行](https://github.com/liamchan-rgb/experiment/actions/runs/38512023512)。SHA-256 校验值见 `SHA256SUMS`。
