import importlib.util, json, sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('split', ROOT / 'scripts/build-p1-head-split.py')
split = importlib.util.module_from_spec(spec); spec.loader.exec_module(split)
comp = split.load_compositor()
BASE = json.loads(split.SELECTION.read_text())['base']
def selection(outfit='forester', weapon='trainingSword', armor=None):
    body = [split.LOWER, split.ARMORS[armor]] if armor else [split.OUTFITS[outfit], split.LOWER]
    return body + split.WEAPONS[weapon] + [split.HEADS[outfit]['hair'], split.HEADS[outfit]['face']]
def layers(direction, clip, frame, sel=None):
    return comp.layers(BASE, sel or selection(), direction, clip, frame)
def flat(ls):
    out = Image.new('RGBA', (256, 256))
    for _, im in ls: out.alpha_composite(im)
    return out
def bbox(im):
    a = np.array(im.getchannel('A')); ys, xs = np.where(a > 8)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None
