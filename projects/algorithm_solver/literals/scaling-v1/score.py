#!/usr/bin/env python3
"""Confirmatory scoring (PREREGISTRATION.md). Measures K* on the sealed catalogue test pool (decides) and on the
catalogue dev set (secondary) for the confirmatory sizes, then applies the frozen criteria to out/predictions.json.

    python3 -I score.py CHAIN_DIR

Writes out/dev-scaling-test-confirm.json, out/dev-scaling-dev-confirm.json and out/test-results.json.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GAMMA = HERE.parents[3]
SIZES = ('800', '1600', '2269')
TOL = 0.20


def main():
    cdir = sys.argv[1]
    pred = json.loads((HERE / 'out' / 'predictions.json').read_text())['sizes']
    for label, s in (('test-confirm', 'sets/catalogue-test.json'), ('dev-confirm', 'sets/catalogue-dev.json')):
        subprocess.run([sys.executable, '-I', str(HERE / 'explore_scaling.py'), label, str(HERE / s), str(GAMMA), cdir, 'open', *SIZES], check=True)
    meas = {lab: json.loads((HERE / 'out' / f'dev-scaling-{lab}.json').read_text())['sizes'] for lab in ('test-confirm', 'dev-confirm')}
    res = {'tolerance': TOL, 'sizes': {}, 'criteria': {}}
    err = {'onset': [], 'B1': [], 'B2': []}
    for n in SIZES:
        k = meas['test-confirm'][n]['k_star']
        row = {'test_k_star': k, 'dev_k_star': meas['dev-confirm'][n]['k_star']}
        for p in ('onset', 'B1', 'B2'):
            v = pred[n][f'{p}_prediction']
            e = abs(math.log(v / k)) if v and k else math.inf
            row[p] = {'prediction': v, 'error_pct': round(100 * (v / k - 1), 1) if v and k else None}
            err[p].append(e)
        res['sizes'][n] = row
    res['criteria']['onset_within_tolerance_at_every_size'] = all(e <= math.log(1 + TOL) for e in err['onset'])
    mean = {p: sum(v) / len(v) for p, v in err.items()}
    res['mean_abs_log_error'] = {p: round(v, 4) for p, v in mean.items()}
    res['criteria']['onset_beats_B1'] = mean['onset'] < mean['B1']
    res['passed'] = all(res['criteria'].values())
    res['reported_not_decisive'] = {'onset_beats_B2': mean['onset'] < mean['B2']}
    (HERE / 'out' / 'test-results.json').write_text(json.dumps(res, indent=1) + '\n')
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main()
