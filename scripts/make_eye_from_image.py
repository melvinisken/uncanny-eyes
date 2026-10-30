#!/usr/bin/env python3
"""Create a new eye asset header from a source image.

Builds a 240px eye that behaves exactly like the reference asset
(default_large.h): identical geometry, polar map and eyelid masks; only the
colors come from the given image. The image is expected to show a round
eyeball (iris + pupil + sclera) on a dark background.

What is generated:
  sclera (375x375 RGB565) - the whole image, scaled so the iris outer edge
      lands exactly at the polar box boundary (90px radius), pupil center
      at the texture center. The pupil disc is repainted solid up to the
      maximum dilation radius so no sclera ring shows at any iris scale.
      The source is radially clamped at the eyeball edge (no background).
  iris map (489x122 RGB565) - the image's iris ring, polar-unwrapped:
      column = angle (512 sectors, same encoding as the polar map),
      row = radius from iris outer edge (row 0) to the pupil edge.
  polar / upper / lower / IRIS_MIN / IRIS_MAX - copied from the reference.

Usage:
  python scripts/make_eye_from_image.py eye_test.png data/eyes/eye_test_240.h
  optional: --ref data/eyes/default_large.h
            --center 488,485 --iris-radius 170 --pupil-radius 50
            --eyeball-radius 405   (manual overrides for detection)
"""
import argparse
import math
import sys

from PIL import Image

import scale_eye_assets as base  # parse_header, rgb565 helpers


