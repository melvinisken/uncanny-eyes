import re
import sys

path = sys.argv[1]
src = open(path, encoding='utf-8', errors='replace').read()
defs = {m.group(1): int(m.group(2))
        for m in re.finditer(r'#define\s+(\w+)\s+(\d+)', src)}
print('defines:', defs)
ok = True
for m in re.finditer(r'const uint(?:16|8)_t (\w+)\[[^\]]*\]\s*PROGMEM\s*=\s*\{(.*?)\};', src, re.S):
    name, body = m.group(1), m.group(2)
    vals = re.findall(r'0[xX][0-9A-Fa-f]+|[0-9]+', body)
    print(f'{name}: {len(vals)} values')
for key in ('SCLERA_WIDTH', 'IRIS_MAP_WIDTH', 'IRIS_WIDTH'):
    if key not in defs:
        ok = False
        print(f'missing define {key}')
expect = {
    'sclera': defs['SCLERA_WIDTH'] * defs['SCLERA_HEIGHT'],
    'iris': defs['IRIS_MAP_WIDTH'] * defs['IRIS_MAP_HEIGHT'],
    'upper': defs['SCREEN_WIDTH'] * defs['SCREEN_HEIGHT'],
    'lower': defs['SCREEN_WIDTH'] * defs['SCREEN_HEIGHT'],
    'polar': defs['IRIS_WIDTH'] * defs['IRIS_HEIGHT'],
}
counts = {}
for m in re.finditer(r'const uint(?:16|8)_t (\w+)\[[^\]]*\]\s*PROGMEM\s*=\s*\{(.*?)\};', src, re.S):
    counts[m.group(1)] = len(re.findall(r'0[xX][0-9A-Fa-f]+|[0-9]+', m.group(2)))
for name, want in expect.items():
    got = counts.get(name, 0)
    status = 'OK' if got == want else f'FAIL (want {want})'
    if got != want:
        ok = False
    print(f'{name}: {got} {status}')
sys.exit(0 if ok else 1)
