"""Public evidence and the frozen decision rules for widenbhd-v1 (FREEZE.md).

  evidence.py --work DIR --run DIR/widenbhd/run-v1    writes evidence/results.json (aggregates, IDs, hashes)
"""
import argparse, hashlib, json, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
import math
import analyze, selection as sel
import run as succ
sha = lambda raw: hashlib.sha256(raw).hexdigest()
q = lambda xs, f: xs[math.ceil(f * len(xs)) - 1]


def rows_for(texts, vocab):
    rows, illegal, db = succ.measure_safe(texts, vocab, 8, sel.forbidden_strings(texts))
    return rows, db, illegal


def summary(rows, ids, db):
    sels = sorted(rows[str(p)]['selections'] for p in ids); acts = sorted(rows[str(p)]['actions'] for p in ids); n = sum(sels)
    return {'selections': {'total': n, 'median': statistics.median(sels), 'p90': q(sels, .9), 'p95': q(sels, .95), 'worst': sels[-1],
                           'within_32': sum(s <= 32 for s in sels), 'within_96': sum(s <= 96 for s in sels)},
            'actions': sum(acts), 'median': statistics.median(acts), 'p90': q(acts, .9), 'p95': q(acts, .95),
            'single_character_fraction': sum(rows[str(p)]['single_characters'] for p in ids) / n,
            'package_bytes': db + sum(rows[str(p)]['packet_bytes'] for p in ids)}


def invariant_violation(recon):
    """The nonregression caps are the experiment's invariant: a completed arm with any fit program worse is rejected."""
    return {'fit_programs_worse_than_start': recon['fit_programs_worse_than_start']} if recon['fit_programs_worse_than_start'] > 0 else None


def record_time_comparison(path, arm, s, rows, val_ids, sha_expected):
    """Incremental predicates against the current best recorded at THIS stage's record time (AMENDMENT-1).
    Returns None (replacement unresolved) unless the comparator's evidence is hash-bound and carries compatible
    per-program validation actions and aggregates."""
    try:
        raw = Path(path).read_bytes(); assert sha(raw) == sha_expected
        cb = json.loads(raw)['arms'][arm]; v = cb['validation']
        crow = {str(p): {'actions': cb['per_problem_validation_actions'][str(p)]} for p in val_ids}
        cs = {'actions': v['actions'], 'median': v['median'], 'p90': v['p90'], 'single_character_fraction': v['single_character_fraction'],
              'package_bytes': v['package_bytes']}
        assert cs['actions'] == sum(r['actions'] for r in crow.values())
    except Exception as ex:
        return {'resolved': False, 'reason': f'{type(ex).__name__}: {ex}'[:200]}
    pr = paired(rows, crow, val_ids)
    checks = {'fewer_actions': s['actions'] < cs['actions'], 'median_not_worse': s['median'] <= cs['median'], 'p90_not_worse': s['p90'] <= cs['p90'],
              'fraction_not_higher': s['single_character_fraction'] <= cs['single_character_fraction'], 'worsened_25': pr['worse'] <= 25,
              'package_105': s['package_bytes'] <= 1.05 * cs['package_bytes']}
    return {'resolved': True, 'evidence': str(path), 'arm': arm, 'evidence_sha256': sha_expected, 'paired': pr, 'checks': checks, 'passes': all(checks.values())}


def replacement(a, cands, out, replays, val_ids, rank):
    if a.record_time_best is None or not a.record_time_arm or not a.record_time_sha256:
        return {'resolved': False, 'replacement_allowed': False, 'selected': None, 'reason': 'no explicit record-time binding'}
    per = {k: record_time_comparison(a.record_time_best, a.record_time_arm, out['arms'][k]['validation'], replays[k], val_ids, a.record_time_sha256)
           for k in cands}
    if any(not v.get('resolved') for v in per.values()):
        return {'resolved': False, 'replacement_allowed': False, 'selected': None, 'per_candidate': per, 'reason': 'comparator unresolved'}
    ok = [k for k in cands if per[k]['passes']]
    return {'resolved': True, 'per_candidate': per, 'eligible': ok, 'replacement_allowed': bool(ok), 'selected': min(ok, key=rank) if ok else None}


