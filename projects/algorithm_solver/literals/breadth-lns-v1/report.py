"""Public evidence for breadth-lns-v1 (FREEZE.md readiness and predictions B1-B6). Written before validation opened.

  report.py --work DIR --run DIR/breadth-lns/run-v1    writes evidence/results.json (aggregates, IDs, hashes)

Each arm is replayed independently: its sealed dictionary is re-read and checked against the fit seal, and all 400
programs are re-measured through the canonical codec; every per-program row the decisions use comes from that replay
and must equal the arm's own report. A missing arm or nonzero exit is kept under failed_arms.
"""
import argparse, hashlib, json, math, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
import analyze, breadth, selection as sel
sha = lambda raw: hashlib.sha256(raw).hexdigest()
q = lambda xs, f: xs[math.ceil(f * len(xs)) - 1]


def summary(rows, ids, db):
    sels = sorted(rows[str(p)]['selections'] for p in ids); acts = sorted(rows[str(p)]['actions'] for p in ids); n = sum(sels)
    dist = lambda xs: {'total': sum(xs), 'median': statistics.median(xs), 'p90': q(xs, .9), 'p95': q(xs, .95), 'worst': xs[-1],
                       'within_32': sum(x <= 32 for x in xs), 'within_96': sum(x <= 96 for x in xs)}
    return {'selections': dist(sels), 'actions': dist(acts),
            'single_character_fraction': sum(rows[str(p)]['single_characters'] for p in ids) / n,
            'package_bytes': db + sum(rows[str(p)]['packet_bytes'] for p in ids), 'dictionary_bytes': db}


