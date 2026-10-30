"""Measure pupil eccentricity in a simulated render.

Renders the eye and computes the centroid of dark pixels near the screen
center at several iris scales. A perfectly centered pupil has offset (0,0).
"""
import math
import sys

import simulate_render as sim
import scale_eye_assets as base


def dark_centroid(rows, max_r=70, threshold=60):
    cx0 = cy0 = len(rows[0]) // 2
    sx = sy = n = 0
    for y in range(len(rows)):
        for x in range(len(rows[0])):
            if (x - cx0) ** 2 + (y - cy0) ** 2 > max_r ** 2:
                continue
            r, g, b = sim.base_rgb565(rows[y][x])
            if (r + g + b) / 3 < threshold:
                sx += x
                sy += y
                n += 1
    if not n:
        return None
    return (sx / n - cx0, sy / n - cy0, n)


def main():
    for path in sys.argv[1:]:
        defs, arrays = base.parse_header(path)
        print(f'--- {path} ---')
        for i_scale in (150, 200, 250):
            rows = sim.render(defs, arrays, i_scale)
            res = dark_centroid(rows)
            if res:
                dx, dy, n = res
                dist = math.hypot(dx, dy)
                print(f'  iScale={i_scale}: pupil centroid offset '
                      f'({dx:+.1f}, {dy:+.1f}) px, |offset|={dist:.1f} px '
                      f'({n} dark px)')


if __name__ == '__main__':
    main()
