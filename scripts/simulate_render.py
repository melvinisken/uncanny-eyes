"""Render a simulated eye frame in ASCII to validate a generated asset.

Replicates the render math of src/eyes/eye_render.cpp (straight gaze,
no lids, fixed iris scale) and prints the result as ASCII art.
"""
import math
import sys

import scale_eye_assets as base


def render(defs, arrays, i_scale=200, use_lids=False, u_t=0, l_t=0):
    sw, sh = defs['SCLERA_WIDTH'], defs['SCLERA_HEIGHT']
    bw, bh = defs['IRIS_WIDTH'], defs['IRIS_HEIGHT']
    mw, mh = defs['IRIS_MAP_WIDTH'], defs['IRIS_MAP_HEIGHT']
    scr_w, scr_h = defs['SCREEN_WIDTH'], defs['SCREEN_HEIGHT']
    sclera, iris, polar = arrays['sclera'][1], arrays['iris'][1], arrays['polar'][1]
    upper, lower = arrays['upper'][1], arrays['lower'][1]

    eye_x = (sw - scr_w) // 2
    eye_y = (sh - scr_h) // 2
    iris_off_x = (sw - bw) // 2
    iris_off_y = (sh - bh) // 2

    rows = []
    for sy in range(scr_h):
        row = []
        for sx in range(scr_w):
            tx, ty = eye_x + sx, eye_y + sy
            if use_lids and (lower[sy * scr_w + sx] <= l_t or
                             upper[sy * scr_w + sx] <= u_t):
                row.append(0)
                continue
            ix, iy = tx - iris_off_x, ty - iris_off_y
            if 0 <= ix < bw and 0 <= iy < bh:
                p = polar[iy * bw + ix]
                dist = p & 0x7F
                d = i_scale * dist // 128
                if d < mh:
                    ang = mw * (p >> 7) // 512
                    row.append(iris[d * mw + ang])
                    continue
            row.append(sclera[ty * sw + tx])
        rows.append(row)
    return rows


def to_ascii(rows, size=60):
    step = max(1, len(rows) // size)
    chars = ' .:-=+*#%@'
    out = []
    for y in range(0, len(rows), step):
        line = ''
        for x in range(0, len(rows[0]), step):
            p = rows[y][x]
            r = ((p >> 11) & 0x1F) * 255 // 31
            g = ((p >> 5) & 0x3F) * 255 // 63
            b = (p & 0x1F) * 255 // 31
            v = (r + g + b) / 3
            line += chars[min(9, int(v / 25.6))]
        out.append(line)
    return '\n'.join(out)


def main():
    path = sys.argv[1]
    i_scale = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    use_lids = len(sys.argv) > 3 and sys.argv[3] == 'lids'
    defs, arrays = base.parse_header(path)
    rows = render(defs, arrays, i_scale, use_lids, 128, 126)
    print(f'--- {path} (iScale={i_scale}, lids={use_lids}) ---')
    print(to_ascii(rows, 56))

    # PNG previews: three iris scales + lids frame, side by side
    try:
        from PIL import Image
        frames = []
        for tag, s, lids in ((150, 150, False), (200, 200, False),
                             (250, 250, False), ('lids', 200, True)):
            fr = render(defs, arrays, s, lids, 128, 126)
            img = Image.new('RGB', (len(fr[0]), len(fr)))
            img.putdata([base_rgb565(p) for row in fr for p in row])
            frames.append((tag, img))
        total_w = sum(im.size[0] for _, im in frames) + 10 * (len(frames) - 1)
        total_h = max(im.size[1] for _, im in frames) + 14
        sheet = Image.new('RGB', (total_w, total_h), (30, 30, 30))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(sheet)
        x = 0
        for tag, im in frames:
            sheet.paste(im, (x, 14))
            draw.text((x + 4, 2), f'iScale={tag}')
            x += im.size[0] + 10
        out = path.replace('.h', '_preview.png')
        sheet.save(out)
        print(f'preview written: {out}')
    except ImportError:
        print('Pillow not installed - no PNG preview')


def base_rgb565(p):
    r = ((p >> 11) & 0x1F) * 255 // 31
    g = ((p >> 5) & 0x3F) * 255 // 63
    b = (p & 0x1F) * 255 // 31
    return (r, g, b)


if __name__ == '__main__':
    main()
