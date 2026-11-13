/**
 * 预览页：把每个角色预设烘焙出的整张 sprite sheet 放大显示。
 * 打开 /?scale=4&s=0.65 （scale = 放大倍数，s = 精灵倍率）
 */
import { bakeSheet } from './pixel/bake';
import { setSpriteScale } from './character/rig';
import { CHARACTERS, buildEquipment } from './items/characters';

const q = new URLSearchParams(location.search);
const scale = Number(q.get('scale') ?? 4);
if (q.get('s')) setSpriteScale(Number(q.get('s')));

for (const preset of CHARACTERS) {
  const { canvas } = bakeSheet(buildEquipment(preset).resolve());
  const big = document.createElement('canvas');
  big.width = canvas.width * scale;
  big.height = canvas.height * scale;
  const g = big.getContext('2d')!;
  g.imageSmoothingEnabled = false;
  g.drawImage(canvas, 0, 0, big.width, big.height);
  document.body.append(`${preset.id} · ${preset.name}`, big);
}
