#!/usr/bin/env python3
"""Scale 128px uncanny-eyes asset headers to 240px for GC9A01 displays.

Reads an eye style header from the original dalori/ESP32-uncanny-eyes-halloween-skull
project (e.g. dragonEye.h) and writes a new header with all asset tables scaled
by 240/128 = 1.875, matching the proven default_large.h geometry scheme
(the original defaultEye.h with sclera 200px became default_large.h with 375px).

What is scaled how:
  sclera  (RGB565)  bilinear upscale, x1.875   (contains the painted pupil)
  iris    (RGB565)  bilinear upscale, x1.875, cylindrical wrap in x
  upper/lower (u8)  bilinear upscale to 240x240 (eyelid threshold masks)
  polar   (u16)     nearest-neighbor on the packed angle/dist codes, x1.875 -
                   preserves the artist's warp of the iris exactly
  IRIS_MIN/IRIS_MAX  x1.875, preserving the relative pupil size
                   (iScale, iris map height and polar radius all scale
                   together, see eye_render.cpp: d = iScale * (p & 0x7F) / 128)

Usage:
  python scripts/scale_eye_assets.py data/eyes/128/dragonEye.h data/eyes/dragonEye_240.h
"""

import math
import re
import sys

SCALE = 240 / 128
TARGET_SCREEN = 240


def parse_header(path):
    src = open(path, encoding='utf-8', errors='replace').read()
    defs = {}
    for m in re.finditer(r'#define\s+(\w+)\s+(\d+)', src):
        defs[m.group(1)] = int(m.group(2))
    arrays = {}
    for m in re.finditer(
            r'const\s+(uint16_t|uint8_t)\s+(\w+)\[[^\]]*\]\s*PROGMEM\s*=\s*\{(.*?)\};',
            src, re.S):
        kind, name, body = m.groups()
        arrays[name] = (kind, [int(t[2:], 16) if t[:2].lower() == '0x' else int(t, 10)
                                for t in re.findall(r'0[xX][0-9A-Fa-f]+|\d+', body)])
    return defs, arrays


def bilinear(img, w, h, nw, nh, unpack, blend, pack, wrap_x=False):
    out = []
    for y in range(nh):
        fy = (y + 0.5) * h / nh - 0.5
        y0 = math.floor(fy)
        ty = fy - y0
        ya = max(0, min(h - 1, y0))
        yb = max(0, min(h - 1, y0 + 1))
        row_a = ya * w
        row_b = yb * w
        for x in range(nw):
            fx = (x + 0.5) * w / nw - 0.5
            x0 = math.floor(fx)
            tx = fx - x0
            if wrap_x:
                xa, xb = x0 % w, (x0 + 1) % w
            else:
                xa = max(0, min(w - 1, x0))
                xb = max(0, min(w - 1, x0 + 1))
            p00 = img[row_a + xa]
            p10 = img[row_a + xb]
            p01 = img[row_b + xa]
            p11 = img[row_b + xb]
            out.append(pack(blend(unpack(p00), unpack(p10),
                                  unpack(p01), unpack(p11), tx, ty)))
    return out


def blend_rgb565(p00, p10, p01, p11, tx, ty):
    r0 = p00[0] + (p10[0] - p00[0]) * tx
    g0 = p00[1] + (p10[1] - p00[1]) * tx
    b0 = p00[2] + (p10[2] - p00[2]) * tx
    r1 = p01[0] + (p11[0] - p01[0]) * tx
    g1 = p01[1] + (p11[1] - p01[1]) * tx
    b1 = p01[2] + (p11[2] - p01[2]) * tx
    r = round(r0 + (r1 - r0) * ty)
    g = round(g0 + (g1 - g0) * ty)
    b = round(b0 + (b1 - b0) * ty)
    return r, g, b


def unpack_rgb565(p):
    return ((p >> 11) & 0x1F, (p >> 5) & 0x3F, p & 0x1F)


def pack_rgb565(c):
    return ((c[0] & 0x1F) << 11) | ((c[1] & 0x3F) << 5) | (c[2] & 0x1F)


def unpack_u8(p):
    return (p,)


def pack_u8(c):
    return c[0] & 0xFF


def blend_u8(p00, p10, p01, p11, tx, ty):
    v0 = p00[0] + (p10[0] - p00[0]) * tx
    v1 = p01[0] + (p11[0] - p01[0]) * tx
    return (round(v0 + (v1 - v0) * ty),)


def scale_polar_nearest(img, w, h, nw, nh):
    # The polar map packs angle (p >> 7, 0..511) and distance (p & 0x7F)
    # into one uint16. Interpolating the packed value would corrupt the
    # codes, so scale the codes with nearest-neighbor instead.
    out = []
    for y in range(nh):
        sy = min(h - 1, int((y + 0.5) * h / nh))
        row = sy * w
        for x in range(nw):
            sx = min(w - 1, int((x + 0.5) * w / nw))
            out.append(img[row + sx])
    return out


def scaled(n):
    return max(1, round(n * SCALE))


