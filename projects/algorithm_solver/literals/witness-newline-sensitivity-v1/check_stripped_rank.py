#!/usr/bin/env python3
"""How much of the unrestricted rank of matched80 rests on the trailing newline. Python 3.8+ and Git; no numpy, no solver.

Every one of the 80 sources (compact and canonical) ends in a newline. This recomputes the rank of the program
vectors v(w)[c] = sum of BASE**i over positions i holding c, in the prime field P, once on the stored bytes and once
with trailing newlines removed. The rank is only a lower bound on the unrestricted minimum; this script makes no
claim about the stripped minimum itself.

    python3 -B check_stripped_rank.py /path/to/gamma        exits 1 unless the recorded values are recomputed
"""
import json
import subprocess
import sys

REPO = sys.argv[1] if len(sys.argv) > 1 else '.'
P, B = 1_000_000_007, 2
PIN, ROOT = '59ff04415ff2afd04ff2ed451340f4f02852bf18', 'projects/algorithm_solver/literals/'
EXPECTED = {'compact': (79, 78), 'canonical': (79, 79)}  # (stored bytes, trailing newline removed)


def blob(path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{PIN}:{ROOT}{path}'])


def rank(words):
    chars = {c: i for i, c in enumerate(sorted(set(b''.join(words))))}
    rows = []
    for w in set(words):
        v, weight = [0] * len(chars), 1
        for c in w:
            v[chars[c]] = (v[chars[c]] + weight) % P
            weight = weight * B % P
        rows.append(v)
    r = 0
    for col in range(len(chars)):
        pivot = next((i for i in range(r, len(rows)) if rows[i][col]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        inv = pow(rows[r][col], P - 2, P)
        rows[r] = [x * inv % P for x in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][col]:
                f = rows[i][col]
                rows[i] = [(x - f * y) % P for x, y in zip(rows[i], rows[r])]
        r += 1
    return r


ids = set(json.loads(blob('matched80-v1/labels/ids.json')))
manifest = json.loads(blob('scale-v2/generated/manifest.json'))['rows']
ok = True
for variant, expected in EXPECTED.items():
    sources = [blob('scale-v2/generated/' + r['file']) for r in manifest if r['variant'] == variant and r['id'] in ids]
    stripped = [s.rstrip(b'\n') for s in sources]
    assert len(sources) == 80 and all(s.endswith(b'\n') for s in sources) and len(set(stripped)) == 80
    got = (rank(sources), rank(stripped))
    print(f'{variant:9} rank on stored bytes {got[0]}, trailing newline removed {got[1]}')
    ok &= got == expected
print('ok' if ok else 'FAILED: recorded values not recomputed')
sys.exit(0 if ok else 1)
