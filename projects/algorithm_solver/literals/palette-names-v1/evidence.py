"""Public evidence and the frozen decision rules for palette-names-v1 (FREEZE.md).

  evidence.py --work DIR --run DIR/palette-names/run-v1    writes evidence/results.json (aggregates, IDs, hashes)
"""
import argparse, hashlib, json, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(LIT / 'cost-decomposition-v1')]
import analyze
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def summary(rows, ids, db):
    acts = sorted(rows[str(p)]['actions'] for p in ids); sel = sum(rows[str(p)]['selections'] for p in ids)
    return {'actions': sum(acts), 'median': statistics.median(acts), 'p90': acts[-(-9 * len(acts) // 10) - 1],
            'p95': acts[-(-19 * len(acts) // 20) - 1], 'worst': acts[-1], 'within_32': sum(a <= 32 for a in acts), 'within_96': sum(a <= 96 for a in acts),
            'single_character_codes': sum(rows[str(p)]['single_characters'] for p in ids),
            'single_character_fraction': sum(rows[str(p)]['single_characters'] for p in ids) / sel,
            'source_bytes': sum(rows[str(p)]['source_bytes'] for p in ids),
            'package_bytes': db + sum(rows[str(p)]['packet_bytes'] for p in ids)}


def paired(a, b, ids):
    d = [a[str(p)]['actions'] - b[str(p)]['actions'] for p in ids]
    return {'better': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'worse': sum(x > 0 for x in d)}


def ready(c, b, pr):
    return {'actions_5pct': c['actions'] <= 0.95 * b['actions'], 'median_lower': c['median'] < b['median'], 'p90_lower': c['p90'] < b['p90'],
            'improved_60': pr['better'] >= 60, 'worsened_25': pr['worse'] <= 25,
            'fraction_not_higher': c['single_character_fraction'] <= b['single_character_fraction'], 'package_105': c['package_bytes'] <= 1.05 * b['package_bytes']}


def incremental(c, b, pr):
    return {'fewer_actions': c['actions'] < b['actions'], 'median_not_worse': c['median'] <= b['median'], 'p90_not_worse': c['p90'] <= b['p90'],
            'fraction_not_higher': c['single_character_fraction'] <= b['single_character_fraction'], 'worsened_25': pr['worse'] <= 25,
            'package_105': c['package_bytes'] <= 1.05 * b['package_bytes']}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path, required=True); a = ap.parse_args()
    c = json.loads((HERE / 'contract.json').read_text()); res = json.loads((a.run / 'results.json').read_text())
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes())
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    # Pinned R baseline: original sources under the pinned L-R-256 dictionary.
    pin = parent['dictionaries']['8']; vocab = json.loads((a.work / pin['relative_path']).read_text())
    assert sha((a.work / pin['relative_path']).read_bytes()) == pin['sha256']
    val = analyze.load_sources(a.work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    db = analyze.dictionary_bytes(vocab); base_rows = {}
    for pid, t in val.items():
        seq = analyze.shortest_encode(t, vocab); pk = analyze.encode(vocab, seq, 8); assert analyze.decode(db, pk) == t
        base_rows[str(pid)] = {'actions': len(seq) + 1, 'selections': len(seq), 'single_characters': sum(len(vocab[i]) == 1 for i in seq),
                               'packet_bytes': len(pk), 'source_bytes': len(t.encode())}
    arms = {r['arm']: r for r in res['arms']}
    out = {'schema': 'gamma.palette-names-v1.evidence.v1', 'contract_sha256': res['contract_sha256'], 'results_sha256': sha((a.run / 'results.json').read_bytes()),
           'pinned_R': summary(base_rows, val_ids, len(db)), 'arms': {}}
    for name, r in arms.items():
        all_q = all(r['qualification'][str(p)]['passed'] for p in fit_ids + val_ids)
        s = summary(r['per_problem'], val_ids, r['dictionary_bytes'])
        row = {'validation': s, 'fit': summary(r['per_problem'], fit_ids, r['dictionary_bytes']), 'rounds': r['rounds'],
               'validation_rewrite': r['validation_rewrite'], 'qualified': r['qualified'], 'all_qualified': all_q,
               'illegal_entry_sha256': r['illegal_entry_sha256'], 'dictionary_sha256': r['dictionary_sha256'],
               'per_problem_validation_actions': {str(p): r['per_problem'][str(p)]['actions'] for p in val_ids}}
        pr = paired(r['per_problem'], base_rows, val_ids); row['paired_vs_R'] = pr
        row['ready_vs_R'] = {**ready(s, out['pinned_R'], pr), 'qualified_clean': all_q and not r['illegal_entry_sha256']}
        out['arms'][name] = row
    for name, control in (('palette_fixed', 'az_fixed'), ('palette_joint', 'az_joint'), ('az_fixed', None), ('az_joint', None)):
        row = out['arms'][name]; s = row['validation']; checks = {'ready_vs_R': all(row['ready_vs_R'].values())}
        for comp in ('seed',) + ((control,) if control else ()):
            pr = paired(arms[name]['per_problem'], arms[comp]['per_problem'], val_ids)
            row[f'paired_vs_{comp}'] = pr
            checks.update({f'{k}_vs_{comp}': v for k, v in incremental(s, out['arms'][comp]['validation'], pr).items()})
        row['successor_checks'] = checks; row['successor'] = all(checks.values()) and name.startswith('palette')
    cands = [n for n in ('palette_fixed', 'palette_joint') if out['arms'][n]['successor']]
    out['selected_successor'] = min(cands, key=lambda n: (out['arms'][n]['validation']['actions'], out['arms'][n]['validation']['package_bytes'], n)) if cands else None
    (HERE / 'evidence').mkdir(exist_ok=True)
    (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for n, r in out['arms'].items():
        v = r['validation']; print(n, v['actions'], v['median'], v['p90'], round(v['single_character_fraction'], 4), r.get('successor'), r['qualified'])
    print('selected', out['selected_successor'])


if __name__ == '__main__':
    main()
