#!/usr/bin/env python3
"""Deterministic split of the authored LeetCode catalogue for the scaling study. Reads file names, sizes and bytes only
to drop duplicates; it never scores anything.

    python3 -I select_catalogue.py

Units are problems with one Python (python/N.py) and one JavaScript (javascript/N.js) solution under
projects/algorithm_solver/catalogue/authored/*/. Dropped before ranking: ids present in more than one folder in either
language; files outside 64..4096 bytes; files equal to another file after removing all whitespace (both copies).
Problems are ranked by sha256('bits-scaling-v1:' + id). Ranks 0-599: sealed test pool (no session opens or scores it
before a preregistration names it); ranks 600-799: dev; the rest: training pool in rank order, so every training size
n is the first n training problems (nested).
Writes sets/catalogue-{test,dev,train}.json.
"""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAMMA = HERE.parents[3]
AUTH = GAMMA / 'projects' / 'algorithm_solver' / 'catalogue' / 'authored'
TEST, DEV = 600, 200


def squeezed(b):
    return hashlib.sha256(b''.join(b.split())).hexdigest()


def main():
    py, js = collections.defaultdict(list), collections.defaultdict(list)
    for p in AUTH.glob('*/python/*.py'):
        if p.stem.isdigit():
            py[int(p.stem)].append(p)
    for p in AUTH.glob('*/javascript/*.js'):
        if p.stem.isdigit():
            js[int(p.stem)].append(p)
    ids = sorted(k for k in set(py) & set(js) if len(py[k]) == 1 and len(js[k]) == 1)
    ids = [k for k in ids if all(64 <= p[0].stat().st_size <= 4096 for p in (py[k], js[k]))]
    sq = collections.Counter(squeezed(p[0].read_bytes()) for k in ids for p in (py[k], js[k]))
    ids = [k for k in ids if all(sq[squeezed(p[0].read_bytes())] == 1 for p in (py[k], js[k]))]
    ids.sort(key=lambda k: hashlib.sha256(f'bits-scaling-v1:{k}'.encode()).hexdigest())

    def rec(k, rank):
        out = []
        for lang, p in (('python', py[k][0]), ('javascript', js[k][0])):
            b = p.read_bytes()
            out.append({'path': str(p.relative_to(GAMMA)), 'unit': str(k), 'rank': rank, 'lang': lang, 'bytes': len(b),
                        'sha256': hashlib.sha256(b).hexdigest()})
        return out
    parts = {'test': ids[:TEST], 'dev': ids[TEST:TEST + DEV], 'train': ids[TEST + DEV:]}
    (HERE / 'sets').mkdir(exist_ok=True)
    for name, ks in parts.items():
        files = [f for r, k in enumerate(ks) for f in rec(k, r)]
        (HERE / 'sets' / f'catalogue-{name}.json').write_text(json.dumps(
            {'set': f'catalogue-{name}', 'source': 'projects/algorithm_solver/catalogue/authored (agent-authored LeetCode solutions)',
             'unit': 'problem id', 'problems': len(ks), 'files': files}, indent=1) + '\n')
        print(name, len(ks), 'problems', sum(f['bytes'] for f in files), 'bytes')


if __name__ == '__main__':
    main()
