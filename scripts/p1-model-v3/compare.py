import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parents[1] / 'p1-skeleton-v2'))
from PIL import Image
import numpy as np
from common import layers, comp
import preview

HEAD = ('head.base', 'face.', 'hair.')
def head_layers(facing):
    return [(s, im) for s, im in layers(facing, 'idle', 0) if s.startswith(HEAD)]

def with_head(facing, body_img, J):
    """Existing head art moved so its idle neck lands on the model's neck."""
    import model, body
    fx, fz = body.FACING[facing]
    W = np.array([[fz, 0, fx], [0, 1, 0], [-fx, 0, fz]])
    n = W @ J['neck']
    sx, sy = model.CENTER_X + n[0], model.GROUND_Y - n[1] + .5 * n[2]
    idle_neck = comp.frames[(facing, 'idle', 0)]['joints']['neck']
    dx, dy = int(round(sx - idle_neck[0])), int(round(sy - idle_neck[1]))
    out = body_img.copy()
    for _, im in head_layers(facing):
        out.alpha_composite(Image.fromarray(np.roll(np.array(im), (dy, dx), (0, 1))))
    return out

if __name__ == '__main__':
    faces = ['down', 'down-right', 'right', 'up-right', 'up']
    out = Image.new('RGBA', (5 * 100 * 3, 2 * 160 * 3), (74, 104, 62, 255))
    for i, f in enumerate(faces):
        old = Image.new('RGBA', (256, 256))
        for _, im in layers(f, 'idle', 0): old.alpha_composite(im)
        im, J = preview.frame(f, preview.idle_pose())
        new = with_head(f, im, J)
        for r, c in enumerate((old, new)):
            out.alpha_composite(c.crop((78, 70, 178, 230)).resize((300, 480), Image.NEAREST), (i * 300, r * 480))
    out.save(sys.argv[1])
