#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Scores the DEV-BUNDLE.md arms against the tolerance fixed in that file before any run.

    python3 -I explore_bundle.py CHAIN_DIR

CHAIN_DIR holds the chains named in ARMS (open is read from out/exact/). Training tokens come from each chain's
E lines (exact shortest-path parse of the training files after that entry). Dev tokens are description only.
Writes out/dev-bundle.json.
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

ALPHA = 171
SLOTS = (84, 3924)
BYTES = (566, 43480)  # open's fragment bytes at 84 and 3,924 fragments
TOL = 1.02
ARMS = {'open': 'EXACT/exact-entry-s1-whole.txt', 'pair': 'pair-ext.txt', 'bundle': 'bundle-slot.txt',
        'open-byte': 'open-byte-ext.txt', 'pair-byte (lazy)': 'lazy-pair-byte.txt', 'bundle-byte': 'bundle-byte.txt',
        'lazy-pair (calibration)': 'lazy-pair.txt', 'pair-byte (exact, partial run)': 'pair-byte.txt'}
CLOSED = ('pair', 'bundle', 'pair-byte (lazy)', 'bundle-byte', 'lazy-pair (calibration)', 'pair-byte (exact, partial run)')


def closed_ok(rows):
    seen = set()
    for _, _, e in rows:
        if len(e) > 1 and not any(e[:i] in seen and e[i:] in seen for i in range(1, len(e))):
            return False
        seen.add(e)
    return True
_DEV = None


def read(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if line.startswith('E ') and len(f) == 6:
            rows.append((int(f[2]), int(f[3]), bytes.fromhex(f[5])))
    return rows


def init(dev):
    global _DEV
    _DEV = dev


def dev_tokens(entries):
    d = B.Dictionary(entries)
    return sum(len(B.parse_tokens(d.edges(r))) for r in _DEV)


def main():
    cdir = Path(sys.argv[1])
    chains = {a: read(HERE / 'out' / 'exact' / p[6:] if p.startswith('EXACT/') else cdir / p) for a, p in ARMS.items()}
    alpha_bytes = chains['open'][ALPHA - 1][0]
    for a in CLOSED:
        assert closed_ok(chains[a]), f'{a} chain has an entry that is not two earlier entries'
    out = {'closure_checked': list(CLOSED), 'note': 'development only; decision on training tokens; dev tokens are description', 'tolerance': TOL,
           'slots': {}, 'bytes': {}, 'chains': {a: {'entries': len(c) - ALPHA, 'fragment_bytes': c[-1][0] - alpha_bytes} for a, c in chains.items()}}
    picks = []
    for k in SLOTS:
        ref = chains['open'][ALPHA + k - 1][1]
        row = {}
        for a, c in chains.items():
            if len(c) >= ALPHA + k:
                t = c[ALPHA + k - 1][1]
                row[a] = {'train_tokens': t, 'vs_open_pct': round(100 * (t / ref - 1), 2), 'match': t <= TOL * ref,
                          'fragment_bytes': c[ALPHA + k - 1][0] - alpha_bytes}
                picks.append((a, 'slots', k, ALPHA + k))
        out['slots'][str(k)] = {'reference': ref, 'arms': row}
    for b in BYTES:
        row, ref = {}, None
        for a, c in chains.items():
            n = max((i + 1 for i, r in enumerate(c) if r[0] - alpha_bytes <= b), default=0)
            if n <= ALPHA or c[-1][0] - alpha_bytes < b:  # chain did not reach the budget
                continue
            row[a] = {'train_tokens': c[n - 1][1], 'fragments': n - ALPHA, 'fragment_bytes': c[n - 1][0] - alpha_bytes}
            picks.append((a, 'bytes', b, n))
        ref = min(row[a]['train_tokens'] for a in ('open', 'open-byte') if a in row)
        for a in row:
            row[a]['vs_reference_pct'] = round(100 * (row[a]['train_tokens'] / ref - 1), 2)
            row[a]['match'] = row[a]['train_tokens'] <= TOL * ref
        out['bytes'][str(b)] = {'reference': ref, 'arms': row}
    dev = [(LIT / f['path']).read_bytes() for f in json.loads((OH / 'frozen/sets/dev.json').read_text())['files']]
    with Pool(8, initializer=init, initargs=(dev,)) as pool:
        toks = pool.map(dev_tokens, [[r[2] for r in chains[a][:n]] for a, _, _, n in picks])
    bpe = {}
    fz = json.loads((HERE / 'frozen' / 'dictionaries.json').read_text())
    bpe_order = [bytes.fromhex(h) for h in fz['dictionaries']['bpe-K4096']]
    init(dev)
    for k in SLOTS:
        bpe[k] = dev_tokens(bpe_order[:ALPHA + k])
    for (a, kind, x, n), t in zip(picks, toks):
        cell = out[kind][str(x)]['arms'][a]
        cell['dev_tokens'] = t
        if kind == 'slots':
            cell['dev_vs_bpe_pct'] = round(100 * (t / bpe[x] - 1), 2)
    out['dev_bpe_tokens'] = {str(k): v for k, v in bpe.items()}
    (HERE / 'out' / 'dev-bundle.json').write_text(json.dumps(out, indent=1) + '\n')
    for kind in ('slots', 'bytes'):
        for x, v in out[kind].items():
            print(f'{kind} {x}: reference {v["reference"]}')
            for a, c in v['arms'].items():
                print(f'   {a:24} train {c["train_tokens"]:>7} ({c.get("vs_open_pct", c.get("vs_reference_pct")):+.2f}%) match={c["match"]} '
                      f'dev {c["dev_tokens"]}' + (f' ({c["dev_vs_bpe_pct"]:+.2f}% vs BPE)' if 'dev_vs_bpe_pct' in c else f' frags {c["fragments"]}'))


if __name__ == '__main__':
    main()
