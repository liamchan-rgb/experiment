# 猎弓战斗持弓返修 · build54 候选

用户反馈此前战斗中的“手和弓对不上”。复核发现，起手时箭已经出现而拉弦手尚未接触弦；原拉弦手随前臂旋转、指向弓弦不清楚，松弦后又跟着弦向前。此前对 build53 猎弓持弓美术的内部放行不再沿用。

本轮修改实际共用 BowRig：持弓手与弓柄共用接触点；拉弦手先接触弦，再搭箭、拉开、释放并向后小幅回摆；握弓手、拉弦手、弓身和弦重新排序，手掌压住弦而不是被弦盖住；拉弦手腕转向箭尾。射出箭矢的起点由同一套实际放箭姿势计算，单人、小队和审核导出一致。原1.048秒命中/一次结算、猎弓 D8 普攻、强击公式与行走背弓不变。

本人查看正常速度整身和整场 GIF 的全部实际解码帧（各190帧、20ms），以及六个动作各5个整身姿势和整场关键样本；这不等于设备体验验收。另检查六动作共3606个导出姿势的持弓手与弓柄像素接触，搭箭的103个采样里拉弦手与弦均有接触（见 grip-geometry.json），技术接触不能取代美术审核。GIF 为离线近似合成，并非 App 录屏。

生成数据：`swift run --package-path Vendor/ClassroomGameCore MeadowSupportReviewExport Art/Review/Battle/hunting-bow-grip-r1`；`python3 scripts/review-hunting-bow-grip-r1.py --prepare` 后使用 `scripts/export-smooth-status-review.swift` 和生产光场生成 `dice-light-samples.json`；执行两个 review 脚本生成整身与整场，`python3 scripts/verify-hunting-bow-grip-r1.py` 做像素接触检查。未运行 App、模拟器或实机。

## 构建与核验

源码 `50e555778208b2b823d1e7a208d552f3bfeb69e2`，设备 Release [归档](https://github.com/liamchan-rgb/experiment/actions/runs/40447896365)成功；107 项纯测试和五项独立检查通过。IPA 为 1.6.28/build54，已检查 CRC、经典 ZIP2.0 结构与 iPhoneOS 资源；macOS 与 Linux 导出的3606个弓姿及场景数据逐字段一致。详见 `Media/Build54/package.json`。整身和场景预览使用相同战斗动作数据，视频每秒50帧为离线预览帧率，不是设备实测。

同一私人审核页已更新为猎弓持弓复审，默认整身预览并可切换整场；原四件装备及此前通过的重剑/权杖演出保留，旧反馈按 revision 迁移。审核页浏览器检查和部署记录见 `browser-qa/result.json`、`deployment.json`。

## 交付核验

交付提交 `62d105042220070606aa56ba3957ab3e518108f7`：直接 IPA、整身 GIF、整场 GIF 与关键画面共五条链接已完整下载并与仓库内容比较，IPA 再次检查 CRC，两个 GIF 均在浏览器成功加载；74 个选定路径的提交对象已核对。回执见 `delivery.json`。用户仍需实际安装并审核修正效果。