def rgb888_from_565(p):
    r = (p >> 11) & 0x1F
    g = (p >> 5) & 0x3F
    b = p & 0x1F
    return (r * 255 // 31, g * 255 // 63, b * 255 // 31)


def pack_rgb888(c):
    """Convert an 8-bit RGB tuple to RGB565."""
    r5 = c[0] * 31 // 255
    g6 = c[1] * 63 // 255
    b5 = c[2] * 31 // 255
    return (r5 << 11) | (g6 << 5) | b5


def sample_bilinear(px, w, h, x, y):
    x = max(0.0, min(w - 1.001, x))
    y = max(0.0, min(h - 1.001, y))
    x0, y0 = int(x), int(y)
    tx, ty = x - x0, y - y0
    out = []
    for c in range(3):
        p00 = px[x0, y0][c]
        p10 = px[x0 + 1, y0][c]
        p01 = px[x0, y0 + 1][c]
        p11 = px[x0 + 1, y0 + 1][c]
        v = (p00 + (p10 - p00) * tx) * (1 - ty) + (p01 + (p11 - p01) * tx) * ty
        out.append(int(round(v)))
    return tuple(out)


def ring_mean(px, w, h, cx, cy, r0, r1, step=3):
    """Mean color of the ring r0..r1 around (cx, cy)."""
    tr = tg = tb = n = 0
    for rr in range(r0, r1 + 1, max(1, (r1 - r0) // 8)):
        for i in range(0, 360, step):
            a = math.radians(i)
            x = int(round(cx + rr * math.cos(a)))
            y = int(round(cy + rr * math.sin(a)))
            if 0 <= x < w and 0 <= y < h:
                r, g, b = px[x, y]
                tr += r
                tg += g
                tb += b
                n += 1
    if not n:
        return (0, 0, 0)
    return (tr // n, tg // n, tb // n)


def detect_geometry(img):
    """Locate the eye geometry.

    Primary method: the iris ring is the connected dark (red-black) region
    inside the eyeball (pupil + ring). A flood fill starting at the darkest
    ball pixel collects it; its centroid is the TRUE eye center - more
    reliable than brightness centroids, which a bright crescent or shadowed
    half of the eyeball can pull away from the iris.

    Falls back to the radial-brightness-profile method if the flood fill
    finds nothing plausible.
    """
    px = img.load()
    w, h = img.size
    step = 2
    gw, gh = w // step, h // step

    def rgb(gx, gy):
        return px[min(w - 1, gx * step), min(h - 1, gy * step)]

    ball = {}
    for gy in range(gh):
        for gx in range(gw):
            r, g, b = rgb(gx, gy)
            if (r + g + b) / 3 > 20:  # not background
                ball[(gx, gy)] = (r + g + b) / 3

    dark = {k: v for k, v in ball.items() if v < 75}
    if len(dark) >= 50:
        seed = min(dark, key=lambda k: dark[k])
        comp = {seed}
        stack = [seed]
        while stack:
            x, y = stack.pop()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in dark and n not in comp:
                    comp.add(n)
                    stack.append(n)

        ball_area = len(ball)
        if ball_area * 0.005 < len(comp) < ball_area * 0.6:
            cx = step * sum(x for x, _ in comp) / len(comp)
            cy = step * sum(y for _, y in comp) / len(comp)
            # radii via radial brightness profile around the ring centroid
            # (robust for both dark rings and brighter brown rings, where a
            # flood-fill radius would only cover the darkest part)
            prof = []
            for r in range(2, int(min(w, h) / 2) - 2):
                b_sum = cnt = 0
                for i in range(0, 360, 3):
                    a = math.radians(i)
                    x = int(round(cx + r * math.cos(a)))
                    y = int(round(cy + r * math.sin(a)))
                    if 0 <= x < w and 0 <= y < h:
                        cr, cg, cb = px[x, y]
                        b_sum += (cr + cg + cb) / 3
                        cnt += 1
                if cnt:
                    prof.append((r, b_sum / cnt))

            def first_sustained(start_idx, predicate, count=4):
                for i in range(start_idx, len(prof) - count):
                    if all(predicate(prof[i + k][1]) for k in range(count)):
                        return prof[i][0]
                return None

            iris_r_default = max(40, int(min(w, h) / 5))

            # pupil edge: first sustained rise out of the dark core
            pupil_r = first_sustained(0, lambda v: v > 55) or iris_r_default
            # iris outer edge: sustained bright sclera
            iris_r = first_sustained(
                next((i for i, (r, v) in enumerate(prof)
                      if r >= pupil_r), 0), lambda v: v > 140) or iris_r_default
            pupil_r = min(pupil_r, int(iris_r * 0.6))
            iris_idx = next((i for i, (r, v) in enumerate(prof)
                             if r >= iris_r), 0)
            eyeball_r = first_sustained(iris_idx, lambda v: v < 40) or (
                int(min(w, h) / 2) - 5)
            return ((cx, cy), max(4, pupil_r), iris_r, eyeball_r, prof,
                    (cx, cy), 'iris-ring flood fill')

    return detect_geometry_profile(img)


def detect_geometry_profile(img):
    """Fallback: brightness-centroid center + radial profile detection."""
    px = img.load()
    w, h = img.size
    sx = sy = n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if r + g + b > 120:
                sx += x
                sy += y
                n += 1
    cx, cy = sx / n, sy / n
    max_r = int(min(w, h) / 2) - 2
    prof = []
    for r in range(2, max_r):
        b_sum = cnt = 0
        for i in range(0, 360, 3):
            a = math.radians(i)
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            if 0 <= x < w and 0 <= y < h:
                cr, cg, cb = px[x, y]
                b_sum += (cr + cg + cb) / 3
                cnt += 1
        if cnt:
            prof.append((r, b_sum / cnt))

    def first_sustained(start_idx, predicate, count=4):
        for i in range(start_idx, len(prof) - count):
            if all(predicate(prof[i + k][1]) for k in range(count)):
                return prof[i][0]
        return None

    pupil_r = first_sustained(0, lambda v: v > 55) or 50
    pupil_idx = next((i for i, (r, v) in enumerate(prof) if r >= pupil_r), 0)
    iris_r = first_sustained(pupil_idx, lambda v: v > 140) or 170
    iris_idx = next((i for i, (r, v) in enumerate(prof) if r >= iris_r), 0)
    eyeball_r = first_sustained(iris_idx, lambda v: v < 40) or (max_r - 5)
    return (cx, cy), pupil_r, iris_r, eyeball_r, prof, (cx, cy), 'brightness profile'


def build_sclera(img, cx, cy, iris_r, eyeball_r, pupil_disc_r, sw, sh, box_w,
                 pupil_color):
    px = img.load()
    w, h = img.size
    scale = (box_w / 2) / iris_r  # box half (90 tex px) at the iris edge
    tex_c = (sw - 1) / 2.0
    out = []
    for ty in range(sh):
        for tx in range(sw):
            dx = tx - tex_c
            dy = ty - tex_c
            r_tex = math.hypot(dx, dy)
            if r_tex <= pupil_disc_r:
                out.append(pack_rgb888(pupil_color))
                continue
            # sample the source, clamped at the eyeball edge
            sx = dx / scale
            sy = dy / scale
            r_src = math.hypot(sx, sy)
            if r_src > eyeball_r and r_src > 0:
                sx = sx * eyeball_r / r_src
                sy = sy * eyeball_r / r_src
            c = sample_bilinear(px, w, h, cx + sx, cy + sy)
            out.append(pack_rgb888(c))
    return out


def build_iris_map(img, cx, cy, iris_r, pupil_r, map_w, map_h, box_w):
    px = img.load()
    w, h = img.size
    # texture rows: row 0 = iris outer edge, row map_h-1 = pupil edge
    out = []
    for d in range(map_h):
        frac = d / (map_h - 1)
        r_src = iris_r - (iris_r - pupil_r) * frac
        row = []
        for a in range(map_w):
            angle_code = a * 512 / map_w
            theta = 2 * math.pi * angle_code / 512
            x = cx - r_src * math.cos(theta)
            y = cy - r_src * math.sin(theta)
            row.append(pack_rgb888(sample_bilinear(px, w, h, x, y)))
        out.extend(row)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('image')
    ap.add_argument('output')
    ap.add_argument('--ref', default='data/eyes/default_large.h')
    ap.add_argument('--center', default=None, help='pupil center x,y')
    ap.add_argument('--iris-radius', type=int, default=None)
    ap.add_argument('--pupil-radius', type=int, default=None)
    ap.add_argument('--eyeball-radius', type=int, default=None)
    args = ap.parse_args()

    ref_defs, ref_arrays = base.parse_header(args.ref)
    sw = ref_defs['SCLERA_WIDTH']
    sh = ref_defs['SCLERA_HEIGHT']
    mw = ref_defs['IRIS_MAP_WIDTH']
    mh = ref_defs['IRIS_MAP_HEIGHT']
    bw = ref_defs['IRIS_WIDTH']
    iris_min = ref_defs['IRIS_MIN']
    iris_max = ref_defs['IRIS_MAX']

    img = Image.open(args.image).convert('RGB')
    print(f'image: {args.image} ({img.size[0]}x{img.size[1]})')
    print(f'reference: {args.ref} (sclera {sw}x{sh}, iris map {mw}x{mh}, box {bw}, '
          f'IRIS {iris_min}/{iris_max})')

    (cx, cy), pup_r, iris_r, eye_r, prof, (pcx, pcy), method = detect_geometry(img)
    if args.center:
        cx, cy = (float(v) for v in args.center.split(','))
    if args.pupil_radius:
        pup_r = args.pupil_radius
    if args.iris_radius:
        iris_r = args.iris_radius
    if args.eyeball_radius:
        eye_r = args.eyeball_radius
    print(f'detection method: {method}')
    print(f'detected: eye center ({cx:.1f},{cy:.1f}), pupil center '
          f'({pcx:.1f},{pcy:.1f}), pupil r={pup_r}, iris r={iris_r}, '
          f'eyeball r={eye_r}')
    if iris_r <= pup_r:
        sys.exit('error: iris radius must be larger than pupil radius')

    # pupil disc: radius the pupil edge reaches at IRIS_MAX (widest dilation)
    pupil_disc_r = (bw / 2) * (1 - 128 * mh / (127.0 * iris_max))
    print(f'pupil disc radius in texture: {pupil_disc_r:.1f} px')

    pupil_color = ring_mean(img.load(), img.size[0], img.size[1],
                            cx, cy, 2, max(3, pup_r * 2 // 3))
    print(f'pupil color: {pupil_color}')

    print('building sclera texture...')
    sclera = build_sclera(img, cx, cy, iris_r, eye_r, pupil_disc_r, sw, sh, bw,
                          pupil_color)
    print('building iris map...')
    iris = build_iris_map(img, cx, cy, iris_r, pup_r, mw, mh, bw)

    with open(args.output, 'w', encoding='utf-8', newline='\n') as f:
        f.write(f'// Auto-generated by scripts/make_eye_from_image.py from {args.image}\n')
        f.write('// Geometry, polar map and eyelid masks match the reference asset\n')
        f.write(f'// ({args.ref}); only the colors come from the image.\n\n')
        f.write(f'#define IRIS_MIN {iris_min}\n')
        f.write(f'#define IRIS_MAX {iris_max}\n\n')
        f.write(f'#define SCLERA_WIDTH {sw}\n')
        f.write(f'#define SCLERA_HEIGHT {sh}\n\n')
        base.emit_array(f, 'uint16_t', 'sclera', sclera, 16)
        f.write(f'#define IRIS_MAP_WIDTH {mw}\n')
        f.write(f'#define IRIS_MAP_HEIGHT {mh}\n\n')
        base.emit_array(f, 'uint16_t', 'iris', iris, 16)
        f.write(f"#define SCREEN_WIDTH {ref_defs['SCREEN_WIDTH']}\n")
        f.write(f"#define SCREEN_HEIGHT {ref_defs['SCREEN_HEIGHT']}\n\n")
        base.emit_array(f, 'uint8_t', 'upper', ref_arrays['upper'][1], 20)
        base.emit_array(f, 'uint8_t', 'lower', ref_arrays['lower'][1], 20)
        f.write(f'#define IRIS_WIDTH {bw}\n')
        f.write(f'#define IRIS_HEIGHT {ref_defs["IRIS_HEIGHT"]}\n\n')
        base.emit_array(f, 'uint16_t', 'polar', ref_arrays['polar'][1], 16)
    print(f'written: {args.output}')


if __name__ == '__main__':
    main()
