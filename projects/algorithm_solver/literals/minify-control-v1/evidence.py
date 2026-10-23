"""Write evidence/results.json from the private run: aggregates, counts and hashes only.

  evidence.py --work DIR [--run DIR/minify/run-v1]

Keeps per-evaluation M1 metrics, per-problem selection counts, dictionary and manifest hashes, the search
arms' trials and stop reasons, the minified-source qualification rows (id, hashes, bytes, cases) and the
O -> Om -> R decompositions. Sources, dictionaries and sequences stay private."""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    import control
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path)
    a = ap.parse_args(); run = a.run or a.work / 'minify/run-v1'
    raw = (run / 'results.json').read_bytes(); r = json.loads(raw)
    contract_sha = sha((HERE / 'contract.json').read_bytes()); assert r['contract_sha256'] == contract_sha and r['smoke_trials'] is None
    evaluations = []
    for e in r['evaluations']:
        folder = run / e['name']; m = json.loads((folder / 'manifest.json').read_text())
        assert len(m['programs']) == e['report']['problems'] == len(list(folder.glob('*.ltv')))
        evaluations.append({**e, 'dictionary_sha256': m['dictionary_sha256'], 'manifest_sha256': sha((folder / 'manifest.json').read_bytes()),
                            'packets_verified': len(m['programs'])})
    sel = {(f, w): {(e['dictionary'], e['pool']): e['report']['selections'] for e in evaluations if e['fit'] == f and e['width'] == w}
           for f in ('F500', 'Fdev') for w in (7, 8)}
    decomposition = {f'{f}-{2 ** w}': {f'{x}->{y}': control.decompose(s, x, y) for x, y in (('O', 'Om'), ('Om', 'R'), ('O', 'R'))}
                     for (f, w), s in sel.items()}
    receipt = json.loads((a.work / 'minify/receipt.json').read_text())
    out = {'contract_sha256': contract_sha, 'results_sha256': sha(raw), 'seconds': r['seconds'],
           'om': {'qualified': receipt['passed'], 'rows': [{k: x[k] for k in ('id', 'passed', 'sha256', 'bytes', 'original_sha256', 'original_bytes', 'checks')}
                                                          for x in receipt['rows']]},
           'search': r['search'], 'evaluations': evaluations, 'decomposition': decomposition}
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    print(len(evaluations), 'evaluations,', sum(e['packets_verified'] for e in evaluations), 'packets')
    print(json.dumps(decomposition['F500-256'], indent=1))


if __name__ == '__main__':
    main()
