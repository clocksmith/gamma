#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Where does exact open token gain cross BPE on dev, as the training set grows?

    python3 -I explore_scaling.py LABEL DEV_SET_JSON DEV_ROOT CHAIN_DIR OPEN_PREFIX SIZES...

For each training size n (chains bpe-u{n}.txt and {OPEN_PREFIX}-u{n}.txt in CHAIN_DIR, trained on the matching list
u{n}.list), counts tokens on the dev set (paths in DEV_SET_JSON relative to DEV_ROOT) with the exact parser for each
rule's first k fragments. K* is the
smallest k on a 50-fragment grid from which open uses more dev tokens than BPE at every larger grid point, refined to
10 fragments; None if open never stays above BPE. Also reports training bytes per fragment slot at K*.
Writes out/dev-scaling-{LABEL}.json.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
OH = LIT / 'objective-holdout-v1'
GAMMA = HERE.parents[3]
sys.path.insert(0, str(OH))
import bits_oh as B  # noqa: E402

_DEV = None


def read(path):
    return [bytes.fromhex(ln.split()[5]) for ln in Path(path).read_text().splitlines() if ln.startswith('E ') and len(ln.split()) == 6]


def split(chain):
    singles = [e for e in chain if len(e) == 1]
    frags = [e for e in chain if len(e) > 1]
    return singles, frags


def init(dev):
    global _DEV
    _DEV = dev


def tokens(entries):
    d = B.Dictionary(entries)
    return sum(len(B.parse_tokens(d.edges(r))) for r in _DEV)


def main():
    label, dev_set, dev_root, cdir, prefix = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]), sys.argv[5]
    sizes = [int(x) for x in sys.argv[6:]]
    dev = [(dev_root / f['path']).read_bytes() for f in json.loads(dev_set.read_text())['files']]
    out = {'note': 'development only: nested training subsets scored on a dev set', 'label': label, 'dev_set': str(dev_set),
           'open_chain': prefix, 'sizes': {}}
    with Pool(8, initializer=init, initargs=(dev,)) as pool:
        for n in sizes:
            sb, fb = split(read(cdir / f'bpe-u{n}.txt'))
            so, fo = split(read(cdir / f'{prefix}-u{n}.txt'))
            assert set(sb) == set(so), 'singleton inventories differ'
            train_bytes = sum(Path(p).stat().st_size for p in (cdir / f'u{n}.list').read_text().split())
            top = min(len(fb), len(fo))
            cache = {}

            def score(ks):
                need = [k for k in ks if k not in cache]
                res = pool.map(tokens, [sb + fb[:k] for k in need] + [so + fo[:k] for k in need])
                for i, k in enumerate(need):
                    cache[k] = (res[i], res[len(need) + i])
                return [cache[k] for k in ks]

            grid = sorted({k for k in range(50, top + 1, 50)} | {84, top})
            vals = score(grid)
            above = [o > b for b, o in vals]
            kstar = None
            for i in range(len(grid)):
                if all(above[i:]):
                    kstar = grid[i]
                    break
            if kstar is not None and grid.index(kstar) > 0:
                lo = grid[grid.index(kstar) - 1]
                fine = list(range(lo + 10, kstar, 10))
                for k, (b, o) in zip(fine, score(fine)):
                    if o > b:
                        kstar = k
                        break
            out['sizes'][str(n)] = {
                'train_bytes': train_bytes, 'alphabet': len(sb), 'fragments_available': top,
                'k_star': kstar, 'train_bytes_per_slot_at_k_star': round(train_bytes / kstar, 1) if kstar else None,
                'grid': {str(k): {'bpe': cache[k][0], 'open': cache[k][1], 'open_vs_bpe_pct': round(100 * (cache[k][1] / cache[k][0] - 1), 2)} for k in sorted(cache)}}
            s = out['sizes'][str(n)]
            print(f'n={n} train_bytes={train_bytes} K*={kstar} bytes/slot={s["train_bytes_per_slot_at_k_star"]} '
                  f'@84 {s["grid"]["84"]["open_vs_bpe_pct"]:+.1f}% @{top} {s["grid"][str(top)]["open_vs_bpe_pct"]:+.1f}%', flush=True)
    (HERE / 'out').mkdir(exist_ok=True)
    (HERE / 'out' / f'dev-scaling-{label}.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
