#!/usr/bin/env python3
"""Development check only: exact minimum token counts on the training and
development (CodeNet `secondary`) files for engine chains, at a grid of sizes.

Reads no test set. Uses the frozen objective-holdout-v1 parser (bits_oh).

    python3 dev_eval.py --chains DIR --out FILE [--sets train,dev]
"""
import argparse
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
OH = LITERALS / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

GRID = [84, 200, 400, 600, 900, 1200, 1408, 1700, 2000, 2350, 2700, 3300, 3924]


def chain_entries(path):
    out = []
    for line in Path(path).read_text().splitlines():
        p = line.split()
        if p and p[0] == 'E':
            out.append(bytes.fromhex(p[5]))
    return out


def load_set(name):
    spec = json.loads((OH / 'frozen' / 'sets' / f'{name}.json').read_text())
    return [(LITERALS / f['path']).read_bytes() for f in spec['files']]


_DOCS = None


def _init(docs):
    global _DOCS
    _DOCS = docs


def _tokens(entries):
    d = B.Dictionary(entries)
    total = 0
    singles_used = 0
    for raw in _DOCS:
        syms = B.parse_tokens(d.edges(raw))
        total += len(syms)
        singles_used += sum(1 for s in syms if s == d.ESC or len(d.entries[s]) == 1)
    return total, singles_used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--chains', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--sets', default='train,dev')
    ap.add_argument('--arms', default='bpe,token,closed')
    ap.add_argument('--jobs', type=int, default=8)
    args = ap.parse_args()
    train = load_set('train')
    singles = [bytes([b]) for b in sorted({b for raw in train for b in raw})]
    orders = {}
    for arm in args.arms.split(','):
        e = chain_entries(Path(args.chains) / f'{arm}.txt')
        if e[:len(singles)] != singles:
            raise SystemExit(f'{arm}: chain does not start with the training alphabet')
        orders[arm] = e[len(singles):]
    result = {'grid': GRID, 'alphabet': len(singles), 'tokens': {}, 'single_byte_tokens': {}}
    for name in args.sets.split(','):
        docs = train if name == 'train' else load_set(name)
        with Pool(args.jobs, initializer=_init, initargs=(docs,)) as pool:
            for arm, order in orders.items():
                rows = pool.map(_tokens, [singles + order[:m] for m in GRID])
                result['tokens'].setdefault(arm, {})[name] = [r[0] for r in rows]
                result['single_byte_tokens'].setdefault(arm, {})[name] = [r[1] for r in rows]
                print(name, arm, [r[0] for r in rows], flush=True)
    Path(args.out).write_text(json.dumps(result, indent=1) + '\n')


if __name__ == '__main__':
    main()
