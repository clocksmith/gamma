#!/usr/bin/env python3
"""Score the frozen closure-holdout-v1 dictionaries. Run by the scorer.

    python3 -I score.py --out out/

Sets: train, dev (objective-holdout-v1 `secondary`), fresh and project (the
objective-holdout-v1 test sets, already used: reported as replication only),
and the new sets fresh2, project-python and project-javascript (decisive).
For every set, arm and cap: exact minimum tokens with the frozen
objective-holdout-v1 parser (an escaped byte is one token), single-byte or
escaped tokens, and the equal-size grid. Per unit: paired comparisons and a
two-sided sign test (ties dropped). Then the decision rules of
PREREGISTRATION.md. Writes out/results.json and out/per-file.csv.
"""
import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from math import comb
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
OH = LITERALS / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

DICTIONARIES_SHA256 = '4f2d4410f6e6a841fbd01783ec9a0f03498f40f356d9f2996642debe0ba543b7'  # frozen dictionaries; checked before scoring
ARMS = ('bpe', 'token', 'closed')
CAPS = (256, 4096)
GRID = [84, 200, 400, 600, 900, 1200, 1408, 1700, 2000, 2350, 2700, 3300, 3924]
SETS = {
    'train': (OH / 'frozen' / 'sets' / 'train.json', LITERALS, 'used'),
    'dev': (OH / 'frozen' / 'sets' / 'dev.json', LITERALS, 'used'),
    'fresh': (OH / 'sets' / 'fresh.json', OH, 'used'),
    'project': (OH / 'sets' / 'project.json', OH, 'used'),
    'fresh2': (HERE / 'sets' / 'fresh2.json', HERE, 'new'),
    'project-python': (HERE / 'sets' / 'project-python.json', HERE, 'new'),
    'project-javascript': (HERE / 'sets' / 'project-javascript.json', HERE, 'new'),
}
THRESHOLD = 1.0


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def sign_test(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


_DOCS = None


def _init(docs):
    global _DOCS
    _DOCS = docs


def _per_file(entries):
    d = B.Dictionary(entries)
    rows = []
    for raw in _DOCS:
        syms = B.parse_tokens(d.edges(raw))
        rows.append((len(syms), sum(1 for s in syms if s == d.ESC or len(d.entries[s]) == 1)))
    return rows


def load(name):
    spec_path, root, _ = SETS[name]
    spec = json.loads(spec_path.read_text())
    docs, files = [], []
    for f in spec['files']:
        raw = (root / f['path']).read_bytes()
        if sha256(raw) != f['sha256']:
            raise SystemExit(f'{name}: hash mismatch {f["path"]}')
        docs.append(raw)
        files.append(f)
    return docs, files


def pct(a, b):
    return round(100.0 * (a / b - 1.0), 2)


def paired(units, x, y):
    """x lower than y counts as a win for x."""
    tx, ty = defaultdict(int), defaultdict(int)
    for u, a, b in zip(units, x, y):
        tx[u] += a
        ty[u] += b
    w = sum(1 for u in tx if tx[u] < ty[u])
    l_ = sum(1 for u in tx if tx[u] > ty[u])
    t = len(tx) - w - l_
    return {'lower': w, 'higher': l_, 'tied': t, 'sign_p': sign_test(w, l_)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(HERE / 'out'))
    ap.add_argument('--jobs', type=int, default=8)
    ap.add_argument('--sets', default=','.join(SETS))
    args = ap.parse_args()
    blob = (HERE / 'frozen' / 'dictionaries.json').read_bytes()
    if DICTIONARIES_SHA256 is None or sha256(blob) != DICTIONARIES_SHA256:
        raise SystemExit('frozen dictionaries missing or changed')
    frozen = json.loads(blob)
    dicts = {k: [bytes.fromhex(h) for h in v] for k, v in frozen['dictionaries'].items()}
    alphabet = frozen['alphabet']
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    results = {'sets': {}, 'dictionaries_sha256': DICTIONARIES_SHA256}
    csv_rows = []
    for name in args.sets.split(','):
        docs, files = load(name)
        units = [f['unit'] for f in files]
        res = {'status': SETS[name][2], 'files': len(docs), 'units': len(set(units)),
               'bytes': sum(map(len, docs)), 'caps': {}, 'grid': {}}
        with Pool(args.jobs, initializer=_init, initargs=(docs,)) as pool:
            jobs = [(arm, cap) for cap in CAPS for arm in ARMS]
            per = dict(zip(jobs, pool.map(_per_file, [dicts[f'{a}-K{c}'] for a, c in jobs])))
            for arm in ARMS:
                big = dicts[f'{arm}-K4096']
                grid = pool.map(_per_file, [big[:alphabet + m] for m in GRID])
                res['grid'][arm] = {'tokens': [sum(r[0] for r in g) for g in grid],
                                    'single_byte_tokens': [sum(r[1] for r in g) for g in grid]}
        for cap in CAPS:
            tok = {a: [r[0] for r in per[(a, cap)]] for a in ARMS}
            one = {a: [r[1] for r in per[(a, cap)]] for a in ARMS}
            c = {'tokens': {a: sum(tok[a]) for a in ARMS},
                 'single_byte_share': {a: round(sum(one[a]) / sum(tok[a]), 4) for a in ARMS}}
            for x, y in (('closed', 'token'), ('closed', 'bpe'), ('token', 'bpe')):
                c[f'{x}_vs_{y}'] = {'percent': pct(c['tokens'][x], c['tokens'][y]), **paired(units, tok[x], tok[y])}
            res['caps'][str(cap)] = c
            for i, f in enumerate(files):
                csv_rows.append([name, cap, f['path'], f['unit'], f['lang'], len(docs[i])]
                                + [tok[a][i] for a in ARMS] + [one[a][i] for a in ARMS])
        results['sets'][name] = res
        k4, k2 = res['caps']['4096'], res['caps']['256']
        print(f'{name}: K4096 closed vs token {k4["closed_vs_token"]["percent"]:+.2f}%, closed vs bpe '
              f'{k4["closed_vs_bpe"]["percent"]:+.2f}%; K256 closed vs token {k2["closed_vs_token"]["percent"]:+.2f}%, '
              f'closed vs bpe {k2["closed_vs_bpe"]["percent"]:+.2f}%', flush=True)

    if 'fresh2' in results['sets']:
        f2 = results['sets']['fresh2']['caps']
        rules = {}
        s = f2['4096']['closed_vs_token']
        rules['S'] = s['percent'] <= -THRESHOLD and s['lower'] > s['higher'] and s['sign_p'] < 0.05
        o = f2['4096']['closed_vs_bpe']
        rules['O'] = o['percent'] <= -THRESHOLD and o['lower'] > o['higher'] and o['sign_p'] < 0.05
        p = f2['256']['closed_vs_token']
        rules['P'] = p['percent'] >= THRESHOLD and p['higher'] > p['lower'] and p['sign_p'] < 0.05
        rules['F'] = f2['4096']['single_byte_share']['closed'] < f2['4096']['single_byte_share']['token']
        g = results['sets']['fresh2']['grid']
        rules['G'] = all(a <= b for a, b in zip(g['closed']['tokens'], g['bpe']['tokens']))
        for lang in ('python', 'javascript'):
            name = f'project-{lang}'
            if name in results['sets']:
                j = results['sets'][name]['caps']['4096']['closed_vs_token']
                rules[f'J-{lang}'] = j['percent'] <= -THRESHOLD and j['lower'] > j['higher'] and j['sign_p'] < 0.05
        results['rules'] = rules
        print('rules:', json.dumps(rules))
    (out / 'results.json').write_text(json.dumps(results, indent=1) + '\n')
    with open(out / 'per-file.csv', 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['set', 'cap', 'path', 'unit', 'lang', 'bytes'] + [f'tokens_{a}' for a in ARMS]
                   + [f'single_{a}' for a in ARMS])
        w.writerows(csv_rows)


if __name__ == '__main__':
    main()
