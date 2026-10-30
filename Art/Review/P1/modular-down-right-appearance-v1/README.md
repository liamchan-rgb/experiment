# 右下整身外观 v1 · 当前候选

[正常全身行走](outfits-walk-120ms.gif) · [正常起停](outfits-start-stop-120ms.gif) · [全身站姿](outfits-idle-2x.png) · [主线程复核](art-review.md) · [技术结果](validation.json) · [重导](reexport-validation.json)

左绿衣/棕发/蓝眼，右蓝衣/银发/琥珀眼，灰裤低靴和背剑。保留已认可右下中性身体/13姿势，8个新独立资源组成16搭配208图。combinations保存全部实际图，8个带剑搭配有全13帧1×/2×板；actual-gif-frame-review-2x.png为正常GIF真正解码的8帧。

root独自制作、修复、审核，无智能体。主线程实际查看8个带剑搭配全部13帧全身1×/2×，主展示配对站姿、完整步态/起停姿势、GIF解码帧和帧时序。近远肩肘腕/髋膝踝足、袖口/裤口/靴底和五官整体比例、残边及背剑遮挡已检查。工具只返回静帧，没有连续播放器/实机验收声明。

技术：9清单，208真实组合、1664身体层/2496反射外观alpha、1248覆盖/416手部/624五官、104武器开关检查通过，14876旧文件保持；12个源槽位只变RGB，左上光源取样与源UV留存，公共装配器/合同未改，仅新增右下头导板。合同26和装配器21个现有测试通过。

正常行走8×120ms；起停22帧，首尾480ms其余120ms，不新增慢放。当前右下新外观认可为空；上一轮左下主要展示获用户“没问题下一步工作开始”认可，范围见对应approval.json，未扩展到所有未展示组合。八方向尚未全部完成，无女性/App/设备/IPA工作。HTTPS发布实测回执见delivery.json。

<!-- verified-delivery -->
美术提交 `ccc65c7035412bf1c7d15b69e29573258ab4f985`；三份HTTPS均实测HTTP200、MIME及SHA256/本地字节一致，GIF帧数/时序/循环已核对。593份重导文件字节一致。[正常GIF直链](https://raw.githubusercontent.com/liamchan-rgb/experiment/ccc65c7035412bf1c7d15b69e29573258ab4f985/Art/Review/P1/modular-down-right-appearance-v1/outfits-walk-120ms.gif)；回执见[delivery.json](delivery.json)。
