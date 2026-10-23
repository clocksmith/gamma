"""Independent source, pool, model and integer witness replay; metadata only."""
import argparse
import json
import math
from pathlib import Path

import backend
import model
import pool

HERE = Path(__file__).resolve().parent; LIT = HERE.parent
packet_audit = backend.module('fraction_primal_packet_audit', LIT / 'all-substring-fraction-v1/report.py')
sha, write = backend.sha, backend.write
SOLVER_TIMER_TOLERANCE = .05  # Separate HiGHS/monotonic timers, seconds.
PATH_POLICY = 'minimum_F_then_minimum_N_then_lexicographic_entry_ids'
# Inherited exactly from all-substring-fraction-v1/report.py witness().
NEAR_WHOLE_THRESHOLD = .9


def witness_summary(witness):
    """Aggregate already independently replayed packets, without changing paths."""
    stats = witness['entry_statistics']; entries = witness['entries']
    assert len(stats) == entries
    one = sum(row['distinct_program_support'] == 1 for row in stats)
    near = sum(row['maximum_fraction_of_containing_source'] >= NEAR_WHOLE_THRESHOLD for row in stats)
    both = sum(row['distinct_program_support'] == 1 and
               row['maximum_fraction_of_containing_source'] >= NEAR_WHOLE_THRESHOLD for row in stats)
    assert one == witness['one_owner_entries']
    assert near == witness['entries_covering_at_least_90_percent_of_a_source']
    n = witness['selections']; actions = witness['actions']
    assert actions['total'] == n['total'] + n['n']
    assert witness['objective'] == 10*witness['characters'] - n['total']
    assert witness['character_fraction'] == witness['characters']/n['total']
    return {'path_policy': PATH_POLICY, 'programs': n['n'], 'F': witness['objective'],
            'C': witness['characters'], 'N': n['total'], 'actions': actions['total'],
            'median_selections': n['median'], 'p90_selections': n['p90'], 'p95_selections': n['p95'],
            'character_fraction': witness['character_fraction'], 'entries': entries,
            'entry_share_denominator': 'all_dictionary_entries_including_unused_and_singletons',
            'one_owner_entries': one, 'one_owner_entry_share': one/entries if entries else None,
            'near_whole_entries': near, 'near_whole_entry_share': near/entries if entries else None,
            'one_owner_and_near_whole_entries': both,
            'one_owner_and_near_whole_entry_share': both/entries if entries else None,
            'near_whole_threshold': NEAR_WHOLE_THRESHOLD,
            'near_whole_definition': 'entry_length >= 90% of at least one source containing that entry',
            'one_owner_definition': 'substring occurs in exactly one distinct source, regardless of packet use',
            'entry_share_interpretation': 'descriptive size/support counts; not semantic reuse or legality tests'}


def summarize_witnesses(witnesses):
    summaries = {name: witness_summary(witnesses[name]) for name in ('seed','warm','cold') if name in witnesses}
    seed = summaries['seed']
    for row in summaries.values():
        row['relative_to_minimum_F_seed'] = {
            'F_delta': row['F']-seed['F'], 'N_delta': row['N']-seed['N'],
            'actions_delta': row['actions']-seed['actions'],
            'character_fraction_delta': row['character_fraction']-seed['character_fraction'],
            'lower_fraction_with_higher_N': row['character_fraction'] < seed['character_fraction'] and row['N'] > seed['N'],
            'lower_F_with_higher_N': row['F'] < seed['F'] and row['N'] > seed['N']}
    return summaries


def number(value, nonnegative=True):
    assert type(value) in (int, float) and math.isfinite(value)
    assert not nonnegative or value >= 0
    return value


def solver_metadata(raw, name, model_hash, seconds_limit, initial, witness):
    assert raw['warm'] is (name == 'warm')
    assert type(raw['feasible']) is bool and type(raw['optimal']) is bool
    assert raw['model_sha256'] == model_hash
    assert type(raw['model_status']) is int and type(raw['nodes']) is int and raw['nodes'] >= 0
    assert raw['optimal'] is (raw['model_status'] == int(model.backend.h.HighsModelStatus.kOptimal))
    if name == 'warm':
        assert raw['set_solution_status'] == 0 and raw['feasible'] is True
    else:
        assert raw['set_solution_status'] is None
    assert (witness is not None) == raw['feasible']
    if witness is not None:
        objective = number(raw['objective'], False)
        assert witness['objective'] <= objective + 1e-6
        if raw['optimal']:
            assert abs(witness['objective'] - objective) <= 1e-6
        if name == 'warm':
            assert witness['objective'] <= initial and objective <= initial + 1e-6
        number(raw['max_primal_infeasibility'])
    else:
        assert raw['objective'] is None and raw['optimal'] is False
    for key in ('dual_bound', 'gap'):
        if raw[key] is not None:
            number(raw[key], key == 'gap')
    call_seconds = number(raw['call_seconds']); solver_seconds = number(raw['solver_run_seconds'])
    assert solver_seconds <= call_seconds + SOLVER_TIMER_TOLERANCE
    # HiGHS measures its own wall time and may complete its current operation
    # after the requested limit; the hard process deadline bounds that overrun.
    return {'warm': raw['warm'], 'feasible': raw['feasible'],
            'numerical_restricted_model_optimal': raw['optimal'], 'model_status': raw['model_status'],
            'model_sha256': model_hash, 'objective': raw['objective'],
            'floating_restricted_pool_dual_bound': raw['dual_bound'], 'relative_gap': raw['gap'],
            'nodes': raw['nodes'], 'max_primal_infeasibility': raw['max_primal_infeasibility'],
            'requested_solver_seconds': seconds_limit, 'solver_run_seconds': solver_seconds,
            'call_seconds': call_seconds}


