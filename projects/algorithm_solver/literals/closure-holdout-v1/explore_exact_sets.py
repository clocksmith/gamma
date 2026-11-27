#!/usr/bin/env python3
"""POST HOC on scored sets. Does the reversal hold for the exact (verified) trainers, not only the lazy ones?

    python3 -I explore_exact_sets.py

Scores the exact open and exact closed chains (out/exact/, brute-force checked at audited steps) and the lazy chains
against the frozen BPE dictionary on every set, on the equal-size grid, with the exact parser.
Writes out/posthoc-exact-sets.json.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

GRID = [84, 200, 400, 600, 900, 1200, 1408, 1700, 2000, 2350, 2700, 3300, 3924]
SETS = {'train': (OH / 'frozen/sets/train.json', LIT), 'dev': (OH / 'frozen/sets/dev.json', LIT),
        'fresh': (OH / 'sets/fresh.json', OH), 'project': (OH / 'sets/project.json', OH),
        'fresh2': (HERE / 'sets/fresh2.json', HERE), 'project-python': (HERE / 'sets/project-python.json', HERE),
        'project-javascript': (HERE / 'sets/project-javascript.json', HERE)}
_D = None


def chain(path):
    return [bytes.fromhex(line.split()[5]) for line in Path(path).read_text().splitlines() if line.startswith('E ') and len(line.split()) == 6]


def init(d):
    global _D
    _D = d


def tokens(entries):
    d = B.Dictionary(entries)
    return sum(len(B.parse_tokens(d.edges(r))) for r in _D)


def main():
    frozen = json.loads((HERE / 'frozen' / 'dictionaries.json').read_text())
    A = frozen['alphabet']
    full = {k: [bytes.fromhex(h) for h in v] for k, v in frozen['dictionaries'].items()}
    singles = full['bpe-K4096'][:A]
    orders = {'bpe': full['bpe-K4096'][A:], 'open-lazy': full['token-K4096'][A:], 'closed-lazy': full['closed-K4096'][A:],
              'open-exact': chain(HERE / 'out/exact/exact-entry-s1-whole.txt')[A:],
              'closed-exact': chain(HERE / 'out/exact/exact-closed-s1-whole.txt')[A:]}
    out = {'note': 'post hoc: exact chains scored on already-scored sets', 'grid': GRID, 'tokens': {}}
    for name, (spec, root) in SETS.items():
        docs = [(root / f['path']).read_bytes() for f in json.loads(spec.read_text())['files']]
        with Pool(8, initializer=init, initargs=(docs,)) as pool:
            jobs = [(a, m) for a in orders for m in GRID]
            res = dict(zip(jobs, pool.map(tokens, [singles + orders[a][:m] for a, m in jobs])))
        out['tokens'][name] = {a: [res[(a, m)] for m in GRID] for a in orders}
        b = out['tokens'][name]['bpe']
        print(name.ljust(18), ' | '.join(f'{a} {100 * (out["tokens"][name][a][0] / b[0] - 1):+.1f}/{100 * (out["tokens"][name][a][-1] / b[-1] - 1):+.1f}'
                                         for a in orders if a != 'bpe'), flush=True)
    (HERE / 'out' / 'posthoc-exact-sets.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