def emit_array(f, ctype, name, values, per_line):
    f.write(f'const {ctype} {name}[{len(values)}] PROGMEM = {{\n')
    line = []
    for i, v in enumerate(values):
        if ctype == 'uint16_t':
            line.append(f'0x{v:04X}')
        else:
            line.append(str(v))
        if len(line) == per_line:
            f.write(', '.join(line) + ',\n')
            line = []
    if line:
        f.write(', '.join(line))
    f.write('\n};\n\n')


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    defs, arrays = parse_header(in_path)
    required = ['SCLERA_WIDTH', 'SCLERA_HEIGHT', 'IRIS_MAP_WIDTH',
                'IRIS_MAP_HEIGHT', 'SCREEN_WIDTH', 'SCREEN_HEIGHT',
                'IRIS_WIDTH', 'IRIS_HEIGHT']
    missing = [k for k in required if k not in defs]
    if missing:
        sys.exit(f'error: {in_path} lacks {missing}')
    for name in ('sclera', 'iris', 'upper', 'lower', 'polar'):
        if name not in arrays:
            sys.exit(f'error: {in_path} lacks array "{name}"')

    iris_min = defs.get('IRIS_MIN', 90)
    iris_max = defs.get('IRIS_MAX', 130)

    sw, sh = defs['SCLERA_WIDTH'], defs['SCLERA_HEIGHT']
    mw, mh = defs['IRIS_MAP_WIDTH'], defs['IRIS_MAP_HEIGHT']
    iw, ih = defs['IRIS_WIDTH'], defs['IRIS_HEIGHT']

    n_sw, n_sh = scaled(sw), scaled(sh)
    n_mw, n_mh = scaled(mw), scaled(mh)
    n_iw, n_ih = scaled(iw), scaled(ih)
    n_iris_min, n_iris_max = round(iris_min * SCALE), round(iris_max * SCALE)

    print(f'{in_path}:')
    print(f'  sclera      {sw}x{sh} -> {n_sw}x{n_sh} (bilinear)')
    print(f'  iris map    {mw}x{mh} -> {n_mw}x{n_mh} (bilinear, wrap)')
    print(f'  polar       {iw}x{ih} -> {n_iw}x{n_ih} (nearest)')
    print(f'  lids        {defs["SCREEN_WIDTH"]}x{defs["SCREEN_HEIGHT"]}'
          f' -> {TARGET_SCREEN}x{TARGET_SCREEN} (bilinear)')
    print(f'  IRIS_MIN/MAX {iris_min}/{iris_max} -> {n_iris_min}/{n_iris_max}')

    print('  scaling sclera...')
    n_sclera = bilinear(arrays['sclera'][1], sw, sh, n_sw, n_sh,
                        unpack_rgb565, blend_rgb565, pack_rgb565)
    print('  scaling iris map...')
    n_iris = bilinear(arrays['iris'][1], mw, mh, n_mw, n_mh,
                     unpack_rgb565, blend_rgb565, pack_rgb565, wrap_x=True)
    print('  scaling polar map...')
    n_polar = scale_polar_nearest(arrays['polar'][1], iw, ih, n_iw, n_ih)
    print('  scaling eyelid maps...')
    n_upper = bilinear(arrays['upper'][1], defs['SCREEN_WIDTH'],
                       defs['SCREEN_HEIGHT'], TARGET_SCREEN, TARGET_SCREEN,
                       unpack_u8, blend_u8, pack_u8)
    n_lower = bilinear(arrays['lower'][1], defs['SCREEN_WIDTH'],
                       defs['SCREEN_HEIGHT'], TARGET_SCREEN, TARGET_SCREEN,
                       unpack_u8, blend_u8, pack_u8)

    if out_path is None:
        print('dry run, no output file given')
        return

    with open(out_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'// Auto-generated by scripts/scale_eye_assets.py from {in_path}\n')
        f.write(f'// Eye style scaled from {defs["SCREEN_WIDTH"]}px to {TARGET_SCREEN}px'
                f' (factor {SCALE}).\n\n')
        f.write(f'#define IRIS_MIN {n_iris_min}\n')
        f.write(f'#define IRIS_MAX {n_iris_max}\n\n')
        f.write(f'#define SCLERA_WIDTH {n_sw}\n')
        f.write(f'#define SCLERA_HEIGHT {n_sh}\n\n')
        emit_array(f, 'uint16_t', 'sclera', n_sclera, 16)
        f.write(f'#define IRIS_MAP_WIDTH {n_mw}\n')
        f.write(f'#define IRIS_MAP_HEIGHT {n_mh}\n\n')
        emit_array(f, 'uint16_t', 'iris', n_iris, 16)
        f.write(f'#define SCREEN_WIDTH {TARGET_SCREEN}\n')
        f.write(f'#define SCREEN_HEIGHT {TARGET_SCREEN}\n\n')
        emit_array(f, 'uint8_t', 'upper', n_upper, 20)
        emit_array(f, 'uint8_t', 'lower', n_lower, 20)
        f.write(f'#define IRIS_WIDTH {n_iw}\n')
        f.write(f'#define IRIS_HEIGHT {n_ih}\n\n')
        emit_array(f, 'uint16_t', 'polar', n_polar, 16)
    print(f'  written: {out_path}')


if __name__ == '__main__':
    main()
