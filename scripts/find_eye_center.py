"""Locate the true eye center of a source image by multiple methods.

Methods:
  1. bright-pixel centroid (what make_eye_from_image.py uses today)
  2. red-dominant pixel centroid (iris centroid for reddish irises)
  3. darkest-blob centroid excluding the image border (pupil)
  4. coarse map of where the red-dominant pixels are (bounding box)
"""
import sys

from PIL import Image


def main():
    path = sys.argv[1]
    img = Image.open(path).convert('RGB')
    w, h = img.size
    px = img.load()
    print(f'size: {w}x{h}')

    # border brightness (background check)
    border = []
    for i in range(0, w, 10):
        border.append(sum(px[i, 2]) / 3)
        border.append(sum(px[i, h - 3]) / 3)
        border.append(sum(px[2, i]) / 3)
        border.append(sum(px[w - 3, i]) / 3)
    print(f'border mean brightness: {sum(border) / len(border):.0f}')

    # bright centroid
    sx = sy = n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r + g + b > 120:
                sx += x
                sy += y
                n += 1
    print(f'bright centroid: ({sx / n:.1f}, {sy / n:.1f})  [{n} px]')

    # red-dominant centroid
    sx = sy = n = 0
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r > (g + b) * 0.75 and r + g + b > 100:  # red-dominant
                sx += x
                sy += y
                n += 1
                minx, miny = min(minx, x), min(miny, y)
                maxx, maxy = max(maxx, x), max(maxy, y)
    if n:
        print(f'red-dominant centroid: ({sx / n:.1f}, {sy / n:.1f})  [{n} px]')
        print(f'red-dominant bbox: x {minx}-{maxx}, y {miny}-{maxy} '
              f'(center {(minx + maxx) / 2:.0f},{(miny + maxy) / 2:.0f})')

    # darkest blob centroid excluding the outer 5% border
    m = int(min(w, h) * 0.05)
    best = []
    for y in range(m, h - m, 2):
        for x in range(m, w - m, 2):
            r, g, b = px[x, y]
            best.append((r + g + b, x, y))
    best.sort()
    dark = best[:max(1, len(best) // 500)]
    dx = sum(x for _, x, _ in dark) / len(dark)
    dy = sum(y for _, _, y in dark) / len(dark)
    print(f'darkest-blob centroid: ({dx:.1f}, {dy:.1f})  '
          f'[mean brightness {sum(v for v, _, _ in dark) / len(dark) / 3:.0f}]')


if __name__ == '__main__':
    main()