def replay_arm(raw, folder, work, c, contract_hash):
    cohort = raw['cohort']; assert cohort in ('R', 'naming')
    private = folder / cohort
    assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256'] == contract_hash
    assert json.loads((private / 'results.json').read_text()) == raw
    assert json.loads((private / 'status.json').read_text()) == {'phase': 'complete', 'complete': True}
    assert not (private / 'failure.json').exists()
    texts, seed, q, parent = backend.inputs(c, work, cohort)
    assert raw['fit_problems'] == len(texts) == 300
    assert raw['fit_source_sha256'] == parent['fit_source_sha256']
    assert raw['parent_q_sha256'] == parent['certificate']['q_sha256']
    banned = backend.dual.sel.forbidden_strings(texts); index = pool.implicit.Index(texts, banned)
    independent_numerator = pool.implicit.verify(index, q, c['pool']['capacity'], c['pool']['denominator'])
    cert = index.certificate(q, c['pool']['capacity'], c['pool']['denominator'])
    assert cert['numerator'] == independent_numerator
    for key in backend.CERT_KEYS:
        assert raw['parent_full_class_certificate'][key] == parent['certificate'][key] == cert[key]
    candidates, info = pool.build(index, q, seed, c['pool']['denominator'], c['pool']['capacity'], c['pool']['entries'])
    assert sha(private / 'pool.json') == raw['pool_sha256']
    assert sha(private / 'pool-provenance.json') == raw['pool_provenance_sha256']
    assert json.loads((private / 'pool.json').read_text()) == candidates
    assert json.loads((private / 'pool-provenance.json').read_text()) == info
    counts = {k: v for k, v in info.items() if k != 'provenance'}; assert counts == raw['pool_counts']
    rebuilt = model.build(texts, candidates, c['pool']['capacity'], seed, banned, **c['construction'])
    model_hash = model.fingerprint(rebuilt); assert model_hash == raw['model_sha256']
    for key in ('arcs', 'variables', 'transitions'):
        assert rebuilt[key] == raw[key]
    assert raw['solve_order'] == c['solve_order'][cohort]
    assert set(raw['solvers']) == {'warm', 'cold'}
    expected = {'seed'} | {name for name, receipt in raw['solvers'].items() if receipt['feasible']}
    assert set(raw['witnesses']) == expected
    witnesses = {}
    for name, data in raw['witnesses'].items():
        clean, vocab = packet_audit.witness(private / name, data, texts, banned, c, cert['integer_lower_bound'])
        assert set(vocab) <= set(candidates)
        if name == 'seed':
            assert vocab == seed
        exact = model.exact(texts, vocab)
        assert (clean['objective'], clean['characters'], clean['selections']['total']) == (exact['F'], exact['C'], exact['N'])
        for pid, row in exact['per_program'].items():
            assert (clean['per_problem'][pid]['objective'], clean['per_problem'][pid]['characters'], clean['per_problem'][pid]['selections']) == (row['F'], row['C'], row['N'])
        witnesses[name] = clean
    initial = witnesses['seed']['objective']; assert initial == rebuilt['initial'] == parent['witnesses']['seed']['objective']
    solvers = {name: solver_metadata(receipt, name, model_hash, c['search']['seconds'], initial, witnesses.get(name))
               for name, receipt in raw['solvers'].items()}
    elapsed = number(raw['seconds']); assert elapsed <= c['limits']['cohort_seconds']
    assert sum(s['call_seconds'] for s in solvers.values()) + number(raw['build_seconds']) <= elapsed
    return {'cohort': cohort, 'complete': True, 'validation_loaded': False, 'fit_problems': len(texts),
            'fit_source_sha256': parent['fit_source_sha256'], 'parent_q_sha256': parent['certificate']['q_sha256'],
            'parent_full_class_integer_lower_bound': cert['integer_lower_bound'],
            'parent_full_class_certificate': {k: cert[k] for k in backend.CERT_KEYS},
            'parent_integer_certificate_replayed': True, 'pool_counts': counts,
            'pool_sha256': raw['pool_sha256'], 'model_sha256': model_hash,
            'arcs': rebuilt['arcs'], 'variables': rebuilt['variables'], 'transitions': rebuilt['transitions'],
            'solve_order': c['solve_order'][cohort], 'solvers': solvers, 'witnesses': witnesses,
            'witness_cost_and_entry_share_summary': summarize_witnesses(witnesses),
            'warm_nonregression': witnesses['warm']['objective'] <= initial,
            'warm_F_gain': initial - witnesses['warm']['objective'],
            'cold_F_gain': initial - witnesses['cold']['objective'] if 'cold' in witnesses else None,
            'seconds': elapsed,
            'source_qualification': 'Pinned item13 exact source-hash receipt reuse; inherited item23 exit137 failure retained.',
            'semantic_reuse_audit': 'not_performed_relaxation_witness_only'}


