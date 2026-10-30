"""Toggle the active eye style include in src/eyes/eye_assets.cpp.

Usage: python scripts/_toggle_style.py <style>   e.g. dragonEye_240 or default_large
"""
import re
import sys

style = sys.argv[1]
path = 'src/eyes/eye_assets.cpp'
lines = open(path, encoding='utf-8').read().split('\n')
out = []
for line in lines:
    m = re.match(r'^(//)?#include "(\w+)\.h"(.*)$', line)
    if m and ('_240' in m.group(2) or m.group(2) == 'default_large'):
        prefix = '' if m.group(2) == style else '//'
        line = prefix + '#include "' + m.group(2) + '.h"' + m.group(3)
    out.append(line)
open(path, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
active = [l.strip() for l in out if re.match(r'^#include "(?:\w+_240|default_large)\.h"', l)]
assert len(active) == 1, 'expected exactly 1 active style, got %s' % active
print('active style: %s' % active[0])
