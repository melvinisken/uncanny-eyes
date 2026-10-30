"""Locate the dark-red ("red-black") iris pixels in a source image.

Prints centroid + bounding box of dark-red pixels (the red-black iris the
user refers to) and, for comparison, the brightest pixels (sclera).
"""
import sys

from PIL import Image


def main():
    path = sys.argv[1]
    img = Image.open(path).convert('RGB')
    w, h = img.size
    px = img.load()

    def stats(match, label):
        sx = sy = n = 0
        minx, miny, maxx, maxy = w, h, 0, 0
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                if match(px[x, y]):
                    sx += x
                    sy += y
                    n += 1
                    minx, miny = min(minx, x), min(miny, y)
                    maxx, maxy = max(maxx, x), max(maxy, y)
        if not n:
            print(f'{label}: none')
            return
        cx, cy = sx / n, sy / n
        print(f'{label}: centroid ({cx:.1f}, {cy:.1f})  [{n} px]  '
              f'bbox x {minx}-{maxx} y {miny}-{maxy} '
              f'(bbox center {(minx + maxx) / 2:.0f}, {(miny + maxy) / 2:.0f})')
        # vertical thirds occupancy
        third = h // 3
        counts = [0, 0, 0]
        for y in range(0, h, 2):
            for x in range(0, w, 2):
                if match(px[x, y]):
                    counts[min(2, y // third)] += 1
        total = sum(counts) or 1
        print(f'  vertical thirds: top {100 * counts[0] / total:.0f}% / '
              f'middle {100 * counts[1] / total:.0f}% / '
              f'bottom {100 * counts[2] / total:.0f}%')

    print(f'image: {w}x{h}')

    # dark red: red clearly dominant, dark overall
    stats(lambda c: (c[0] > (c[1] + c[2]) * 0.9 and c[0] < 120
                    and c[0] + c[1] + c[2] < 240),
          'dark-red (rot-schwarze Iris)')
    # bright sclera
    stats(lambda c: sum(c) > 600, 'bright (sclera/highlights)')
    # very dark (pupil candidate)
    stats(lambda c: sum(c) < 60, 'near-black')


if __name__ == '__main__':
    main()
