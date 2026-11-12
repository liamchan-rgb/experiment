# HD-2D 像素人物管线

用代码绘制 Q 版像素人物，采用纸娃娃（Paper Doll）分层装备，导出 5 方向 × 8 帧的 sprite sheet，并生成 MeadowJourney 现有格式的 4 × 4 人物图集。不使用任何外部图片素材。

**制作标准、五官 / 发型 / 衣服的替换规则、交接步骤见 [../docs/CHARACTER_SPRITES.md](../docs/CHARACTER_SPRITES.md)。**

```bash
npm install
npm run dev      # 预览全部套装的 sheet；参数 ?scale=4&s=0.8&weapon=weapon_staff
npm run export   # 输出到 export/（ios 图集 + 原生 sheet + JSON）
npm run check    # 类型检查
```

## 目录

```
src/
  pixel/      PixelLayer（索引色图层、自动描边）、Brush（单位坐标画笔、光照量化、粗粝噪声）、palette、bake
  character/  rig（骨架与姿态）、layers（图层顺序）、paperdoll（合成）、equipment（装备槽）、
              animator（帧状态机）、scarfPhysics（围巾尾弹簧链）、types（ItemDef 等数据格式）
  items/      body（身体与五官）、hair/ top/ bottom/ shoes/ scarf/ bag/ weapon/（每件装备一个文件）、
              outfits（套装预设）、registry（自动收集装备）、shared（手臂 / 躯干 / 袖子等共用形状）
scripts/      export.ts（导出）、png.ts（无依赖 PNG 编码）
export/       已导出的图集，交接给 iPad 工程
```

## 装备接口

```ts
const eq = new Equipment(body);
eq.equip('weapon_main', staff);
eq.unequip('scarf');
eq.setPalette('hair', ramp('hair-red', '#b03a26'));
eq.setVariant('top', 'green');
bakeSheet(eq.resolve()); // 按装备 id + 调色板 id 缓存，只在换装时重新烘焙
```

新增一件装备：在 `src/items/<分类>/` 下加一个导出 `ItemDef` 的文件。预览页和导出脚本会自动收录，不需要修改核心代码。
