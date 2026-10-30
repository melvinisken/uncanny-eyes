"""Numeric sanity check of a rendered eye frame: radial ring statistics."""
import math
import sys

import simulate_render as sim
import scale_eye_assets as base


def ring_stats(rows, cx, cy, r0, r1):
    tr = tg = tb = n = 0
    for rr in range(r0, r1 + 1):
        for i in range(0, 360, 5):
            a = math.radians(i)
            x = int(round(cx + rr * math.cos(a)))
            y = int(round(cy + rr * math.sin(a)))
            if 0 <= y < len(rows) and 0 <= x < len(rows[0]):
                r, g, b = sim.base_rgb565(rows[y][x])
                tr += r
                tg += g
                tb += b
                n += 1
    if not n:
        return None
    return (tr // n, tg // n, tb // n)


def main():
    path = sys.argv[1]
    defs, arrays = base.parse_header(path)
    print(f'--- {path} ---')
    cx = cy = defs['SCREEN_WIDTH'] // 2
    for i_scale in (150, 200, 250):
        rows = sim.render(defs, arrays, i_scale)
        print(f'iScale={i_scale}:')
        for r0, r1, label in ((2, 8, 'center (pupil)'),
                              (10, 20, 'inner ring'),
                              (40, 50, 'mid ring'),
                              (75, 85, 'outer iris'),
                              (95, 105, 'sclera just outside box'),
                              (110, 118, 'far sclera')):
            c = ring_stats(rows, cx, cy, r0, r1)
            print(f'  r={r0:3d}-{r1:3d} {label:24s} rgb={c}')
        # find pupil edge: first radius where brightness rises above 60
        prev = None
        for rr in range(2, 90):
            c = ring_stats(rows, cx, cy, rr, rr)
            if c and sum(c) / 3 > 60:
                print(f'  pupil edge detected at r={rr}')
                break
    # lid frame
    rows = sim.render(defs, arrays, 200, True, 128, 126)
    print('lids frame (uT=128/lT=126):')
    for r0, r1, label in ((2, 10, 'center'), (60, 80, 'mid'),
                           (100, 118, 'edge')):
        print(f'  r={r0:3d}-{r1:3d} {label:10s} rgb={ring_stats(rows, cx, cy, r0, r1)}')


if __name__ == '__main__':
    main()
