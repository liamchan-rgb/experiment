# 上斜独立资源包 v1

六包：forester绿色短上衣、wayfarer蓝色分叉外套、lower裤靴、hair-chestnut棕发、hair-silver银发、back-scabbard背剑。各包覆盖up-left/up-right及13姿势，人体与动作仍为原r6。

source/保存图像工具原稿、固定画布登记与原共同UV；authoring.json保存明确掩膜、解剖登记及变形域配置；每包包含透明PNG、独立源片、ORA/SVG编辑文件和asset.json。头发96×96局部图不含脸皮，跟随原头部矩阵；背视角不新增虚构五官。背剑保持同一物理肩侧，随上身运动。新增上斜头板定义见profile.json，原方向定义不变。

衣袖、裤腿与衣摆离线采样原共同身体UV，右上同步交换左右语义与坐标，使用独立固定光照源颜色。只在衣物中让出原来实际可见的手掌遮挡窗口，不复制皮肤或替换底模。不是任意衣物图自动生成全动作。

运行：python scripts/export-upper-wardrobe.py；python scripts/verify-upper-wardrobe.py；python scripts/reexport-upper-wardrobe.py（仓库根目录）。后者从已有最终产物验证重新生成逐字节一致。新外观尚待用户评价。
