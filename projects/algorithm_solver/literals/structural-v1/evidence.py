"""Write evidence/results.json from the private run: aggregates, counts and hashes only.

  evidence.py --work DIR [--run DIR/structural/run-v1]"""
import argparse, hashlib, json, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path)
    a = ap.parse_args(); run = a.run or a.work / 'structural/run-v1'
    raw = (run / 'results.json').read_bytes(); r = json.loads(raw)
    c = sha((HERE / 'contract.json').read_bytes()); assert r['contract_sha256'] == c and r['smoke_trials'] is None
    audit = json.loads((a.work / 'structural/audit.json').read_text())
    arms = {x['arm']: x for x in r['arms']}
    pairs = {}
    for w in (128, 256):
        for p in ('O', 'Om', 'R'):
            L, T = arms[f'L-{p}-{w}'], arms[f'T-{p}-{w}']
            d = [T['per_problem'][k] - L['per_problem'][k] for k in L['per_problem']]
            pairs[f'{p}-{w}'] = {'L': L['devval']['selections'], 'T': T['devval']['selections'],
                                 'change': T['devval']['selections'] / L['devval']['selections'] - 1,
                                 'per_problem': {'fewer': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'more': sum(x > 0 for x in d),
                                                 'min': min(d), 'max': max(d), 'median': statistics.median(d)}}
    out = {'contract_sha256': c, 'results_sha256': sha(raw), 'seconds': r['seconds'],
           'audit_sha256': sha((a.work / 'structural/audit.json').read_bytes()),
           'audit': {p: {k: v[k] for k in ('admissible', 'support_problems', 'instances', 'near_whole_rejected', 'guard_rejections')}
                     for p, v in audit['pools'].items()},
           'arms': r['arms'], 'pairs': pairs}
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(json.dumps(pairs, indent=1))


if __name__ == '__main__':
    main()
