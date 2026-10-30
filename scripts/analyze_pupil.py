"""Analyze the perceived pupil in a render: per-angle pupil edge + fit.

For each angle (0-359 deg) the pupil edge is the first radius where the
brightness rises above a threshold. Reports the edge radius per direction
and the center of the fitted circle -> shows whether the visible pupil is
off-center and in which direction. Also prints a magnified ASCII view of
the screen center.
"""
import math
import sys

import simulate_render as sim
import scale_eye_assets as base


def pupil_edges(rows, threshold=60, max_r=100):
    cx = cy = len(rows[0]) // 2
    edges = []
    for deg in range(0, 360, 10):
        a = math.radians(deg)
        edge = None
        for r in range(2, max_r):
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            if not (0 <= x < len(rows[0]) and 0 <= y < len(rows)):
                break
            pr, pg, pb = sim.base_rgb565(rows[y][x])
            if (pr + pg + pb) / 3 > threshold:
                edge = r
                break
        edges.append((deg, edge))
    return edges


def ascii_center(rows, half=50, step=2):
    chars = ' .:-=+*#%@'
    cx = cy = len(rows[0]) // 2
    lines = []
    for y in range(cy - half, cy + half, step):
        line = ''
        for x in range(cx - half, cx + half, step):
            r, g, b = sim.base_rgb565(rows[y][x])
            line += chars[min(9, int(((r + g + b) / 3) / 25.6))]
        lines.append(line)
    return '\n'.join(lines)


def main():
    path = sys.argv[1]
    i_scale = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    defs, arrays = base.parse_header(path)
    rows = sim.render(defs, arrays, i_scale)
    edges = pupil_edges(rows)
    print(f'--- {path} iScale={i_scale}: pupil edge per angle ---')
    xs, ys = [], []
    for deg, edge in edges:
        if edge is None:
            print(f'  {deg:3d} deg: no edge (dark beyond max_r)')
            continue
        print(f'  {deg:3d} deg: r={edge}')
        a = math.radians(deg)
        xs.append(edge * math.cos(a))
        ys.append(edge * math.sin(a))
    if xs:
        mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
        r_mean = sum(math.hypot(x, y) for x, y in zip(xs, ys)) / len(xs)
        print(f'fitted pupil center offset: ({mx:+.1f}, {my:+.1f}) px, '
              f'mean r={r_mean:.1f}')
    print('--- ASCII center view (50px half-range, 2px/char) ---')
    print(ascii_center(rows))


if __name__ == '__main__':
    main()
