"""Precisely locate the iris center: centroid of dark pixels inside the ball.

The iris+pupil form a dark disc inside the bright eyeball. Its centroid is
the true iris center - unlike the bright-pixel centroid, which bright
sclera/skin can pull away from the eye.
"""
import math
import sys

from PIL import Image


def main():
    path = sys.argv[1]
    img = Image.open(path).convert('RGB')
    w, h = img.size
    px = img.load()

    # ball mask: brightness > 120
    ball = [(x, y) for y in range(0, h, 2) for x in range(0, w, 2)
            if sum(px[x, y]) > 120]
    bcx = sum(x for x, _ in ball) / len(ball)
    bcy = sum(y for _, y in ball) / len(ball)
    print(f'bright (ball) centroid: ({bcx:.1f}, {bcy:.1f})')

    # dark pixels inside the ball (within 1.5x of the ball radius guess)
    dark = [(x, y) for y in range(0, h, 2) for x in range(0, w, 2)
            if sum(px[x, y]) < 150 * 3 / 2 and sum(px[x, y]) > 15 * 3 / 2
            and math.hypot(x - bcx, y - bcy) < min(w, h) * 0.45]
    if dark:
        dcx = sum(x for x, _ in dark) / len(dark)
        dcy = sum(y for _, y in dark) / len(dark)
        print(f'dark (iris+pupil) centroid: ({dcx:.1f}, {dcy:.1f})  '
              f'[{len(dark)} px]')
        print(f'offset from bright centroid: ({dcx - bcx:+.1f}, {dcy - bcy:+.1f})')

        # per-angle dark-region edge around the dark centroid -> radius fit
        radii = []
        for deg in range(0, 360, 15):
            a = math.radians(deg)
            rr = 1
            while rr < min(w, h) / 2:
                x = int(round(dcx + rr * math.cos(a)))
                y = int(round(dcy + rr * math.sin(a)))
                if not (0 <= x < w and 0 <= y < h):
                    break
                if sum(px[x, y]) > 200 * 3:  # clearly bright (sclera)
                    radii.append((deg, rr))
                    break
                rr += 2
            else:
                radii.append((deg, None))
        rs = [r for _, r in radii if r]
        print(f'dark-region edge radii (every 15 deg): {rs}')
        if rs:
            print(f'mean dark-region radius: {sum(rs) / len(rs):.0f}')
        bad = [(d, r) for d, r in radii if r is None]
        if bad:
            print(f'angles without bright transition: {[d for d, _ in bad]}')


if __name__ == '__main__':
    main()
