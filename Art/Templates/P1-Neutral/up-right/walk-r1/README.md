# up-right 中性人体与基本步态候选

最终作者数据：`authoring.json`；`authoring-draft.json`仅保留Luna辅助草案，曾存在像素归属与关节误判，不用于发布导出。每方向固定同一头部与共同中性躯干，8个语义层，idle00 + walk01–08。新方向尚待用户认可。

用项目公共导出器重建：

```sh
python scripts/export-neutral-direction.py Art/Templates/P1-Neutral/up-right/walk-r1 --review Art/Review/P1/neutral-upper-diagonals-v1/up-right
```

`asset.json` / `motion.json`供公共compositor按同一规范装配；头发、脸、衣物和武器不在本包。坐标是256×256固定画布，部件不按alpha边界适配。美术源稿的整体／独立组件按显式解剖锚点固定注册后烘焙，所有引擎图层仍是256×256；没有外观ID分支或运行时部件缩放。

可见原稿、图像工具生成稿、固定注册、判退批量稿、错误步相和替换部件均保留于`source/`。共同torso的完整下衬补隐藏区域，原可见背心／短裤和颈部保留；中性色衣料明确归torso，裸露四肢单独归属。每侧关节以人物解剖左右命名，近远遮挡由drawOrder定义。

本轮只证明可见中性idle／walk候选可装配；未校准完整隐蔽人体、独立服装／发型／面部组合、背负插槽角度或起停路径，不表示App接入／用户认可。主线程整身审阅与正常速交付见`Art/Review/P1/neutral-upper-diagonals-v1/`。
