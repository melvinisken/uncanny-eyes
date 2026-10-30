"""Build a side-by-side comparison: source image vs pipeline render.

Left frame: the source image scaled exactly like the sclera texture build
(iris edge -> 90px radius around the frame center), cropped to the 240x240
render window. Right frame: the simulated render. Crosshairs mark the frame
center in both. Differences between the two expose pipeline errors;
similarities mean the source image content is being reproduced faithfully.
"""
import math
import sys

from PIL import Image, ImageDraw

import simulate_render as sim
import scale_eye_assets as base
import make_eye_from_image as mk


def main():
    src_path = sys.argv[1]
    asset_path = sys.argv[2]
    out_path = sys.argv[3]

    # pipeline geometry detection (same as the asset build)
    img = Image.open(src_path).convert('RGB')
    (cx, cy), pup_r, iris_r, eye_r, prof, _, _ = mk.detect_geometry(img)

    # left frame: source scaled like build_sclera
    scale = 90.0 / iris_r
    left = Image.new('RGB', (240, 240), (0, 0, 0))
    lpx = left.load()
    for ty in range(240):
        for tx in range(240):
            sx = (tx - 119.5) / scale
            sy = (ty - 119.5) / scale
            r_src = math.hypot(sx, sy)
            if r_src > eye_r:
                f = eye_r / r_src
                sx, sy = sx * f, sy * f
            lpx[tx, ty] = mk.sample_bilinear(img.load(), img.size[0], img.size[1],
                                             cx + sx, cy + sy)

    # right frame: simulated render (straight gaze)
    defs, arrays = base.parse_header(asset_path)
    rows = sim.render(defs, arrays, 200)
    right = Image.new('RGB', (240, 240))
    right.putdata([sim.base_rgb565(p) for row in rows for p in row])

    sheet = Image.new('RGB', (494, 254), (30, 30, 30))
    draw = ImageDraw.Draw(sheet)
    sheet.paste(left, (0, 14))
    sheet.paste(right, (254, 14))
    draw.text((4, 2), 'source (as scaled by pipeline)')
    draw.text((258, 2), 'pipeline render iScale=200')
    for ox in (0, 254):
        draw.line((ox + 120, 14, ox + 120, 253), fill=(255, 255, 255), width=1)
        draw.line((ox, 14 + 120, ox + 239, 14 + 120), fill=(255, 255, 255), width=1)
    sheet.save(out_path)
    print(f'written: {out_path}')
    print(f'geometry used: center ({cx:.1f},{cy:.1f}), pupil r={pup_r}, '
          f'iris r={iris_r}, eyeball r={eye_r}')


if __name__ == '__main__':
    main()