def paired(a, b, ids):
    d = [a[str(p)]['actions'] - b[str(p)]['actions'] for p in ids]
    return {'better': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'worse': sum(x > 0 for x in d)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path, required=True); a = ap.parse_args()
    c = breadth.contract(); res = json.loads((a.run / 'results.json').read_text())
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes())
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text())
    assert sha((LIT / 'cost-decomposition-v1/contract.json').read_bytes()) == c['parent_contract_sha256']
    fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    texts = analyze.load_sources(a.work, parent)
    assert sorted(texts) == sorted(fit_ids + val_ids)
    forbidden = sel.forbidden_strings({p: texts[p] for p in fit_ids}) | sel.forbidden_strings({p: texts[p] for p in val_ids})
    pin = parent['dictionaries']['8']; raw = (a.work / pin['relative_path']).read_bytes(); assert sha(raw) == pin['sha256']
    p_rows, p_ill, p_db = sel.measure(texts, json.loads(raw), 8, forbidden); assert not p_ill
    exit_codes = dict(zip(breadth.ARMS, res['exit_codes'])) if isinstance(res['exit_codes'], list) else res['exit_codes']
    out = {'schema': 'gamma.breadth-lns-v1.evidence.v1', 'contract_sha256': res['contract_sha256'],
           'results_sha256': sha((a.run / 'results.json').read_bytes()), 'exit_codes': exit_codes,
           'pinned': {'fit': summary(p_rows, fit_ids, p_db), 'validation': summary(p_rows, val_ids, p_db)},
           'decoder_dependency_bytes': {rel: (LIT / rel).stat().st_size for rel in ('literals.py', 'pass2/working/bitpack.py')},
           'offline_encoder_bytes': {rel: (LIT / rel).stat().st_size for rel in ('breadth-lns-v1/breadth.py', 'lagrange-select-v2/selection.py',
                                                                                 'cost-decomposition-v1/analyze.py', 'tail-search-v1/structure.cjs')},
           'arms': {}, 'failed_arms': {}}
    present = {x['arm']: x for x in res['arms']}; replays = {}
    for name in breadth.ARMS:
        if name not in present or exit_codes.get(name) != 0:
            out['failed_arms'][name] = {'exit_code': exit_codes.get(name), 'results_present': name in present}; continue
        arm = present[name]; folder = a.run / name
        draw = (folder / 'dictionary.json').read_bytes(); seal = json.loads((folder / 'fit-seal.json').read_text())
        assert sha(draw) == seal['dictionary_sha256'] == arm['dictionary_sha256'] and seal['validation_loaded'] is False, name
        vocab = json.loads(draw); assert len(vocab) <= 256
        rows, ill, db = sel.measure(texts, vocab, 8, forbidden)
        va = arm['validation_arm']
        assert db == va['dictionary_bytes'] and ill == va['illegal_entry_sha256'], name
        assert {str(p): rows[str(p)]['actions'] for p in val_ids} == {str(k): v for k, v in va['per_problem_actions'].items()}, name
        assert sum(rows[str(p)]['selections'] for p in fit_ids) == arm['final_fit'] == arm['fit_selections_arm'], name
        assert arm['decoded_arm'] == arm['decoded_pinned'] == len(rows) == 400
        pv = arm['validation_pinned']; assert pv['per_problem_actions'] == {str(p): p_rows[str(p)]['actions'] for p in val_ids}
        replays[name] = rows
        s = summary(rows, val_ids, db); pr = paired(rows, p_rows, val_ids); ps = out['pinned']['validation']
        ready = {'decoded_100': all(str(p) in rows for p in val_ids), 'audit_clean': not ill,
                 'actions_5pct': s['actions']['total'] <= 0.95 * ps['actions']['total'],
                 'median_lower': s['actions']['median'] < ps['actions']['median'], 'p90_lower': s['actions']['p90'] < ps['actions']['p90'],
                 'improved_60': pr['better'] >= 60, 'worsened_25': pr['worse'] <= 25,
                 'fraction_not_higher': s['single_character_fraction'] <= ps['single_character_fraction'],
                 'package_105': s['package_bytes'] <= 1.05 * ps['package_bytes']}
        out['arms'][name] = {**{k: arm[k] for k in ('moves', 'accepted_moves', 'lns_seconds', 'start_fit', 'final_fit', 'final_objective',
                                                    'fit_programs_worse_than_start', 'fit_programs_better_than_start', 'statuses', 'dictionary_sha256')},
                             'fit': summary(rows, fit_ids, db), 'validation': s, 'paired_vs_pinned': pr, 'readiness': ready, 'ready': all(ready.values()),
                             'per_problem_validation_actions': {str(p): rows[str(p)]['actions'] for p in val_ids}}
    if 'unweighted' in replays:
        for name in out['arms']:
            out['arms'][name]['paired_vs_unweighted'] = paired(replays[name], replays['unweighted'], val_ids)
    A = out['arms']; have = lambda *ns: all(n in A for n in ns)
    out['predictions'] = {
        'B1': abs(A['unweighted']['final_fit'] - 25268) <= 0.01 * 25268 if have('unweighted') else None,
        'B2': (A['nonregress']['fit_programs_worse_than_start'] == 0 and A['nonregress']['paired_vs_pinned']['worse'] < A['unweighted']['paired_vs_pinned']['worse'])
              if have('nonregress', 'unweighted') else None,
        'B3': A['relative']['validation']['actions']['median'] < A['unweighted']['validation']['actions']['median'] if have('relative', 'unweighted') else None,
        'B4': all(A[n]['start_fit'] - A[n]['final_fit'] < A['unweighted']['start_fit'] - A['unweighted']['final_fit'] for n in ('nonregress', 'relative'))
              if have('nonregress', 'relative', 'unweighted') else None,
        'B5': not any(v['ready'] for v in A.values()) if A else None,
        'B6': (not out['failed_arms'] and all(v['readiness']['decoded_100'] and v['readiness']['audit_clean'] for v in A.values())) if A else False}
    (HERE / 'evidence').mkdir(exist_ok=True); (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for k, v in A.items():
        print(k, v['final_fit'], v['validation']['actions']['total'], v['validation']['actions']['median'], v['validation']['actions']['p90'],
              v['paired_vs_pinned'], v['ready'])
    print('pinned', out['pinned']['validation']['actions']['total'], 'failed', out['failed_arms'], out['predictions'])


if __name__ == '__main__':
    main()
