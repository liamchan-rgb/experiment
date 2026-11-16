"""像素场景的最终限色：按整张图挑一套 N 色调色板（k-means），不抖动，再最近邻放大"""
import sys
from PIL import Image
src, out, n, W, H = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
im = Image.open(src).convert('RGB')
q = im.quantize(colors=n, method=Image.Quantize.MAXCOVERAGE, kmeans=2, dither=Image.Dither.NONE).convert('RGB')
q.resize((W, H), Image.NEAREST).save(out)
