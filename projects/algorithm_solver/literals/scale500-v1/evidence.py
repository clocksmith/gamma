"""Write evidence/results.json from the private run: aggregates, counts and hashes only.

  evidence.py --work DIR [--run DIR/scale500/run-v1]

Sources, sequences and dictionaries stay private; this keeps their SHA-256, per-problem selection
counts, chosen variant names, M1 metrics and the rewrite qualification rows (id, hash, bytes, cases,
parity checks used)."""
import argparse, hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path)
    a = ap.parse_args(); run = a.run or a.work / 'scale500/run-v1'; s = a.work / 'scale500'
    raw = (run / 'results.json').read_bytes(); results = json.loads(raw)
    contract_sha = sha((HERE / 'contract.json').read_bytes()); assert results['contract_sha256'] == contract_sha
    assert results['smoke_trials'] is None
    arms = []
    for r in results['arms']:
        folder = run / r['arm']; m = json.loads((folder / 'manifest.json').read_text())
        dictionary = json.loads((folder / 'dictionary.json').read_text())
        assert len(m['programs']) == 500 and len(list(folder.glob('*.ltv'))) == 500
        arms.append({**{k: r[k] for k in r if k not in ('per_problem', 'chosen')},
                     'dictionary_sha256': m['dictionary_sha256'], 'manifest_sha256': sha((folder / 'manifest.json').read_bytes()),
                     'packets_verified': len(m['programs']), 'whole_program_literals': m['metrics']['whole_program_literals'],
                     'longest_entry_bytes': max(len(e.encode()) for e in dictionary),
                     'entries_by_provenance': m['metrics']['entries_by_provenance'],
                     'per_problem': r['per_problem'], 'chosen': r['chosen']})
    rewrites = []
    for f in sorted((s / 'qualification').glob('*.json'), key=lambda p: int(p.stem)):
        q = json.loads(f.read_text())
        used = sum(1 for line in (s / 'checks' / f'{q["id"]}.jsonl').read_text().splitlines() if line.strip()) \
            if (s / 'checks' / f'{q["id"]}.jsonl').exists() else 0
        rewrites.append({'id': q['id'], 'passed': q['passed'], 'sha256': q['sha256'], 'bytes': q['bytes'], 'cases': q['checks'],
                         'parity_checks_used': used, 'failure': q['failure']})
    out = {'contract_sha256': contract_sha, 'results_sha256': sha(raw), 'seconds': results['seconds'],
           'rewrites': {'qualified': sum(r['passed'] for r in rewrites), 'submitted': len(rewrites),
                        'bytes': sum(r['bytes'] for r in rewrites if r['passed']), 'rows': rewrites},
           'arms': arms}
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(f"{len(arms)} arms, {out['rewrites']['qualified']}/{out['rewrites']['submitted']} rewrites")


if __name__ == '__main__':
    main()