def build_report(folder, work, here=HERE, lit=LIT):
    pool.implicit.require_checks(); cpath = here / 'contract.json'; c = json.loads(cpath.read_text()); chash = sha(cpath)
    assert c['ready_to_freeze'] is True
    for rel, digest in c['code_hashes'].items():
        assert sha(lit / rel) == digest
    for path, digest in c['runtime_files'].items():
        assert sha(Path(path)) == digest
    base = {'schema': 'gamma.fraction-primal-repair.report.v1', 'contract_sha256': chash, 'validation_loaded': False,
            'scope': 'fixed fit populations; bounded-pool relaxation witnesses only; no M1 promotion',
            'bound_interpretation': 'Only the replayed parent integer bound covers the full substring class. Solver bounds/statuses are numerical restricted-pool evidence.',
            'inherited_item23_failure_retained': True}
    if (folder / 'failure.json').exists():
        failure = json.loads((folder / 'failure.json').read_text())
        assert failure['contract_sha256'] == chash and failure['complete'] is False
        assert failure['partial_witnesses_promoted'] is False and failure['validation_loaded'] is False
        allowed = {'TimeoutError', 'MemoryError', 'AssertionError', 'ValueError', 'RuntimeError', 'OSError', 'FileNotFoundError', 'KeyboardInterrupt', 'SystemExit'}
        return {**base, 'complete': False, 'status': 'incomplete; no whole-job witness accepted',
                'promotion_allowed': False, 'verdicts': None,
                'failure_sha256': sha(folder / 'failure.json'), 'failure_type': failure['exception'] if failure['exception'] in allowed else 'other_exception',
                'seconds': number(failure['seconds']), 'predictions': {'P1': False, 'P2': None, 'P3': None}}
    assert not list(folder.glob('*/failure.json'))
    raw = json.loads((folder / 'results.json').read_text())
    assert raw['complete'] is True and raw['validation_loaded'] is False and raw['contract_sha256'] == chash
    assert len(raw['arms']) == 2 and {a['cohort'] for a in raw['arms']} == {'R', 'naming'}
    elapsed = number(raw['seconds']); assert elapsed <= c['limits']['overall_seconds']
    assert all(number(a['seconds']) <= elapsed for a in raw['arms'])
    for rel, digest in c['private_files'].items():
        assert sha(work / rel) == digest
    assert set(c['decoder_source_files']) == {'literals.py', 'pass2/working/bitpack.py'}
    for rel, spec in c['decoder_source_files'].items():
        assert sha(lit / rel) == spec['sha256'] and (lit / rel).stat().st_size == spec['bytes']
    assert c['decoder_dependency_bytes'] == sum(s['bytes'] for s in c['decoder_source_files'].values())
    arms = [replay_arm(a, folder, work, c, chash) for a in raw['arms']]
    return {**base, 'complete': True, 'status': 'complete; independently replayed', 'arms': arms, 'seconds': elapsed,
            'private_results_sha256': sha(folder / 'results.json'), 'decoder_dependency_bytes': c['decoder_dependency_bytes'],
            'offline_encoder_bytes': c['offline_encoder_bytes'], 'offline_encoder_scope': c['offline_encoder_scope'],
            'decoded_packets': sum(len(w['per_problem']) for a in arms for w in a['witnesses'].values()),
            'predictions': {'P1': all(a['warm_nonregression'] for a in arms),
                            'P2': {'cold_feasible_cohorts': sum(a['solvers']['cold']['feasible'] for a in arms)},
                            'P3': {'nonpositive_F_cohorts': sum(any(w['objective'] <= 0 for name, w in a['witnesses'].items() if name != 'seed') for a in arms)}}}


