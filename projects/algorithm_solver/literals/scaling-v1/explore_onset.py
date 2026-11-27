#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Does the point where the open chain starts buying single-problem fragments predict K*?

    python3 -I explore_onset.py LABEL LIST_DIR CHAIN_DIR OPEN_PREFIX SCALING_JSON SIZES...

For each training size, the support of each open fragment is the number of distinct training problems whose text
contains it (training files only). K_t is the first k at which at least a share t of the 200 fragments ending at k
have support 1. Compares K_t with K* from SCALING_JSON. Writes out/dev-onset-{LABEL}.json.
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TS = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7)
WIN = 200


def unit_of(path):
    m = re.search(r'/(p\d+)_', path)
    return m.group(1) if m else Path(path).stem


def main():
    label, ldir, cdir, prefix, sj = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], json.loads(Path(sys.argv[5]).read_text())
    out = {'note': 'development only', 'window': WIN, 'thresholds': TS, 'sizes': {}}
    for n in [int(x) for x in sys.argv[6:]]:
        units = collections.defaultdict(list)
        for p in (ldir / f'u{n}.list').read_text().split():
            units[unit_of(p)].append(Path(p).read_bytes())
        frags = [bytes.fromhex(ln.split()[5]) for ln in (cdir / f'{prefix}-u{n}.txt').read_text().splitlines()
                 if ln.startswith('E ') and len(ln.split()) == 6 and len(ln.split()[5]) > 2]
        texts = list(units.values())
        sup = [sum(1 for t in texts if any(f in r for r in t)) for f in frags]
        one = [s == 1 for s in sup]
        k_t = {}
        for t in TS:
            k_t[t] = None
            run = sum(one[:WIN])
            for k in range(WIN, len(one) + 1):
                if k > WIN:
                    run += one[k - 1] - one[k - 1 - WIN]
                if run >= t * WIN:
                    k_t[t] = k
                    break
        ks = sj['sizes'][str(n)]['k_star']
        out['sizes'][str(n)] = {'k_star': ks, 'k_t': {str(t): v for t, v in k_t.items()},
                                'ratio': {str(t): (round(v / ks, 3) if v else None) for t, v in k_t.items()}}
        print(f'n={n} K*={ks} ' + ' '.join(f't{t}:{v}({v / ks:.2f})' if v else f't{t}:-' for t, v in k_t.items()), flush=True)
    (HERE / 'out' / f'dev-onset-{label}.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