def exists(full, pred, n_arms=2):
    """Existential prediction over arms: True if any fully replayed arm satisfies it; False only if every arm fully
    replayed and none does; otherwise None (an unobserved or failed arm cannot establish the negative)."""
    if any(pred(k) for k in full): return True
    return False if len(full) == n_arms else None


def predictions(A, full, failed):  # FREEZE.md K1-K6 (AMENDMENT-1: three-valued existential predictions)
    both = len(full) == 2
    return {'K1': exists(full, lambda k: A[k]['accepted_moves'] >= 3),
            'K2': A['k120']['statuses'].get('13', 0) > A['k80']['statuses'].get('13', 0) if both else None,
            'K3': exists(full, lambda k: A[k]['start_fit'] - A[k]['final_fit'] > 5),
            'K4': exists(full, lambda k: A[k]['successor']),
            'K5': all(A[k]['fit_programs_worse_than_start'] == 0 and A[k]['dev_val_worse_than_seed'] <= 5 for k in full) if both else None,
            'K6': both and not failed}


def paired(a, b, ids):
    d = [a[str(p)]['actions'] - b[str(p)]['actions'] for p in ids]
    return {'better': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'worse': sum(x > 0 for x in d)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--record-time-best', type=Path, help='evidence of the current best recorded at record time, if not item 43')
    ap.add_argument('--record-time-arm'); ap.add_argument('--record-time-sha256'); a = ap.parse_args()
    c = succ.contract(); res = json.loads((a.run / 'results.json').read_text())  # verifies code, runtime and parent hashes first
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes())
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text()); fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    seed_vocab, allsrc = succ.load_seed(a.work, c, 'all')
    seed_rows, seed_db, ill = rows_for(allsrc, seed_vocab); assert not ill
    pin = parent['dictionaries']['8']; pvocab = json.loads((a.work / pin['relative_path']).read_text())
    assert sha((a.work / pin['relative_path']).read_bytes()) == pin['sha256']
    original = analyze.load_sources(a.work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    r_rows, r_db, ill = rows_for(original, pvocab); assert not ill
    # Sources are item 13's own (unchanged), so their qualification is item 13's/15's receipts by exact hash.
    assert sha((LIT / c['qualification_receipt']).read_bytes()) == c['qualification_receipt_sha256']
    qual = json.loads((LIT / c['qualification_receipt']).read_text())
    q13 = next(x for x in qual['arms'] if x['arm'] == 'scope_joint' and x['width'] == 8)
    assert all(q13['per_problem'][str(p)]['source_sha256'] == sha(allsrc[p].encode()) for p in fit_ids + val_ids)
    all_q = all(q13['qualification'][str(p)]['passed'] for p in fit_ids + val_ids)
    # Current best at freeze time (item 24 optional), a published comparator only: its per-program actions and aggregates.
    cb = c['current_best']; assert sha((LIT / cb['evidence']).read_bytes()) == cb['evidence_sha256']
    cba = json.loads((LIT / cb['evidence']).read_text())['arms'][cb['arm']]  # item 43 evidence: arms keyed by name
    cb_rows = {str(p): {'actions': cba['per_problem_validation_actions'][str(p)]} for p in val_ids}
    cbv = cba['validation']
    cb_sum = {'actions': cbv['actions'], 'median': cbv['median'], 'p90': cbv['p90'],
              'single_character_fraction': cbv['single_character_fraction'], 'package_bytes': cbv['package_bytes']}
    assert cb_sum['actions'] == sum(r['actions'] for r in cb_rows.values())
    out = {'schema': 'gamma.widenbhd-v1.evidence.v1', 'contract_sha256': res['contract_sha256'], 'results_sha256': sha((a.run / 'results.json').read_bytes()),
           'qualification_reused': c['qualification_receipt'], 'all_sources_qualified_by_receipt': all_q,
           'pinned_R': summary(r_rows, val_ids, r_db), 'seed': summary(seed_rows, val_ids, seed_db),
           'current_best': {'evidence': cb['evidence'], 'arm': cb['arm'], **cb_sum}, 'exit_codes': res['exit_codes'],
           'decoder_dependency_bytes': {rel: (LIT / rel).stat().st_size for rel in ('literals.py', 'pass2/working/bitpack.py')},
           'offline_encoder_bytes': {rel: (LIT / rel).stat().st_size for rel in ('widenbhd-v1/run.py', 'widenbhd-v1/capped.py', 'seeded-repair-v1/model.py', 'breadth-lns-v1/breadth.py',
                                                                                 'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py',
                                                                                 'tail-search-v1/structure.cjs')},
           'arms': {}, 'failed_arms': {}}
    present = {x['arm']: x for x in res['arms']}; replays = {}
    for name in succ.ARMS:
        # A missing arm or a nonzero exit is a retained failure, never silently dropped from the evidence.
        if name not in present or res['exit_codes'].get(name) != 0:
            out['failed_arms'][name] = {'exit_code': res['exit_codes'].get(name), 'results_present': name in present}; continue
        arm = present[name]; folder = a.run / name
        # Independent replay: re-read the sealed dictionary, check it against the fit seal, and re-measure all 400 sources.
        raw = (folder / 'dictionary.json').read_bytes(); seal = json.loads((folder / 'fit-seal.json').read_text())
        assert sha(raw) == seal['dictionary_sha256'] == arm['dictionary_sha256'] and seal['validation_loaded'] is False
        vocab = json.loads(raw); assert len(vocab) <= 256
        replay, replay_db, replay_illegal = rows_for(allsrc, vocab); replays[name] = replay
        assert replay_illegal == arm['illegal_entry_sha256'] and replay_db == arm['dictionary_bytes'] and replay == {str(k): v for k, v in arm['per_problem'].items()}, name
        covered = {'fit': sum(replay[str(p)]['encodable'] for p in fit_ids), 'validation': sum(replay[str(p)]['encodable'] for p in val_ids)}
        assert arm['decoded'] == covered['fit'] + covered['validation'] and len(replay) == 400
        if covered != {'fit': 300, 'validation': 100}:
            # Incomplete coverage is a retained failure: no cohort totals, no readiness, no successor.
            out['arms'][name] = {'coverage': covered, 'unencodable_ids': sorted(int(p) for p, r in replay.items() if not r['encodable']),
                                 'ready_vs_R': {'coverage_400': False}, 'successor': False, 'new_current_best': False,
                                 'dictionary_sha256': arm['dictionary_sha256']}
            continue
        rows = replay; s = summary(rows, val_ids, replay_db); f = summary(rows, fit_ids, replay_db)
        # Reconcile every reported counter with the replay and with the retained move log; never copy one unchecked.
        fit_sel = {p: rows[str(p)]['selections'] for p in fit_ids}; seed_sel = {p: seed_rows[str(p)]['selections'] for p in fit_ids}
        recon = {'start_fit': sum(seed_sel.values()), 'final_fit': sum(fit_sel.values()), 'final_objective': sum(fit_sel.values()),
                 'fit_programs_worse_than_start': sum(fit_sel[p] > seed_sel[p] for p in fit_ids),
                 'fit_programs_better_than_start': sum(fit_sel[p] < seed_sel[p] for p in fit_ids)}
        mv = [json.loads(line) for line in (a.run / f'{name}-live' / 'moves.jsonl').read_text().splitlines()]
        recon.update(moves=len(mv), accepted_moves=sum(m['accepted'] for m in mv), improving_moves=sum(m['accepted'] for m in mv),
                     feasible_moves=sum(m['feasible'] for m in mv), optimal_moves=sum(m['optimal'] for m in mv),
                     statuses={str(x): sum(m['model_status'] == x for m in mv) for x in sorted({m['model_status'] for m in mv})})
        assert all(recon[k] == arm[k] for k in recon), {k: (recon[k], arm[k]) for k in recon if recon[k] != arm[k]}
        bad = invariant_violation(recon)
        if bad:
            out['failed_arms'][name] = {'nonregression_invariant_violated': bad}; continue
        assert all(m['warm'] and m['feasible'] for m in mv)  # both arms are warm-started; a lost incumbent fails closed
        pr_r, pr_s = paired(rows, r_rows, val_ids), paired(rows, seed_rows, val_ids)
        ready = {'actions_5pct': s['actions'] <= 0.95 * out['pinned_R']['actions'], 'median_lower': s['median'] < out['pinned_R']['median'],
                 'p90_lower': s['p90'] < out['pinned_R']['p90'], 'improved_60': pr_r['better'] >= 60, 'worsened_25': pr_r['worse'] <= 25,
                 'fraction_not_higher': s['single_character_fraction'] <= out['pinned_R']['single_character_fraction'],
                 'package_105': s['package_bytes'] <= 1.05 * out['pinned_R']['package_bytes'], 'qualified_clean': all_q and not replay_illegal,
                 'decoded_400': arm['decoded'] == 400}
        inc = {'fewer_actions': s['actions'] < out['seed']['actions'], 'median_not_worse': s['median'] <= out['seed']['median'],
               'p90_not_worse': s['p90'] <= out['seed']['p90'], 'fraction_not_higher': s['single_character_fraction'] <= out['seed']['single_character_fraction'],
               'worsened_25': pr_s['worse'] <= 25, 'package_105': s['package_bytes'] <= 1.05 * out['seed']['package_bytes']}
        pr_c = paired(rows, cb_rows, val_ids)
        vs_cb = {'fewer_actions': s['actions'] < cb_sum['actions'], 'median_not_worse': s['median'] <= cb_sum['median'],
                 'p90_not_worse': s['p90'] <= cb_sum['p90'], 'fraction_not_higher': s['single_character_fraction'] <= cb_sum['single_character_fraction'],
                 'worsened_25': pr_c['worse'] <= 25, 'package_105': s['package_bytes'] <= 1.05 * cb_sum['package_bytes']}
        out['arms'][arm['arm']] = {**recon, 'coverage': covered, 'lns_seconds': arm['lns_seconds'], 'dictionary_sha256': arm['dictionary_sha256'],
                                   'illegal_entry_sha256': replay_illegal, 'decoded': len(replay),
                                   'dev_val_worse_than_seed': pr_s['worse'],
                                   'fit': f, 'validation': s, 'paired_vs_R': pr_r, 'paired_vs_seed': pr_s, 'paired_vs_current_best': pr_c, 'ready_vs_R': ready,
                                   'incremental_vs_seed': inc, 'incremental_vs_current_best': vs_cb,
                                   'successor': all(ready.values()) and all(inc.values()),
                                   'new_current_best': all(ready.values()) and all(inc.values()) and all(vs_cb.values()),
                                   'per_problem_validation_actions': {str(p): rows[str(p)]['actions'] for p in val_ids}}
    cands = [k for k, v in out['arms'].items() if v['successor']]
    assert out['seed']['actions'] == 8285, 'seed must reproduce item 43 nonregress'
    out['replayed_arms'] = sorted(out['arms'])
    full = [k for k in ('k80', 'k120') if k in out['arms'] and out['arms'][k].get('coverage') == {'fit': 300, 'validation': 100}]
    if len(full) == 2:
        out['k80_vs_k120'] = {'validation': paired(replays['k80'], replays['k120'], val_ids), 'fit': paired(replays['k80'], replays['k120'], fit_ids)}
    A = out['arms']
    ok = lambda n: n in full
    out['predictions'] = predictions(A, full, out['failed_arms'])
    rank = lambda k: (out['arms'][k]['validation']['actions'], out['arms'][k]['validation']['package_bytes'], k)
    out['selected_successor'] = min(cands, key=rank) if cands else None
    best = [k for k in cands if out['arms'][k]['new_current_best']]
    out['selected_new_current_best'] = min(best, key=rank) if best else None
    # AMENDMENT-1: replacing the M1-GAP current-best row needs an EXPLICIT record-time binding (also when item 43 is still
    # current). Every frozen-rule successor is checked against it before ranking; a missing binding leaves replacement unresolved.
    out['record_time_best'] = replacement(a, cands, out, replays, val_ids, rank)
    (HERE / 'evidence').mkdir(exist_ok=True); (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for k, v in out['arms'].items():
        if 'validation' not in v: print(k, 'coverage failure', v['coverage']); continue
        print(k, v['validation']['actions'], v['validation']['median'], v['validation']['p90'], v['paired_vs_seed'], v['successor'])
    print('seed', out['seed']['actions'], 'selected', out['selected_successor'], 'new current best', out['selected_new_current_best'],
          'failed', out['failed_arms'], out['predictions'])


if __name__ == '__main__':
    main()
