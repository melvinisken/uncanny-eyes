"""ASCII visualization of an image: luminance mapped to characters."""
import sys

from PIL import Image

img = Image.open(sys.argv[1]).convert('RGB')
size = int(sys.argv[2]) if len(sys.argv) > 2 else 56
img.thumbnail((size, size))
px = img.load()
w, h = img.size
chars = ' .:-=+*#%@'
for y in range(h):
    row = ''
    for x in range(w):
        r, g, b = px[x, y]
        row += chars[min(9, int(((r + g + b) / 3) / 25.6))]
    print(row)
