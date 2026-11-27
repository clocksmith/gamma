#!/usr/bin/env python3
"""DEVELOPMENT ONLY. Does K* (from out/dev-scaling-*.json) track the number of strings that recur across training
problems? Counts distinct strings of 2..16 bytes occurring in at least m distinct training problems, for each nested
training size, from the training lists alone (no dev data, no dictionary).

    python3 -I explore_support_count.py LABEL LIST_DIR SCALING_JSON SIZES...

Writes out/dev-support-count-{LABEL}.json.
"""
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MS = (2, 3, 4, 5, 6, 8, 10, 12, 16)


def unit_of(path):
    m = re.search(r'/(p\d+)_', path)  # CodeNet problem id
    return m.group(1) if m else Path(path).stem  # catalogue: numeric problem id


def main():
    label, ldir, sj = sys.argv[1], Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text())
    sizes = [int(x) for x in sys.argv[4:]]
    out = {'note': 'development only; counts from training files only', 'm': MS, 'sizes': {}}
    for n in sizes:
        by_unit = collections.defaultdict(set)
        for p in (ldir / f'u{n}.list').read_text().split():
            raw = Path(p).read_bytes()
            s = by_unit[unit_of(p)]
            for i in range(len(raw)):
                for j in range(i + 2, min(len(raw), i + 16) + 1):
                    s.add(raw[i:j])
        cnt = collections.Counter()
        for s in by_unit.values():
            cnt.update(s)
        counts = {m: sum(1 for c in cnt.values() if c >= m) for m in MS}
        k = sj['sizes'][str(n)]['k_star']
        out['sizes'][str(n)] = {'problems': len(by_unit), 'k_star': k, 'strings_in_at_least_m_problems': counts,
                                'ratio_to_k_star': {m: round(c / k, 3) for m, c in counts.items()}}
        print(f'n={n} problems={len(by_unit)} K*={k} ' + ' '.join(f'm{m}:{counts[m]}({counts[m] / k:.2f})' for m in MS), flush=True)
    (HERE / 'out' / f'dev-support-count-{label}.json').write_text(json.dumps(out, indent=1) + '\n')


if __name__ == '__main__':
    main()
