import sys, math
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np
from PIL import Image
import model, body

def idle_pose():
    return dict(bob=0, lean=0, twist=0, legs={'R': (0, 0, 0), 'L': (0, 0, 0)},
                arms={'R': (0.05, .25), 'L': (0.05, .25)})

def frame(facing, pose):
    J = body.skeleton(pose)
    rgba, depth, sid = model.render(body.shapes(J, facing))
    return Image.fromarray(rgba), J

if __name__ == '__main__':
    out = Image.new('RGBA', (5 * 120 * 3, 170 * 3), (74, 104, 62, 255))
    for i, f in enumerate(['down', 'down-right', 'right', 'up-right', 'up']):
        im, _ = frame(f, idle_pose())
        out.alpha_composite(im.crop((68, 62, 188, 232)).resize((360, 510), Image.NEAREST), (i * 360, 0))
    out.save(sys.argv[1] if len(sys.argv) > 1 else 'idle.png')