def write_report(report, here=HERE):
    (here / 'evidence').mkdir(exist_ok=True); write(here / 'evidence/results.json', report)
    lines = ['# Coverage-preserving fraction repair', '', '[Freeze](FREEZE.md); [design](DRAFT.md); [metadata](evidence/results.json).', '', report['status'] + '.', '']
    if not report['complete']:
        lines += ['No verdict, bound, or whole-job witness is accepted. Previous successful report prose has been replaced.',
                  '', 'The failed replay does not certify population exposure or run outcomes. Item 23 remains a recorded failure.']
        (here / 'README.md').write_text('\n'.join(lines) + '\n')
        return
    if report['complete']:
        lines += ['| Cohort | Seed F | Warm F | Cold F | Warm gain | Entries warm | Parent exact bound |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for arm in report['arms']:
            w = arm['witnesses']
            lines.append(f"| {arm['cohort']} | {w['seed']['objective']} | {w['warm']['objective']} | {w.get('cold', {}).get('objective', 'infeasible')} | {arm['warm_F_gain']} | {w['warm']['entries']} | {arm['parent_full_class_integer_lower_bound']} |")
        lines += ['', 'All following seed and feasible-witness rows use exact **minimum-F paths**, with ties by minimum N and then entry IDs. These are not minimum-N encodings. Actions include one Finish per program; median/p90/p95 below count selections only.', '',
                  '| Cohort | Witness | F | C | Character fraction | N | Actions | Median N | p90 N | p95 N | N change vs seed |',
                  '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
        for arm in report['arms']:
            for name, row in arm['witness_cost_and_entry_share_summary'].items():
                lines.append(f"| {arm['cohort']} | {name} | {row['F']} | {row['C']} | {100*row['character_fraction']:.4f}% | {row['N']} | {row['actions']} | {row['median_selections']} | {row['p90_selections']} | {row['p95_selections']} | {row['relative_to_minimum_F_seed']['N_delta']:+d} |")
        lines += ['', '| Cohort | Witness | Dictionary entries | One-owner entries / share | Near-whole entries / share | Both / share |',
                  '|---|---|---:|---:|---:|---:|']
        for arm in report['arms']:
            for name, row in arm['witness_cost_and_entry_share_summary'].items():
                counts = [f"{row[count]} / {100*row[share]:.2f}%" if row[share] is not None else '0 / undefined'
                          for count, share in [('one_owner_entries','one_owner_entry_share'),
                                               ('near_whole_entries','near_whole_entry_share'),
                                               ('one_owner_and_near_whole_entries','one_owner_and_near_whole_entry_share')]]
                lines.append(f"| {arm['cohort']} | {name} | {row['entries']} | {' | '.join(counts)} |")
        lines += ['', 'Entry-share denominators include every dictionary entry, including unused entries and singletons. One-owner means occurrence in exactly one distinct source, not use by one packet. Near-whole retains the inherited threshold: entry length at least 90% of any containing source. The overlap column is both conditions. These are descriptive size/support statistics, not semantic reuse or legality tests.']
    lines += ['', 'Every singleton is charged. F = 10 C − N targets the aggregate character fraction; exact minimum-F paths may use more selections than minimum-N paths.',
              '', 'Lower F or a lower character fraction does not imply fewer actions or better selection quantiles. Signed seed comparisons and the lower_fraction_with_higher_N flag in metadata expose that tradeoff under the same minimum-F policy. No minimum-N counterfactual is computed by this reporting addition.',
              '', report['bound_interpretation'], '', 'One-owner and near-whole strings remain relaxation witnesses with semantic reuse unresolved. No M1 candidate or full-class impossibility claim follows. Item 23’s failed qualification remains recorded; unchanged sources reuse only exact item 13 passing hashes.',
              '', 'No validation or protected population was loaded. Sources, vocabularies, q and packets remain private.']
    (here / 'README.md').write_text('\n'.join(lines) + '\n')


def publish(folder, work, here=HERE, lit=LIT):
    """A failed rerun replaces both metadata and any stale successful prose."""
    try:
        result = build_report(folder, work, here, lit)
    except (Exception, KeyboardInterrupt) as error:
        allowed = {'TimeoutError', 'MemoryError', 'AssertionError', 'ValueError', 'RuntimeError', 'OSError',
                   'FileNotFoundError', 'KeyboardInterrupt', 'TypeError', 'KeyError'}
        failure = {'schema': 'gamma.fraction-primal-repair.report.v1', 'complete': False,
                   'status': 'replay verification failed; no verdict', 'promotion_allowed': False,
                   'verdicts': None, 'phase': 'independent_report',
                   'failure_type': type(error).__name__ if type(error).__name__ in allowed else 'other_exception',
                   'bound_interpretation': 'No bound or witness is accepted after this verification failure.',
                   'inherited_item23_failure_retained': True}
        write_report(failure, here)
        raise
    write_report(result, here)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True); a = p.parse_args()
    publish(a.run.resolve(), a.work.resolve())
