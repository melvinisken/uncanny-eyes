"""Analyze eyelid map behavior of an eye asset header.

Shows, per lid (upper/lower), how much of the screen is covered for a range
of thresholds, and how the pupil-tracking rule (uThreshold sampled near the
pupil, lThreshold = 254 - uThreshold) drives both lids across the eye's
gaze range. Pure stdlib.
"""
import math
import re
import sys


def parse(path):
    src = open(path, encoding='utf-8', errors='replace').read()
    defs = {m.group(1): int(m.group(2))
            for m in re.finditer(r'#define\s+(\w+)\s+(\d+)', src)}
    arrays = {}
    for m in re.finditer(r'const uint(?:16|8)_t (\w+)\[[^\]]*\]\s*PROGMEM\s*=\s*\{(.*?)\};', src, re.S):
        arrays[m.group(1)] = [int(t[2:], 16) if t[:2].lower() == '0x' else int(t, 10)
                              for t in re.findall(r'0[xX][0-9A-Fa-f]+|[0-9]+', m.group(2))]
    return defs, arrays


def coverage_rows(lid, w, h, threshold):
    """For each column: covered fraction of rows (value <= threshold)."""
    frac = []
    for x in range(w):
        covered = 0
        for y in range(h):
            if lid[y * w + x] <= threshold:
                covered += 1
        frac.append(covered / h)
    return sum(frac) / len(frac), min(frac), max(frac)


def lid_profile(lid, w, h, label):
    print(f'--- {label} map {w}x{h} ---')
    hist = [0] * 256
    for v in lid:
        hist[v] += 1
    total = w * h
    top = sorted(range(256), key=lambda v: -hist[v])[:6]
    print('value histogram (top):', {v: hist[v] for v in top if hist[v]})
    print(f'  zeros: {hist[0]} px, 255s: {hist[255]} px')
    for label2, x, y in [('top-left', 5, 5), ('top-center', w // 2, 5),
                         ('center', w // 2, h // 2), ('bottom-center', w // 2, h - 6),
                         ('bottom-left', 5, h - 6), ('bottom-right', w - 6, h - 6),
                         ('top-right', w - 6, 5)]:
        print(f'  {label2}: {lid[y * w + x]}')


def simulate_tracking(defs, arrays, mode='coupled'):
    """mode='coupled': original rule (lT = 254 - uT).
    mode='direct':   new rule - both lids sample near the pupil
                     (mirrors src/eyes/eye_motion.cpp)."""
    sw, sh = defs['SCLERA_WIDTH'], defs['SCLERA_HEIGHT']
    iw, ih = defs['IRIS_WIDTH'], defs['IRIS_HEIGHT']
    w, h = defs['SCREEN_WIDTH'], defs['SCREEN_HEIGHT']
    upper, lower = arrays['upper'], arrays['lower']

    print(f'--- simulated pupil tracking ({mode}) over gaze range ---')
    print(f'(sclera {sw}x{sh}, box {iw}x{ih}, screen {w}x{h})')
    print('gaze eyeX,eyeY -> uT, lT -> covered rows upper/lower')
    u_t, l_t = 128, 128
    us, ls = [], []
    for eyeX in range(0, sw - w + 1, (sw - w) // 6):
        for eyeY in range(0, sh - h + 1, max(1, (sh - h) // 6)):
            sample_x = max(0, min(w - 1, sw // 2 - eyeX // 2))
            pupil_y = sh // 2 - eyeY
            # upper lid: slightly above the pupil
            up_y = pupil_y - ih // 4
            if up_y < 0:
                n_up = 0
            else:
                n_up = (upper[up_y * w + sample_x] +
                        upper[up_y * w + (w - 1 - sample_x)]) // 2
            for _ in range(12):
                u_t = (u_t * 3 + n_up) // 4
            if mode == 'coupled':
                l_t = 254 - u_t
            else:
                lo_y = pupil_y + ih // 4
                if 0 <= lo_y < h:
                    n_lo = (lower[lo_y * w + sample_x] +
                            lower[lo_y * w + (w - 1 - sample_x)]) // 2
                    n_lo = min(n_lo, 254)
                else:
                    n_lo = 0
                for _ in range(12):
                    l_t = (l_t * 3 + n_lo) // 4
            cu, cu_min, cu_max = coverage_rows(upper, w, h, u_t)
            cl, cl_min, cl_max = coverage_rows(lower, w, h, l_t)
            us.append(cu)
            ls.append(cl)
            print(f'  eyeX={eyeX:3d} eyeY={eyeY:3d} -> uT={u_t:3d} lT={l_t:3d} '
                  f'-> upper covered {cu * 100:4.1f}% (col {cu_min * 100:3.0f}-{cu_max * 100:3.0f}%), '
                  f'lower covered {cl * 100:4.1f}%')
    print(f'upper lid coverage range: {min(us) * 100:.1f}% - {max(us) * 100:.1f}%')
    print(f'lower lid coverage range: {min(ls) * 100:.1f}% - {max(ls) * 100:.1f}%')


def main():
    path = sys.argv[1]
    defs, arrays = parse(path)
    w, h = defs['SCREEN_WIDTH'], defs['SCREEN_HEIGHT']
    lid_profile(arrays['upper'], w, h, 'upper')
    lid_profile(arrays['lower'], w, h, 'lower')
    if len(sys.argv) > 2 and sys.argv[2] == 'direct':
        simulate_tracking(defs, arrays, mode='direct')
    else:
        simulate_tracking(defs, arrays, mode='coupled')


if __name__ == '__main__':
    main()
