"""Public evidence and the frozen decision rules for jsratiocap-v1 (FREEZE.md).

  evidence.py --work DIR --run DIR/jsratiocap/run-v1 [--record-time-best EVIDENCE --record-time-arm ARM --record-time-sha256 H]
  writes evidence/results.json (aggregates, IDs, hashes)
"""
import argparse, hashlib, json, math, statistics, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
sys.path[:0] = [str(HERE), str(LIT / 'breadth-lns-v1'), str(LIT / 'lagrange-select-v2'), str(LIT / 'cost-decomposition-v1'), str(LIT), str(LIT / 'pass2/working')]
import analyze, selection as sel
import run as succ
sha = lambda raw: hashlib.sha256(raw).hexdigest()
q = lambda xs, f: xs[math.ceil(f * len(xs)) - 1]
PAIRS = (('k40ratio', 'k40lex'), ('k24ratio', 'k24lex'))


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


def paired(a, b, ids):
    d = [a[str(p)]['actions'] - b[str(p)]['actions'] for p in ids]
    return {'better': sum(x < 0 for x in d), 'same': sum(x == 0 for x in d), 'worse': sum(x > 0 for x in d)}


def incremental(s, ref, pr):
    return {'fewer_actions': s['actions'] < ref['actions'], 'median_not_worse': s['median'] <= ref['median'], 'p90_not_worse': s['p90'] <= ref['p90'],
            'fraction_not_higher': s['single_character_fraction'] <= ref['single_character_fraction'], 'worsened_25': pr['worse'] <= 25,
            'package_105': s['package_bytes'] <= 1.05 * ref['package_bytes']}


def published(path, arm, digest, val_ids):
    """A published comparator's per-program validation actions and aggregates, bound by its evidence SHA-256."""
    raw = Path(path).read_bytes(); assert sha(raw) == digest, path
    cb = json.loads(raw)['arms'][arm]; v = cb['validation']
    rows = {str(p): {'actions': cb['per_problem_validation_actions'][str(p)]} for p in val_ids}
    agg = {k: v[k] for k in ('actions', 'median', 'p90', 'single_character_fraction', 'package_bytes')}
    assert agg['actions'] == sum(r['actions'] for r in rows.values())
    return rows, agg


def invariant_violations(recon, ratio, seed_fit):
    """Nonregression in every arm; for ratio arms also the aggregate fit-fraction invariant against the seed (each accepted move
    is canonically fraction-nonincreasing, so the end state must satisfy N_seed*C_final <= C_seed*N_final)."""
    bad = {}
    if recon['fit_programs_worse_than_start'] > 0: bad['fit_programs_worse_than_start'] = recon['fit_programs_worse_than_start']
    if ratio and seed_fit[0] * recon['final_characters'] > seed_fit[1] * recon['final_fit']: bad['fit_fraction_rose'] = True
    return bad or None


