# 镜像与光照来源

- `raw-mirror-idle-4x.png`：未校正光照的镜像站姿，仅作为编辑输入，不是最终交付。
- `relight-generated.png`：imagegen提供的一份光照参考。其alpha、形体和比例不作为动作或人物几何来源。
- `relight-registration.json` / `relight-registered.png`：完整参考画布按固定比例注册到256px源空间，无逐帧边界拟合。
- `approved-left-uv`：在认可版的隔离副本上捕获原像素坐标，导出九帧与原版逐像素相同；R/G是源x/y数据，不是颜色素材。
- `relit-textures`：将工具参考的皮肤/背心/短裤颜色绑定到固定源面，保留原描边和所有alpha。隐藏源区保留原色。颜色采样始终限于同材质，最大注册邻域不超过2px；记录见lighting-bake.json。
- `head-local.png`：96px头部挂载验证用局部源；镜像局部原点与坐标变换在mirror-authoring.json/motion.json中记录。

左右语义、关节和遮挡与动作同时镜像。仅在离线生成中处理RGB，公共运行装配器不重着色、不拟合、不按外观ID选择人体。原左上源和已认可画面保持不变。
