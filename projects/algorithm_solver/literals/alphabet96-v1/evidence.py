"""Public evidence and the frozen decision rules for alphabet96-v1 (FREEZE.md).

  evidence.py --work DIR --run DIR/alphabet96/run-v1 [--record-time-best EVIDENCE --record-time-arm ARM --record-time-sha256 H]
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
    v13 = json.loads((a.work / c['item13_dictionary']).read_bytes()); assert sha((a.work / c['item13_dictionary']).read_bytes()) == c['item13_dictionary_sha256']
    rows13, db13, ill = rows_for(allsrc, v13); assert not ill and all(s in set(v13) for s in sel.ALPHABET)
    pin = parent['dictionaries']['8']; pvocab = json.loads((a.work / pin['relative_path']).read_text())
    assert sha((a.work / pin['relative_path']).read_bytes()) == pin['sha256']
    original = analyze.load_sources(a.work, {**parent, 'sources': [r for r in parent['sources'] if r['id'] in set(val_ids)]})
    r_rows, r_db, ill = rows_for(original, pvocab); assert not ill
    assert sha((LIT / c['qualification_receipt']).read_bytes()) == c['qualification_receipt_sha256']
    qual = json.loads((LIT / c['qualification_receipt']).read_text())
    q13 = next(x for x in qual['arms'] if x['arm'] == 'scope_joint' and x['width'] == 8)
    assert all(q13['per_problem'][str(p)]['source_sha256'] == sha(allsrc[p].encode()) for p in fit_ids + val_ids)
    all_q = all(q13['qualification'][str(p)]['passed'] for p in fit_ids + val_ids)
    cb = c['current_best']; cb_rows, cb_sum = published(LIT / cb['evidence'], cb['arm'], cb['evidence_sha256'], val_ids)
    seed_val = summary(seed_rows, val_ids, seed_db); item13 = summary(rows13, val_ids, db13)
    assert all(seed_rows[p]['actions'] == cb_rows[p]['actions'] for p in cb_rows) and all(seed_val[k] == cb_sum[k] for k in cb_sum)
    assert seed_val['actions'] == 8283 and item13['actions'] == 8504, 'item 51 and item 13 must reproduce'
    out = {'schema': 'gamma.alphabet96-v1.evidence.v1', 'contract_sha256': res['contract_sha256'], 'results_sha256': sha((a.run / 'results.json').read_bytes()),
           'qualification_reused': c['qualification_receipt'], 'all_sources_qualified_by_receipt': all_q, 'missing_characters': c['missing_characters'],
           'pinned_R': summary(r_rows, val_ids, r_db), 'seed': seed_val, 'item13': item13, 'exit_codes': res['exit_codes'], 'arms': {}, 'failed_arms': {}}
    present = {x['arm']: x for x in res['arms']}; replays = {}
    for name in succ.ARMS:
        # A missing arm or a nonzero exit is a retained failure, never silently dropped from the evidence.
        if name not in present or res['exit_codes'].get(name) != 0:
            out['failed_arms'][name] = {'exit_code': res['exit_codes'].get(name), 'results_present': name in present}; continue
        arm = present[name]; folder = a.run / name; spec = c['arms'][name]
        assert arm['k'] == spec['k'] and arm['repair'] == spec['repair']
        raw = (folder / 'dictionary.json').read_bytes(); seal = json.loads((folder / 'fit-seal.json').read_text())
        assert sha(raw) == seal['dictionary_sha256'] == arm['dictionary_sha256'] and seal['validation_loaded'] is False
        vocab = json.loads(raw); assert len(vocab) <= 256 and len(set(vocab)) == len(vocab)
        if not all(s in set(vocab) for s in sel.ALPHABET):
            out['failed_arms'][name] = {'alphabet_incomplete': True}; continue
        replay, replay_db, replay_illegal = rows_for(allsrc, vocab); replays[name] = replay
        assert replay_illegal == arm['illegal_entry_sha256'] and replay_db == arm['dictionary_bytes'] and replay == {str(k): v for k, v in arm['per_problem'].items()}, name
        covered = {'fit': sum(replay[str(p)]['encodable'] for p in fit_ids), 'validation': sum(replay[str(p)]['encodable'] for p in val_ids)}
        assert covered == {'fit': 300, 'validation': 100} and arm['decoded'] == 400  # all 96 characters: every program is encodable
        rows = replay; s = summary(rows, val_ids, replay_db); f = summary(rows, fit_ids, replay_db)
        fit_n = sum(rows[str(p)]['selections'] for p in fit_ids); fit_c = sum(rows[str(p)]['single_characters'] for p in fit_ids)
        mv = [json.loads(line) for line in (a.run / f'{name}-live' / 'moves.jsonl').read_text().splitlines()]
        drop = json.loads((a.run / f'{name}-live' / 'drop.json').read_text()); assert drop == arm['drop']
        recon = {'seed_fit': sum(seed_rows[str(p)]['selections'] for p in fit_ids), 'seed_characters': sum(seed_rows[str(p)]['single_characters'] for p in fit_ids),
                 'final_fit': fit_n, 'final_characters': fit_c, 'final_objective': c['char_scale'] * fit_n + fit_c,
                 'moves': len(mv), 'accepted_moves': sum(m['accepted'] for m in mv), 'feasible_moves': sum(m['feasible'] for m in mv),
                 'optimal_moves': sum(m['optimal'] for m in mv), 'statuses': {str(x): sum(m['model_status'] == x for m in mv) for x in sorted({m['model_status'] for m in mv})}}
        assert all(recon[k] == arm[k] for k in recon), {k: (recon[k], arm[k]) for k in recon if recon[k] != arm[k]}
        assert arm['start_fit'] == drop['selections'] and arm['start_characters'] == drop['characters'] and len(drop['dropped_sha256']) == len(c['missing_characters'])
        assert spec['repair'] or (not mv and arm['final_fit'] == drop['selections'] and arm['final_characters'] == drop['characters'])
        assert all(m['warm'] and m['feasible'] for m in mv) and arm['fit_programs_worse_than_start'] == 0
        pr_r, pr_s, pr_13 = paired(rows, r_rows, val_ids), paired(rows, seed_rows, val_ids), paired(rows, rows13, val_ids)
        ready = {'actions_5pct': s['actions'] <= 0.95 * out['pinned_R']['actions'], 'median_lower': s['median'] < out['pinned_R']['median'],
                 'p90_lower': s['p90'] < out['pinned_R']['p90'], 'improved_60': pr_r['better'] >= 60, 'worsened_25': pr_r['worse'] <= 25,
                 'fraction_not_higher': s['single_character_fraction'] <= out['pinned_R']['single_character_fraction'],
                 'package_105': s['package_bytes'] <= 1.05 * out['pinned_R']['package_bytes'], 'qualified_clean': all_q and not replay_illegal,
                 'decoded_400': arm['decoded'] == 400}
        inc13, inc51 = incremental(s, item13, pr_13), incremental(s, out['seed'], pr_s)
        out['arms'][name] = {**recon, 'k': spec['k'], 'repair': spec['repair'], 'drop': drop, 'coverage': covered, 'dictionary_sha256': arm['dictionary_sha256'],
                             'illegal_entry_sha256': replay_illegal, 'fit': f, 'validation': s, 'paired_vs_R': pr_r, 'paired_vs_item51': pr_s, 'paired_vs_item13': pr_13,
                             'ready_vs_R': ready, 'incremental_vs_item13': inc13, 'incremental_vs_item51': inc51,
                             'robust_ready': all(ready.values()) and all(inc13.values()), 'successor_of_item51': all(ready.values()) and all(inc51.values()),
                             'per_problem_validation_actions': {str(p): rows[str(p)]['actions'] for p in val_ids}}
    A = out['arms']; ok = lambda n: n in A
    out['same_drop'] = (A['drop']['drop']['dropped_sha256'] == A['repair']['drop']['dropped_sha256']) if ok('drop') and ok('repair') else None
    out['predictions'] = {  # FREEZE.md F1-F5
        'F1': all(A[n]['drop']['optimal'] for n in A) if A else None,
        'F2': (A['drop']['validation']['actions'] <= out['seed']['actions'] + 20) if ok('drop') else None,
        'F3': any(v['robust_ready'] for v in A.values()) if A else None,
        'F4': (A['repair']['validation']['actions'] < A['drop']['validation']['actions']) if ok('drop') and ok('repair') else None,
        'F5': all(ok(n) for n in succ.ARMS) and not out['failed_arms']}
    cands = [k for k, v in A.items() if v['robust_ready']]
    rank = lambda k: (A[k]['validation']['actions'], A[k]['validation']['package_bytes'], k)
    out['selected_robust'] = min(cands, key=rank) if cands else None
    succs = [k for k, v in A.items() if v['successor_of_item51']]
    out['selected_successor'] = min(succs, key=rank) if succs else None
    out['record_time_best'] = replacement(a, succs, out, replays, val_ids, rank)
    (HERE / 'evidence').mkdir(exist_ok=True); (HERE / 'evidence/results.json').write_text(json.dumps(out, indent=1, sort_keys=True) + '\n')
    for k, v in A.items():
        print(k, v['drop']['optimal'], v['drop']['selections'], v['final_fit'], v['validation']['actions'], v['validation']['median'], v['validation']['p90'],
              round(100 * v['validation']['single_character_fraction'], 3), 'vs51', v['paired_vs_item51'], 'vs13', v['paired_vs_item13'], 'robust', v['robust_ready'])
    print('item51', out['seed']['actions'], 'item13', out['item13']['actions'], 'robust', out['selected_robust'], 'successor', out['selected_successor'],
          'failed', out['failed_arms'], out['predictions'])


if __name__ == '__main__':
    main()
