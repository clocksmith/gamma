#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Two candidate predictors of held-out token loss, computed before any test set is opened.

    python3 -I explore_predictors.py

1. Leverage share, per rule and dictionary size, from training data alone. For a dictionary D and each fragment w,
   s(w) is the fewest tokens that spell w with D minus w, and u(w) its uses in the exact minimum-token training
   parse. Each use saves s(w) - 1 tokens against spelling w without it; the leverage share is
       sum u(w) * max(0, s(w) - 2)  /  sum u(w) * (s(w) - 1),
   the part of those savings beyond one token per use. A closed or BPE dictionary has s(w) = 2 for every w whose
   two pieces it holds, so its share is near 0.
2. Shared coverage, per target set, with no dictionary: the share of 12-byte windows of the target files whose string
   occurs in at least two training files.

Development data only: `train` and `dev`. Coverage is also reported for the already-scored sets, labelled post hoc.
Writes out/dev-predictors.json.
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

SIZES = [84, 400, 1408, 2000, 3924]
SETS = {'train': (OH / 'frozen/sets/train.json', LIT, 'train'), 'dev': (OH / 'frozen/sets/dev.json', LIT, 'dev'),
        'fresh': (OH / 'sets/fresh.json', OH, 'post hoc'), 'project': (OH / 'sets/project.json', OH, 'post hoc'),
        'fresh2': (HERE / 'sets/fresh2.json', HERE, 'post hoc'),
        'project-python': (HERE / 'sets/project-python.json', HERE, 'post hoc'),
        'project-javascript': (HERE / 'sets/project-javascript.json', HERE, 'post hoc')}


def chain(path):
    return [bytes.fromhex(line.split()[5]) for line in Path(path).read_text().splitlines() if line.startswith('E ') and len(line.split()) == 6]


def load(name):
    spec, root, _ = SETS[name]
    return [(root / f['path']).read_bytes() for f in json.loads(spec.read_text())['files']]


_TRAIN = None


def init(train):
    global _TRAIN
    _TRAIN = train


def leverage(entries):
    d = B.Dictionary(entries)
    uses = {}
    for raw in _TRAIN:
        for s in B.parse_tokens(d.edges(raw)):
            if s < d.ESC and len(d.entries[s]) > 1:
                uses[s] = uses.get(s, 0) + 1
    num = den = 0
    for s, u in uses.items():
        w = d.entries[s]
        without = B.Dictionary([e for e in entries if e != w])
        sp = len(B.parse_tokens(without.edges(w)))
        num += u * max(0, sp - 2)
        den += u * (sp - 1)
    return num / den if den else 0.0


def coverage(target, train, k=12):
    seen = {}
    for i, raw in enumerate(train):
        for g in {raw[j:j + k] for j in range(len(raw) - k + 1)}:
            seen[g] = seen.get(g, 0) + 1
    hit = tot = 0
    for raw in target:
        for j in range(len(raw) - k + 1):
            tot += 1
            hit += seen.get(raw[j:j + k], 0) >= 2
    return hit / tot


def main():
    frozen = json.loads((HERE / 'frozen' / 'dictionaries.json').read_text())
    A = frozen['alphabet']
    train = load('train')
    singles = [bytes([b]) for b in sorted({b for r in train for b in r})]
    ex = HERE / 'out' / 'exact'
    orders = {
        'bpe': [bytes.fromhex(h) for h in frozen['dictionaries']['bpe-K4096']][A:],
        'token (lazy)': [bytes.fromhex(h) for h in frozen['dictionaries']['token-K4096']][A:],
        'open (exact)': chain(ex / 'exact-entry-s1-whole.txt')[len(singles):],
        'closed (exact)': chain(ex / 'exact-closed-s1-whole.txt')[len(singles):],
        'gain per byte (exact)': chain(ex / 'exact-byte-s1-whole.txt')[len(singles):],
        'normalized + 2-problem support (exact)': chain(ex / 'exact-norm-p2-nowhole.txt')[len(singles):],
    }
    out = {'note': 'development only; coverage on scored sets is post hoc', 'sizes': SIZES, 'leverage': {}, 'coverage': {}}
    with Pool(8, initializer=init, initargs=(train,)) as pool:
        for name, order in orders.items():
            vals = pool.map(leverage, [singles + order[:m] for m in SIZES])
            out['leverage'][name] = [round(v, 4) for v in vals]
            print(f'{name:40}', ' '.join(f'{v:.3f}' for v in vals), flush=True)
    for name in SETS:
        if name == 'train':
            continue
        out['coverage'][name] = {'status': SETS[name][2], 'share': round(coverage(load(name), train), 4)}
        print('coverage', name, out['coverage'][name], flush=True)
    (HERE / 'out' / 'dev-predictors.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