def replacement(a, cands, out, replays, val_ids, rank):
    """Replacing the M1-GAP current-best row needs an EXPLICIT record-time binding; a missing or unresolvable one leaves it unresolved."""
    if a.record_time_best is None or not a.record_time_arm or not a.record_time_sha256:
        return {'resolved': False, 'replacement_allowed': False, 'selected': None, 'reason': 'no explicit record-time binding'}
    try:
        crow, cs = published(a.record_time_best, a.record_time_arm, a.record_time_sha256, val_ids)
    except Exception as ex:
        return {'resolved': False, 'replacement_allowed': False, 'selected': None, 'reason': f'{type(ex).__name__}: {ex}'[:200]}
    per = {}
    for k in cands:
        pr = paired(replays[k], crow, val_ids); checks = incremental(out['arms'][k]['validation'], cs, pr)
        per[k] = {'paired': pr, 'checks': checks, 'passes': all(checks.values())}
    ok = [k for k in cands if per[k]['passes']]
    return {'resolved': True, 'evidence': str(a.record_time_best), 'arm': a.record_time_arm, 'evidence_sha256': a.record_time_sha256,
            'per_candidate': per, 'eligible': ok, 'replacement_allowed': bool(ok), 'selected': min(ok, key=rank) if ok else None}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--work', type=Path, required=True); ap.add_argument('--run', type=Path, required=True)
    ap.add_argument('--record-time-best', type=Path); ap.add_argument('--record-time-arm'); ap.add_argument('--record-time-sha256'); a = ap.parse_args()
    c = succ.contract(); res = json.loads((a.run / 'results.json').read_text())  # verifies code, runtime and parent hashes first
    assert res['contract_sha256'] == sha((HERE / 'contract.json').read_bytes())
    parent = json.loads((LIT / 'cost-decomposition-v1/contract.json').read_text()); fit_ids, val_ids = parent['partition']['dev_fit'], parent['partition']['dev_val']
    seed_vocab, _, allsrc = succ.load_seed(a.work, c, 'all')
    seed_rows, seed_db, ill = rows_for(allsrc, seed_vocab); assert not ill
    pin = parent['dictionaries']['8']; pvocab = json.loads((a.work / pin['relative_path']).read_text())
    assert sha((a.work / pin['relative_path']).read_bytes()) == pin['sha256']
    original = analyze.load_sources(a.work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    r_rows, r_db, ill = rows_for(original, pvocab); assert not ill
    # Sources are item 13's own (unchanged), so their qualification is item 13's receipts by exact hash.
    assert sha((LIT / c['qualification_receipt']).read_bytes()) == c['qualification_receipt_sha256']
    qual = json.loads((LIT / c['qualification_receipt']).read_text())
    q13 = next(x for x in qual['arms'] if x['arm'] == 'scope_joint' and x['width'] == 8)
    assert all(q13['per_problem'][str(p)]['source_sha256'] == sha(allsrc[p].encode()) for p in fit_ids + val_ids)
    all_q = all(q13['qualification'][str(p)]['passed'] for p in fit_ids + val_ids)
    cb = c['current_best']; cb_rows, cb_sum = published(LIT / cb['evidence'], cb['arm'], cb['evidence_sha256'], val_ids)
    seed_val = summary(seed_rows, val_ids, seed_db)
    # the seed IS item 51 flat: its fresh replay must equal item 51's published validation, per program and in aggregate
    assert all(seed_rows[p]['actions'] == cb_rows[p]['actions'] for p in cb_rows) and all(seed_val[k] == cb_sum[k] for k in cb_sum)
    seed_fit = (sum(seed_rows[str(p)]['selections'] for p in fit_ids), sum(seed_rows[str(p)]['single_characters'] for p in fit_ids))
    out = {'schema': 'gamma.jsratiocap-v1.evidence.v1', 'contract_sha256': res['contract_sha256'], 'results_sha256': sha((a.run / 'results.json').read_bytes()),
           'qualification_reused': c['qualification_receipt'], 'all_sources_qualified_by_receipt': all_q,
           'pinned_R': summary(r_rows, val_ids, r_db), 'seed': seed_val, 'seed_fit': {'selections': seed_fit[0], 'single_characters': seed_fit[1]},
           'current_best': {'evidence': cb['evidence'], 'arm': cb['arm'], **cb_sum}, 'exit_codes': res['exit_codes'],
           'decoder_dependency_bytes': {rel: (LIT / rel).stat().st_size for rel in ('literals.py', 'pass2/working/bitpack.py')},
           'offline_encoder_bytes': {rel: (LIT / rel).stat().st_size for rel in ('jsratiocap-v1/run.py', 'jsratiocap-v1/capped.py', 'seeded-repair-v1/model.py',
                                                                                 'lagrange-select-v2/selection.py', 'cost-decomposition-v1/analyze.py',
                                                                                 'tail-search-v1/structure.cjs')},
           'arms': {}, 'failed_arms': {}}
    assert out['seed']['actions'] == 8283, 'seed must reproduce item 51 flat'
    present = {x['arm']: x for x in res['arms']}; replays = {}
    for name in succ.ARMS:
        # A missing arm or a nonzero exit is a retained failure, never silently dropped from the evidence.
        if name not in present or res['exit_codes'].get(name) != 0:
            out['failed_arms'][name] = {'exit_code': res['exit_codes'].get(name), 'results_present': name in present}; continue
        arm = present[name]; folder = a.run / name; spec = c['arms'][name]
        assert arm['k'] == spec['k'] and arm['ratio'] == spec['ratio']
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
                                 'ready_vs_R': {'coverage_400': False}, 'successor': False, 'dictionary_sha256': arm['dictionary_sha256']}
            continue
        rows = replay; s = summary(rows, val_ids, replay_db); f = summary(rows, fit_ids, replay_db)
        # Reconcile every reported counter with the replay and with the retained move log; never copy one unchecked.
        fit_sel = {p: rows[str(p)]['selections'] for p in fit_ids}; seed_sel = {p: seed_rows[str(p)]['selections'] for p in fit_ids}
        fit_chr = sum(rows[str(p)]['single_characters'] for p in fit_ids)
        recon = {'start_fit': seed_fit[0], 'final_fit': sum(fit_sel.values()), 'final_objective': c['char_scale'] * sum(fit_sel.values()) + fit_chr,
                 'start_characters': seed_fit[1], 'final_characters': fit_chr,
                 'fit_programs_worse_than_start': sum(fit_sel[p] > seed_sel[p] for p in fit_ids),
                 'fit_programs_better_than_start': sum(fit_sel[p] < seed_sel[p] for p in fit_ids)}
        mv = [json.loads(line) for line in (a.run / f'{name}-live' / 'moves.jsonl').read_text().splitlines()]
        recon.update(moves=len(mv), accepted_moves=sum(m['accepted'] for m in mv), ratio_rejections=sum(m['ratio_rejected'] for m in mv),
                     feasible_moves=sum(m['feasible'] for m in mv), optimal_moves=sum(m['optimal'] for m in mv),
                     statuses={str(x): sum(m['model_status'] == x for m in mv) for x in sorted({m['model_status'] for m in mv})})
        assert all(recon[k] == arm[k] for k in recon), {k: (recon[k], arm[k]) for k in recon if recon[k] != arm[k]}
        assert all(m['warm'] and m['feasible'] and m['integral_arcs'] for m in mv)  # warm, binary arcs; a lost incumbent fails closed
        assert spec['ratio'] or recon['ratio_rejections'] == 0
        bad = invariant_violations(recon, spec['ratio'], seed_fit)
        if bad:
            out['failed_arms'][name] = {'invariant_violated': bad}; continue
        pr_r, pr_s = paired(rows, r_rows, val_ids), paired(rows, seed_rows, val_ids)
        ready = {'actions_5pct': s['actions'] <= 0.95 * out['pinned_R']['actions'], 'median_lower': s['median'] < out['pinned_R']['median'],
                 'p90_lower': s['p90'] < out['pinned_R']['p90'], 'improved_60': pr_r['better'] >= 60, 'worsened_25': pr_r['worse'] <= 25,
                 'fraction_not_higher': s['single_character_fraction'] <= out['pinned_R']['single_character_fraction'],
                 'package_105': s['package_bytes'] <= 1.05 * out['pinned_R']['package_bytes'], 'qualified_clean': all_q and not replay_illegal,
                 'decoded_400': arm['decoded'] == 400}
        inc = incremental(s, out['seed'], pr_s)  # the seed is item 51 flat, the current best at freeze time
        out['arms'][name] = {**recon, 'k': spec['k'], 'ratio': spec['ratio'], 'coverage': covered, 'lns_seconds': arm['lns_seconds'],
                             'dictionary_sha256': arm['dictionary_sha256'], 'illegal_entry_sha256': replay_illegal, 'decoded': len(replay),
                             'fit': f, 'validation': s, 'paired_vs_R': pr_r, 'paired_vs_seed': pr_s, 'ready_vs_R': ready, 'incremental_vs_seed': inc,
                             'successor': all(ready.values()) and all(inc.values()),
                             'per_problem_validation_actions': {str(p): rows[str(p)]['actions'] for p in val_ids}}
    full = lambda n: n in out['arms'] and out['arms'][n].get('coverage') == {'fit': 300, 'validation': 100}
    out['ratio_vs_lex'] = {r: {'validation': paired(replays[r], replays[l], val_ids), 'fit': paired(replays[r], replays[l], fit_ids)}
                           for r, l in PAIRS if full(r) and full(l)}
    A = out['arms']; ratios = [r for r, _ in PAIRS]
    def some(names, pred):  # three-valued: None when none of the named arms fully replayed
        done = [n for n in names if full(n)]
        return any(pred(A[n]) for n in done) if done else None
    out['predictions'] = {  # FREEZE.md J1-J6, on replayed and reconciled values only
        'J1': some(ratios, lambda x: x['accepted_moves'] >= 1),
        'J2': some(ratios, lambda x: x['validation']['single_character_fraction'] <= out['seed']['single_character_fraction']),
        'J3': some(ratios, lambda x: x['successor']),
        'J4': all(A[l]['validation']['actions'] <= A[r]['validation']['actions'] for r, l in PAIRS) if all(full(r) and full(l) for r, l in PAIRS) else None,
        'J5': all(full(n) for n in succ.ARMS) and not out['failed_arms'],
        'J6': all(2 * A[n]['optimal_moves'] < A[n]['moves'] for n in ratios) if all(full(n) for n in ratios) else None}
    cands = [k for k, v in A.items() if v['successor']]
    rank = lambda k: (A[k]['validation']['actions'], A[k]['validation']['package_bytes'], k)
    out['replayed_arms'] = sorted(A)
    out['selected_successor'] = min(cands, key=rank) if cands else None
    out['record_time_best'] = replacement(a, cands, out, replays, val_ids, rank)
    (HERE / 'evidence').mkdir(exist_ok=True); (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for k, v in A.items():
        if 'validation' not in v: print(k, 'coverage failure', v['coverage']); continue
        print(k, v['accepted_moves'], v['ratio_rejections'], v['final_fit'], v['final_characters'], v['validation']['actions'],
              round(100 * v['validation']['single_character_fraction'], 3), v['paired_vs_seed'], v['successor'])
    print('seed', out['seed']['actions'], 'selected', out['selected_successor'], 'replacement', out['record_time_best'].get('selected'),
          'failed', out['failed_arms'], out['predictions'])


if __name__ == '__main__':
    main()
