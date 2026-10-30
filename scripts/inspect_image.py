"""Inspect an eye source image (v2): assumes a round eye on a dark background.

Detects the bright-region centroid, then a radial brightness/saturation
profile around it to locate pupil and iris radii.
"""
import math
import sys

from PIL import Image


def main():
    path = sys.argv[1]
    img = Image.open(path).convert('RGB')
    w, h = img.size
    px = img.load()
    print(f'size: {w}x{h}')

    # centroid of bright pixels (exclude dark background)
    sx = sy = n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r + g + b > 120:  # brightness threshold
                sx += x
                sy += y
                n += 1
    cx, cy = sx / n, sy / n
    print(f'bright-region centroid: ({cx:.1f}, {cy:.1f}), {n} px sampled')

    # radial profile around the centroid
    max_r = int(math.hypot(w, h) / 2)
    print('radius | bright | sat | mean color        | ring coverage')
    for r in range(4, max_r, 8):
        nb = ns = 0
        tr = tg = tb = 0
        cnt = 0
        dark_cnt = 0
        for i in range(0, 360, 3):
            a = math.radians(i)
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            if 0 <= x < w and 0 <= y < h:
                cr, cg, cb = px[x, y]
                if cr + cg + cb <= 120:
                    dark_cnt += 1
                tr += cr
                tg += cg
                tb += cb
                mx, mn = max(cr, cg, cb), min(cr, cg, cb)
                ns += (mx - mn)
                nb += (cr + cg + cb) / 3
                cnt += 1
        if cnt:
            cov = 100 * (cnt - dark_cnt) / cnt
            print(f'{r:5d} | {nb/cnt:6.1f} | {ns/cnt:5.1f} | '
                  f'({tr/cnt:4.0f},{tg/cnt:4.0f},{tb/cnt:4.0f}) | {cov:5.1f}%')


if __name__ == '__main__':
    main()
