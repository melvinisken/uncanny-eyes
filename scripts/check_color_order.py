"""Check the R/B channel convention of eye asset iris maps.

The iris texture is the most color-distinctive table (hazel/brown human eye,
fiery red dragon eye). If the standard RGB565 convention holds, the red
channel (bits 11-15) must dominate over blue (bits 0-4). Prints mean r5/b5
per eye so swapped (BGR) data would stand out immediately.
"""
import sys

import scale_eye_assets as base


def channel_stats(values):
    r_sum = b_sum = 0
    for p in values:
        r_sum += (p >> 11) & 0x1F
        b_sum += p & 0x1F
    n = len(values)
    return r_sum / n, b_sum / n


def main():
    for path in sys.argv[1:]:
        defs, arrays = base.parse_header(path)
        for name in ('iris', 'sclera'):
            if name not in arrays:
                continue
            vals = arrays[name][1]
            r_mean, b_mean = channel_stats(vals)
            verdict = 'R-dominant (standard RGB565)' if r_mean > b_mean else (
                'B-dominant (BGR-stored!)' if b_mean > r_mean * 1.2 else 'neutral')
            print(f'{path} {name}: mean r5={r_mean:.1f} b5={b_mean:.1f} -> {verdict}')


if __name__ == '__main__':
    main()
