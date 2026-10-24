"""Public evidence and the frozen decision rules for python-nonregress-v1 (FREEZE.md).

  evidence.py --work DIR --run DIR/python-nonregress/run-v1    writes evidence/results.json (aggregates, IDs, hashes)
"""
import argparse, hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(HERE)]
import run
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def summary(ev, split):
    s = ev[split]
    if s['actions'] is None: return None
    return {'covered': s['covered'], 'problems': s['problems'], 'actions': s['actions']['total'], 'median': s['actions']['median'],
            'p90': s['actions']['p90'], 'selections': s['selections'], 'single_character_fraction': s['single_character_fraction'],
            'package_bytes': s['package_bytes']}


def paired(a, b, ids):
    d = [a[str(p)]['actions'] - b[str(p)]['actions'] for p in ids]
    return {'better': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'worse': sum(x > 0 for x in d)}


def incremental(s, base, pr, worse_max):
    return {'fewer_actions': s['actions'] < base['actions'], 'median_not_worse': s['median'] <= base['median'], 'p90_not_worse': s['p90'] <= base['p90'],
            'fraction_not_higher': s['single_character_fraction'] <= base['single_character_fraction'], 'worsened_max': pr['worse'] <= worse_max,
            'package_105': s['package_bytes'] <= 1.05 * base['package_bytes']}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path, required=True); a = ap.parse_args()
    c = run.contract(); res = json.loads((a.run / 'results.json').read_text()); cm = run.common()
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes())
    fit_ids, val_ids = c['partition']['dev_fit'], c['partition']['dev_val']; work = a.work.resolve(); g = c['gates']
    out = {'schema': 'gamma.python-nonregress-v1.evidence.v1', 'contract_sha256': res['contract_sha256'],
           'results_sha256': sha((a.run / 'results.json').read_bytes()), 'exit_codes': res['exit_codes'], 'arms': {}, 'failed_arms': {}}
    present = {x['arm']: x for x in res['arms']}
    for name in run.ARMS:
        if name not in present or res['exit_codes'].get(name) != 0:
            out['failed_arms'][name] = {'exit_code': res['exit_codes'].get(name), 'results_present': name in present}; continue
        arm = present[name]; width = int(name[1:]); inp = c['inputs'][str(width)]; folder = a.run / name
        raw = (folder / 'dictionary.json').read_bytes(); seal = json.loads((folder / 'fit-seal.json').read_text())
        assert sha(raw) == seal['dictionary_sha256'] == arm['dictionary_sha256'] and seal['validation_loaded'] is False
        vocab = json.loads(raw)
        texts = {str(k): v for k, v in run.checked(work, inp['sources']).items()}
        original = {str(k): v for k, v in run.checked(work, inp['original_sources']).items()}
        # Independent replay through the same evaluator, then the matched references.
        ev = cm.evaluate(texts, vocab, width, c); assert ev == arm['evaluation'], name
        ev_seed = cm.evaluate(texts, run.checked(work, inp['seed_dictionary']), width, c)
        ev_R = cm.evaluate(original, run.checked(work, inp['baseline_dictionary']), width, c)
        cm.authority(c, width, 'scope_joint', texts)  # every source passes item 31's receipt by exact hash
        # Reconcile reported counters with the replay and the retained move log.
        fit_sel = {p: ev['per_problem'][str(p)]['selections'] for p in fit_ids}
        seed_sel = {p: ev_seed['per_problem'][str(p)]['selections'] for p in fit_ids}
        mv = [json.loads(l) for l in (a.run / f'{name}-live' / 'moves.jsonl').read_text().splitlines()]
        recon = {'start_fit': sum(seed_sel.values()), 'final_fit': sum(fit_sel.values()),
                 'fit_programs_worse_than_start': sum(fit_sel[p] > seed_sel[p] for p in fit_ids),
                 'fit_programs_better_than_start': sum(fit_sel[p] < seed_sel[p] for p in fit_ids),
                 'moves': len(mv), 'accepted_moves': sum(m['accepted'] for m in mv), 'feasible_moves': sum(m['feasible'] for m in mv),
                 'optimal_moves': sum(m['optimal'] for m in mv),
                 'statuses': {str(x): sum(m['model_status'] == x for m in mv) for x in sorted({m['model_status'] for m in mv})}}
        assert all(recon[k] == arm[k] for k in recon), {k: (recon[k], arm[k]) for k in recon if recon[k] != arm[k]}
        assert all(m['warm'] and m['feasible'] for m in mv)
        if recon['fit_programs_worse_than_start'] > 0:
            out['failed_arms'][name] = {'nonregression_invariant_violated': recon['fit_programs_worse_than_start']}; continue
        covered = ev['fit']['covered'] == len(fit_ids) and ev['validation']['covered'] == len(val_ids)
        s, s_seed, s_R = summary(ev, 'validation'), summary(ev_seed, 'validation'), summary(ev_R, 'validation')
        row = {**recon, 'width': width, 'dictionary_sha256': arm['dictionary_sha256'], 'coverage': {'fit': ev['fit']['covered'], 'validation': ev['validation']['covered']},
               'illegal_entry_sha256': ev['illegal_entry_sha256'], 'validation': s, 'seed_validation': s_seed, 'R_validation': s_R,
               'fit': summary(ev, 'fit'), 'seed_fit': summary(ev_seed, 'fit')}
        if not covered or s is None:
            row.update(ready_vs_R={'coverage': False}, successor=False); out['arms'][name] = row; continue
        pr_R = paired(ev['per_problem'], ev_R['per_problem'], val_ids); pr_seed = paired(ev['per_problem'], ev_seed['per_problem'], val_ids)
        ready = {'coverage_qualified_legal': covered and not ev['illegal_entry_sha256'], 'actions_5pct': s['actions'] <= (1 - g['ready_action_fraction']) * s_R['actions'],
                 'median_lower': s['median'] < s_R['median'], 'p90_lower': s['p90'] < s_R['p90'], 'improved_min': pr_R['better'] >= g['improved_min'],
                 'worsened_max': pr_R['worse'] <= g['worsened_max'], 'fraction_not_higher': s['single_character_fraction'] <= s_R['single_character_fraction'],
                 'package_105': s['package_bytes'] <= 1.05 * s_R['package_bytes']}
        inc = incremental(s, s_seed, pr_seed, g['worsened_max'])
        row.update(paired_vs_R=pr_R, paired_vs_seed=pr_seed, ready_vs_R=ready, incremental_vs_seed=inc,
                   ready=all(ready.values()), incremental=all(inc.values()), successor=all(ready.values()) and all(inc.values()),
                   per_problem_validation_actions={str(p): ev['per_problem'][str(p)]['actions'] for p in val_ids})
        out['arms'][name] = row
    A = out['arms']; full = [k for k in run.ARMS if k in A and 'paired_vs_seed' in A[k]]
    exists = lambda pred: True if any(pred(k) for k in full) else (False if len(full) == len(run.ARMS) else None)
    out['predictions'] = {  # FREEZE.md Y1-Y5, three-valued where existential
        'Y1': exists(lambda k: A[k]['accepted_moves'] >= 1),
        'Y2': exists(lambda k: A[k]['validation']['actions'] < A[k]['seed_validation']['actions'] and A[k]['paired_vs_seed']['worse'] == 0),
        'Y3': (not any(A[k]['ready'] for k in full)) if len(full) == len(run.ARMS) else (False if any(A[k]['ready'] for k in full) else None),
        'Y4': len(full) == len(run.ARMS) and all(A[k]['coverage'] == {'fit': len(fit_ids), 'validation': len(val_ids)} for k in full),
        'Y5': len(full) == len(run.ARMS) and all(not A[k]['illegal_entry_sha256'] for k in full)}
    (HERE / 'evidence').mkdir(exist_ok=True); (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for k, v in A.items():
        if 'paired_vs_seed' in v:
            print(k, v['validation']['actions'], 'seed', v['seed_validation']['actions'], 'R', v['R_validation']['actions'], v['paired_vs_seed'], 'ready', v['ready'], 'incremental', v['incremental'])
        else: print(k, 'incomplete', v.get('coverage'))
    print('failed', out['failed_arms'], out['predictions'])


if __name__ == '__main__':
    main()
