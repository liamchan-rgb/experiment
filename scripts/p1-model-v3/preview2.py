import sys, time
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from PIL import Image
import body, scene, preview, jog

if __name__ == '__main__':
    looks = [('forester', None), ('wayfarer', None), ('forester', 'leatherArmor'), ('forester', 'runeArmor')]
    faces = sys.argv[2].split(',') if len(sys.argv) > 2 else ['down', 'down-right', 'right', 'up-right', 'up']
    pose = preview.idle_pose() if len(sys.argv) < 4 else jog.jog_pose(int(sys.argv[3]))
    out = Image.new('RGBA', (len(faces) * 100 * 2, len(looks) * 160 * 2), (74, 104, 62, 255))
    t = time.time()
    for r, (o, a) in enumerate(looks):
        for c, f in enumerate(faces):
            J = body.skeleton(pose)
            im, order = scene.compose(J, f, o, 'trainingSword', a)
            out.alpha_composite(im.crop((78, 72, 178, 232)).resize((200, 320), Image.NEAREST), (c * 200, r * 320))
    out.save(sys.argv[1]); print('s', time.time() - t)
