"""Check the source image's inner iris for asymmetric dark sectors.

Mean color per angular sector in the ring [r0, r1] around the eye center.
If the source is bright on all sides, the render asymmetry would be a
pipeline artifact; if the source is dark on one side, it is image content.
"""
import math
import sys

from PIL import Image

import make_eye_from_image as mk


def main():
    path = sys.argv[1]
    img = Image.open(path).convert('RGB')
    (cx, cy), pup_r, iris_r, eye_r, prof, _ = mk.detect_geometry(img)
    print(f'center ({cx:.1f},{cy:.1f}), pupil r={pup_r}, iris r={iris_r}')
    px = img.load()
    w, h = img.size
    for r0, r1, label in ((pup_r + 5, pup_r + 25, 'inner iris'),
                          (pup_r + 25, (pup_r + iris_r) // 2, 'mid iris'),
                          ((pup_r + iris_r) // 2, iris_r - 5, 'outer iris')):
        print(f'--- ring {label} (r {r0}-{r1}) ---')
        for deg in range(0, 360, 30):
            b_sum = n = 0
            for rr in range(r0, r1, 4):
                a = math.radians(deg)
                x = int(round(cx + rr * math.cos(a)))
                y = int(round(cy + rr * math.sin(a)))
                if 0 <= x < w and 0 <= y < h:
                    r, g, b = px[x, y]
                    b_sum += (r + g + b) / 3
                    n += 1
            bar = '#' * int(b_sum / n / 10) if n else ''
            print(f'  {deg:3d} deg: {b_sum / n:6.1f} {bar}')


if __name__ == '__main__':
    main()
