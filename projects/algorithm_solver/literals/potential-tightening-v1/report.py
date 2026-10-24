"""Independent item53 certificate replay; private inputs require accepted production.

The measured independent checker is immutable. Public output contains selected
hashes, counts and numerical certificate rows, never source or top-entry text
or identities. Shared input/parser and item33 index dependencies are disclosed.
"""
import signal
import time


class HardDeadline(BaseException):
    pass


def _expired(*_):
    raise HardDeadline('independent report deadline')


BOOT_STARTED = time.monotonic() if __name__ == '__main__' else None
if BOOT_STARTED is not None:
    signal.signal(signal.SIGALRM, _expired)
    signal.setitimer(signal.ITIMER_REAL, 600)

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import sys

HERE = Path(__file__).resolve().parent
WORKER_SECONDS = 600
PHASE_SECONDS = 1200
ADDRESS_SPACE_BYTES = 8*1024**3
COHORTS = ('R', 'naming')
PROOF_FIELDS = ('denominator', 'path_numerators', 'old_charge', 'old_numerator',
                'class_counts', 'top_entries', 'rows', 'old_occurrences', 'occurrence_sha256')
PRODUCTION_COUNTERS = ('old_trie_transitions', 'old_occurrences_tightened',
    'tight_suffix_positions_checked', 'repeated_new_occurrence_contributions',
    'unique_range_queries', 'unique_entries_extracted')
REPORT_COUNTERS = ('old_occurrences_tightened', 'old_bellman_edges_checked',
    'tight_suffix_positions_checked', 'streamed_allowed_depths', 'new_entries_streamed',
    'new_occurrence_contributions')
SCIENTIFIC_FIELDS = ('schema', 'lifted', 'tightened', 'new_only_class_counts',
    'new_only_top_entries', 'digests', 'reductions', 'deltas')
GEOMETRY_FIELDS = ('source_characters', 'full_groups', 'full_distinct_entries', 'exact_ban_occurrences')
SHARED = 'Pinned input/parser binding; item33 Index and suffix/partition/ban verifier.'
ARM_FIELDS = set(('schema complete validation_loaded cohort contract_sha256 bindings_sha256 '
    'source_identity_sha256 banned_set_sha256 parent_certificate_sha256 checked_proof_sha256 '
    'top_entries_sha256 old_occurrence_order_sha256 old_path_terms_sha256 fit_problems '
    'old_pool_entries seed_entries old_occurrences geometry denominator path_numerator '
    'old_charge old_numerator old_integer_lower_bound largest_positive_k lifted_largest_positive_k '
    'class_counts rows lifted_rows paired_digests reductions deltas new_only_class_counts '
    'production_seconds production_phase_seconds_sha256 production_peak_rss_kib '
    'production_work report_work shared_dependencies all514_independently_replayed '
    'parent50_independently_reconstructed parent50_evidence_sha256 '
    'old_certificate_independently_replayed suffix_potential_proof_checked '
    'production_arm_sha256 production_results_sha256 production_supervisor_sha256 '
    'report_worker_seconds report_peak_rss_kib').split())


def integer(value, minimum=None, maximum=None):
    assert type(value) is int
    assert minimum is None or value >= minimum
    assert maximum is None or value <= maximum
    return value


def number(value, maximum=None):
    assert type(value) in (int, float) and math.isfinite(value) and value >= 0
    assert maximum is None or value <= maximum
    return value


def shaped(value):
    """Normalize tuple/JSON key representation, never bool/integer semantics."""
    if type(value) is dict:
        assert all(type(key) in (str, int) for key in value)
        result = {str(key): shaped(item) for key, item in value.items()}
        assert len(result) == len(value)
        return result
    if type(value) in (list, tuple):
        return [shaped(item) for item in value]
    assert type(value) in (str, int, float, bool, type(None))
    if type(value) is float:
        assert math.isfinite(value)
    return value


def exact(actual, expected):
    assert type(actual) is type(expected), (type(actual).__name__, type(expected).__name__)
    if type(expected) is dict:
        assert actual.keys() == expected.keys()
        for key in expected:
            exact(actual[key], expected[key])
    elif type(expected) is list:
        assert len(actual) == len(expected)
        for left, right in zip(actual, expected):
            exact(left, right)
    else:
        assert actual == expected


def digest(value):
    return hashlib.sha256(json.dumps(shaped(value), sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_string(value):
    assert type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
    return value


def read(path):
    # Reject repeated keys rather than silently accepting an ambiguous receipt.
    def unique(pairs):
        output = {}
        for key, value in pairs:
            assert key not in output, 'duplicate JSON key'
            output[key] = value
        return output
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def config_limits(config):
    assert config['active'] is True
    expected = {'worker_seconds': WORKER_SECONDS, 'production_seconds': PHASE_SECONDS,
                'report_seconds': PHASE_SECONDS, 'cleanup_seconds': 10,
                'address_space_bytes': ADDRESS_SPACE_BYTES,
                'arm_cores': {'R': [6], 'naming': [7]}}
    for key, value in expected.items():
        exact(config['limits'][key], value)
    assert type(config['fit_ids']) is list and len(config['fit_ids']) == 300
    assert len(set(config['fit_ids'])) == 300
    for pid in config['fit_ids']:
        integer(pid, 0)


def top_shape(entries, counts):
    assert type(entries) is dict and set(entries) == set(counts) == {'1', '2'}
    for support in ('1', '2'):
        integer(counts[support], 0)
        assert type(entries[support]) is list and len(entries[support]) == min(256, counts[support])
        for row in entries[support]:
            assert type(row) is list and len(row) == 3
            integer(row[0], 0); integer(row[1], 0); integer(row[2], 1)
        assert entries[support] == sorted(entries[support], key=lambda row: (-row[0], row[1], row[2]))
        assert len({tuple(row[1:]) for row in entries[support]}) == len(entries[support])
    assert not ({tuple(row[1:]) for row in entries['1']} & {tuple(row[1:]) for row in entries['2']})


def proof_shape(proof):
    assert type(proof) is dict and set(proof) == set(PROOF_FIELDS)
    integer(proof['denominator'], 1); integer(proof['old_charge'], 0)
    integer(proof['old_numerator']); integer(proof['old_occurrences'], 0)
    hash_string(proof['occurrence_sha256'])
    assert type(proof['path_numerators']) is dict and proof['path_numerators']
    for pid, value in proof['path_numerators'].items():
        assert type(pid) is str; integer(value)
    total = sum(proof['path_numerators'].values())
    assert proof['old_numerator'] == total-proof['old_charge']
    top_shape(proof['top_entries'], proof['class_counts'])
    prefixes = {}
    for support, entries in proof['top_entries'].items():
        prefixes[support] = [0]
        for weight, _, _ in entries: prefixes[support].append(prefixes[support][-1]+weight)
    assert type(proof['rows']) is list and len(proof['rows']) == 257
    for k, row in enumerate(proof['rows']):
        assert set(row) == {'k', 'charge', 'one_owner_slots', 'shared_slots', 'numerator', 'integer_lower_bound'}
        for value in row.values(): integer(value)
        best = None
        for one in range(min(k, 256, proof['class_counts']['1'])+1):
            shared = min(256-one, proof['class_counts']['2'])
            candidate = (prefixes['1'][one]+prefixes['2'][shared], -one, shared)
            if best is None or candidate > best: best = candidate
        charge, minus_one, shared = best
        exact(row, {'k': k, 'charge': charge, 'one_owner_slots': -minus_one,
            'shared_slots': shared, 'numerator': total-charge,
            'integer_lower_bound': -(-(total-charge)//proof['denominator'])})
    assert proof['rows'][0]['numerator'] >= proof['old_numerator']
    assert all(a['charge'] <= b['charge'] for a,b in zip(proof['rows'], proof['rows'][1:]))


def paired_shape(paired):
    assert type(paired) is dict and set(paired) == set(SCIENTIFIC_FIELDS)|{'work'}
    assert paired['schema'] == 'gamma.potential-tightening.supplied.v1'
    for name in ('lifted', 'tightened'): proof_shape(paired[name])
    before, after = paired['lifted'], paired['tightened']
    for key in set(PROOF_FIELDS)-{'top_entries','rows'}: exact(after[key], before[key])
    top_shape(paired['new_only_top_entries'], paired['new_only_class_counts'])
    assert paired['new_only_class_counts']['2'] == 0
    for support in ('1','2'): assert paired['new_only_class_counts'][support] <= before['class_counts'][support]
    deltas = []
    for a,b in zip(before['rows'], after['rows']):
        assert b['charge'] <= a['charge'] and b['integer_lower_bound'] >= a['integer_lower_bound']
        deltas.append({'k':a['k'], 'charge_reduction':a['charge']-b['charge'],
                       'integer_bound_gain':b['integer_lower_bound']-a['integer_lower_bound']})
    exact(paired['deltas'], deltas)
    red = paired['reductions']
    assert set(red) == {'old_occurrences_reduced','old_multiplier_reduction','old_entries_reduced',
        'occurring_old_entries','absent_old_entries','strict_charge_budgets','strict_integer_bound_budgets'}
    for value in red.values(): integer(value, 0)
    assert red['old_entries_reduced'] <= red['occurring_old_entries'] <= before['old_occurrences']
    assert red['old_entries_reduced'] <= red['old_occurrences_reduced'] <= before['old_occurrences']
    assert red['old_multiplier_reduction'] >= red['old_occurrences_reduced']
    assert red['occurring_old_entries'] == sum(before['class_counts'].values())-sum(paired['new_only_class_counts'].values())
    assert all(row['charge_reduction'] <= red['old_multiplier_reduction'] for row in deltas)
    exact(red['strict_charge_budgets'], sum(row['charge_reduction']>0 for row in deltas))
    exact(red['strict_integer_bound_budgets'], sum(row['integer_bound_gain']>0 for row in deltas))
    hashes = paired['digests']
    expected = {'potentials_sha256','old_weights_sha256','tightened_old_weights_sha256','new_only_top_sha256'}
    for name in ('lifted','tightened'):
        expected.update(name+suffix for suffix in ('_proof_sha256','_top_entries_sha256','_rows_sha256'))
        assert hashes[name+'_proof_sha256'] == digest(paired[name])
        assert hashes[name+'_top_entries_sha256'] == digest(paired[name]['top_entries'])
        assert hashes[name+'_rows_sha256'] == digest(paired[name]['rows'])
    assert set(hashes) == expected
    for value in hashes.values(): hash_string(value)
    assert hashes['new_only_top_sha256'] == digest(paired['new_only_top_entries'])
    assert set(paired['work']) == set(PRODUCTION_COUNTERS)
    for value in paired['work'].values(): integer(value, 0)
    assert paired['work']['old_occurrences_tightened'] == before['old_occurrences']
    assert paired['work']['old_trie_transitions'] >= before['old_occurrences']
    assert paired['work']['unique_entries_extracted'] <= 256
    assert paired['work']['unique_range_queries'] >= paired['work']['unique_entries_extracted']


def parent50(config):
    pin = config['parent50_evidence']; parent_contract = config['parent50_contract']
    for binding in (pin, parent_contract):
        assert set(binding) == {'path','sha256'}
        assert sha(HERE.parent/binding['path']) == hash_string(binding['sha256'])
    value = read(HERE.parent/pin['path'])
    assert value['schema'] == 'gamma.potential-lift.report.v1' and value['complete'] is True
    assert value['contract_sha256'] == parent_contract['sha256']
    assert value['validation_loaded'] is False and value['validation_or_cases_opened'] is False
    assert value['verdicts']['all257_replayed'] is True and value['verdicts']['k0_preserves_old_bound'] is True
    assert [a['cohort'] for a in value['arms']] == list(COHORTS)
    exact({a['cohort']:a for a in value['arms']}, config['parent50_arms'])
    for arm in value['arms']:
        assert arm['complete'] is True and arm['validation_loaded'] is False
        for key in ('all257_independently_replayed','old_certificate_independently_replayed','suffix_potential_proof_checked'):
            assert arm[key] is True
        assert arm['contract_sha256'] == parent_contract['sha256']
    return config['parent50_arms']


def compare50(cohort, arm, proof, expected):
    # Reconstruct all scientific parent50 terms from this run's independently
    # checked values; never accept counts alone or read private item50 artifacts.
    common = ('bindings_sha256','source_identity_sha256','banned_set_sha256','parent_certificate_sha256',
        'old_occurrence_order_sha256','old_path_terms_sha256','fit_problems','old_pool_entries','seed_entries',
        'old_occurrences','geometry','denominator','path_numerator','old_charge','old_numerator','old_integer_lower_bound','class_counts')
    assert expected['cohort'] == cohort
    for key in common: exact(arm[key], expected[key])
    exact(proof['rows'], expected['rows'])
    assert digest(proof) == expected['checked_proof_sha256']
    assert digest(proof['top_entries']) == expected['top_entries_sha256']
    exact(max((r['k'] for r in proof['rows'] if r['integer_lower_bound']>0), default=None),expected['largest_positive_k'])


def accepted_production(run, config, contract_hash):
    """Only run receipts are read here; this must precede all nine-file access."""
    config_limits(config)
    parent50(config)
    run = Path(run)
    assert not (run/'failure.json').exists()
    for cohort in COHORTS:
        assert not (run/(cohort+'-failure.json')).exists()
        assert not (run/cohort/'failure.json').exists()
    production, supervisor = read(run/'results.json'), read(run/'supervisor.json')
    assert production['complete'] is supervisor['complete'] is True
    assert production['validation_loaded'] is False and supervisor['phase'] == 'production'
    assert production['contract_sha256'] == supervisor['contract_sha256'] == contract_hash
    codes = supervisor['returncodes']
    assert type(codes) is list and len(codes) == 2
    assert all(type(code) is int and code == 0 for code in codes)
    number(supervisor['cleanup_seconds'], 10)
    number(supervisor['elapsed'], PHASE_SECONDS)
    number(production['seconds'], PHASE_SECONDS)
    assert production['seconds'] <= supervisor['elapsed']
    assert type(production['arms']) is list and len(production['arms']) == 2
    assert [arm['cohort'] for arm in production['arms']] == list(COHORTS)
    for arm in production['arms']:
        assert arm['complete'] is True and arm['validation_loaded'] is False
        assert arm['contract_sha256'] == contract_hash
        number(arm['seconds'], WORKER_SECONDS)
        assert arm['seconds'] <= production['seconds']
        integer(arm['peak_rss_kib'], 1, ADDRESS_SPACE_BYTES//1024)
        assert type(arm['phase_seconds']) is dict
        assert all(type(key) is str for key in arm['phase_seconds'])
        for value in arm['phase_seconds'].values():
            number(value, arm['seconds'])
        assert sum(arm['phase_seconds'].values()) <= arm['seconds']
        assert type(arm['bindings']) is dict
        assert set(arm['full_shape']) == set(GEOMETRY_FIELDS)
        for value in arm['full_shape'].values():
            integer(value, 0)
        assert arm['schema'] == 'gamma.potential-tightening.arm.v1'
        paired_shape(arm['proof'])
        assert set(arm['proof']['lifted']['path_numerators']) == {str(pid) for pid in config['fit_ids']}
        exact(read(run/arm['cohort']/'results.json'), arm)
    return production, supervisor


def replay(cohort, inputs, raw, checker, expected_old, expected50):
    """Fresh scalar proof, with no production potentials or selected entries reused."""
    assert cohort in COHORTS and raw['cohort'] == cohort
    texts, banned = inputs['texts'], inputs['banned']
    exact(raw['bindings'], shaped(inputs['bindings']))
    index = checker.full.Index(texts, banned)
    checker.full.verify(index, {pid: [0]*len(text) for pid, text in texts.items()}, 0, 1)
    geometry = {'source_characters': len(index.positions), 'full_groups': len(index.groups),
                'full_distinct_entries': index.distinct_allowed_entries,
                'exact_ban_occurrences': sum(len(ends) for rows in index.banned_ends.values() for ends in rows)}
    exact(raw['full_shape'], geometry)
    exact(shaped(inputs['geometry']), geometry)
    del index
    assert {word for word in inputs['pool'] if len(word) == 1} == set(inputs['alphabet'])
    extras = sorted(word for word in inputs['seed'] if len(word) > 1
                    and sum(word in text for text in texts.values()) < 2)
    pool_counts = {'pool_entries': len(inputs['pool']),
                   'maximum_entry_length': max(map(len, inputs['pool'])),
                   'seed_extra_entries': len(extras),
                   'shared_learned_entries': sum(len(word) > 1 for word in inputs['pool'])-len(extras),
                   'occurrences': len(inputs['q'])}
    for key, value in pool_counts.items():
        exact(expected_old[key], value)
    assert expected_old['seed_extras_sha256'] == hashlib.sha256(
        json.dumps(extras, ensure_ascii=True).encode()).hexdigest()
    checked = checker.check(texts, banned, inputs['pool'], inputs['q'], inputs['seed'],
                            inputs['alphabet'], inputs['denominator'],
                            expected_source_hashes=inputs['source_hashes'],
                            expected_old_banned=banned,
                            expected_old_certificate=inputs['parent_certificate'],
                            expected_occurrence_sha256=raw['proof']['lifted']['occurrence_sha256'])
    checked = shaped(checked)
    paired_shape(raw['proof'])
    for key in SCIENTIFIC_FIELDS: exact(raw['proof'][key], checked[key])
    exact(checked['geometry'], geometry)
    assert set(checked) == set(SCIENTIFIC_FIELDS)|{'geometry','work','shared_dependency','scalar_replay'}
    assert checked['shared_dependency'] == 'item33 Index and verify partition/suffix/ban checks'
    assert checked['scalar_replay'] == 'AC/end-order paths; owner-run ends; all-depth exact sums'
    check_work(raw['proof'], checked['work'], geometry)
    result = sanitize(cohort, inputs, raw, checked, geometry)
    compare50(cohort, result, checked['lifted'], expected50)
    return result


def check_work(paired, work, geometry):
    assert set(work) == set(REPORT_COUNTERS)
    for value in work.values(): integer(value, 0)
    old = paired['lifted']['old_occurrences']
    assert work['old_occurrences_tightened'] == work['old_bellman_edges_checked'] == old
    assert work['tight_suffix_positions_checked'] == geometry['source_characters']
    assert work['streamed_allowed_depths'] == geometry['full_distinct_entries']
    assert work['new_entries_streamed'] == sum(paired['new_only_class_counts'].values())
    assert work['new_occurrence_contributions'] >= work['new_entries_streamed']
    assert paired['work']['repeated_new_occurrence_contributions'] <= work['new_occurrence_contributions']
    assert paired['work']['tight_suffix_positions_checked'] == geometry['source_characters']


def positive_k(proof):
    return max((row['k'] for row in proof['rows'] if row['integer_lower_bound']>0), default=None)


def sanitize(cohort, inputs, raw, checked, geometry):
    proof = checked['tightened']; paths = proof['path_numerators']; old = proof['old_numerator']
    denominator = proof['denominator']
    return {'schema': 'gamma.potential-tightening.report-arm.v1', 'complete': True,
        'validation_loaded': False, 'cohort': cohort, 'contract_sha256': raw['contract_sha256'],
        'bindings_sha256': digest(inputs['bindings']), 'source_identity_sha256': digest(inputs['source_hashes']),
        'banned_set_sha256': digest(sorted(inputs['banned'])), 'parent_certificate_sha256': digest(inputs['parent_certificate']),
        'checked_proof_sha256': digest({key:checked[key] for key in SCIENTIFIC_FIELDS}),
        'top_entries_sha256': digest(proof['top_entries']), 'old_occurrence_order_sha256': proof['occurrence_sha256'],
        'old_path_terms_sha256': digest([paths[pid] for pid in sorted(paths)]),
        'fit_problems': len(inputs['texts']), 'old_pool_entries': len(inputs['pool']), 'seed_entries': len(inputs['seed']),
        'old_occurrences': proof['old_occurrences'], 'geometry': geometry, 'denominator': denominator,
        'path_numerator': sum(paths.values()), 'old_charge': proof['old_charge'], 'old_numerator': old,
        'old_integer_lower_bound': -(-old//denominator), 'largest_positive_k': positive_k(proof),
        'lifted_largest_positive_k': positive_k(checked['lifted']), 'class_counts': proof['class_counts'],
        'rows': proof['rows'], 'lifted_rows': checked['lifted']['rows'], 'paired_digests': checked['digests'],
        'reductions': checked['reductions'], 'deltas': checked['deltas'], 'new_only_class_counts': checked['new_only_class_counts'],
        'production_seconds': raw['seconds'], 'production_phase_seconds_sha256': digest(raw['phase_seconds']),
        'production_peak_rss_kib': raw['peak_rss_kib'], 'production_work': raw['proof']['work'], 'report_work': checked['work'],
        'shared_dependencies': SHARED, 'all514_independently_replayed': True,
        'parent50_independently_reconstructed': True, 'old_certificate_independently_replayed': True,
        'suffix_potential_proof_checked': True}


def failure_result(error):
    # Exception strings can contain source paths or input data; retain only type.
    name = type(error).__name__ if isinstance(error, BaseException) else 'ReportFailure'
    return {'schema': 'gamma.potential-tightening.report.v1', 'complete': False,
            'validation_loaded': False, 'failure_type': name, 'verdicts': None,
            'predictions': {'P1': None, 'P2': None, 'P3': None, 'P4': None},
            'm1_claim': False, 'packet_or_witness_claim': False}


def markdown(result):
    if result['complete'] is not True:
        return '# Item 53 incomplete\n\nIndependent report incomplete; no verdict. Partial artifacts retained.\n'
    lines = ['# Item 53 fixed-potential tightening', '',
        'Exact fixed-source bounds for F = 10C − N with at most 256 paid entries.',
        'Every old occurrence penalty is minimized at unchanged old suffix potentials; new-only penalties remain item50’s lift.', '',
        '| Cohort | k | Item50 bound | Item53 bound | Exact charge reduction |',
        '| --- | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        ks = {0,1,2,4,8,16,32,64,128,256}
        for key in ('largest_positive_k','lifted_largest_positive_k'):
            if arm[key] is not None: ks.update((arm[key],min(256,arm[key]+1)))
        for k in sorted(ks):
            lines.append(f"| {arm['cohort']} | {k} | {arm['lifted_rows'][k]['integer_lower_bound']} | {arm['rows'][k]['integer_lower_bound']} | {arm['deltas'][k]['charge_reduction']} |")
        lines += ['',f"{arm['cohort']}: largest positive k changes from {arm['lifted_largest_positive_k']} to {arm['largest_positive_k']}; old occurrences reduced: {arm['reductions']['old_occurrences_reduced']}."]
    lines += ['', 'All 257 paired rows per cohort are retained. Exact charge reductions and integer-bound gains are separate; rounding may hide a strict raw gain.',
        '', 'Predictions: '+json.dumps(result['predictions'],sort_keys=True),
        '', 'Positive bounds exclude aggregate C/N <= 10% only within this fixed300-source support-budget class. Paid singletons count. One-owner means one distinct source ID, not semantic reuse. Positivity does not prove coverage feasibility; larger budgets are not proved sufficient.',
        '', 'The full potential vector is derived independently and its digest reconciled. '+SHARED,
        '', result['fixed_potential_scope'],
        '', 'Nonpositive values and zero gains do not rule out stronger potentials. No validation, cases, source execution, new qualification, witness packets, canonical/package result, M1 or promotion claim. Original item13 qualification is reused; inherited item23 unchanged-source exit137 remains separate.']
    return '\n'.join(lines)+'\n'


def remove_success(output, deadline=None):
    """Minimal withdrawal only; never swallow the caller's hard deadline."""
    output = Path(output)
    for name in ('results.json', 'REPORT.md', 'results.json.pending', 'REPORT.md.pending'):
        if deadline is not None: worker_failure_guard(deadline)
        try:
            (output/name).unlink(missing_ok=True)
        except Exception:
            pass


def withdraw(output, error, deadline=None):
    """Caller supplies the absolute failure-I/O guard; hard deadlines propagate.

    Withdraw both success markers before starting potentially slow failure
    serialization/writes. Ordinary per-file errors remain independent, but a
    BaseException deadline from ANY supervisor class ends all further I/O.
    """
    output = Path(output)
    remove_success(output, deadline)
    failed = failure_result(error)
    for name, text in (('REPORT.md', markdown(failed)),
                       ('results.json', json.dumps(failed, sort_keys=True, indent=2)+'\n')):
        target = output/name
        try:
            if deadline is not None: worker_failure_guard(deadline)
            output.mkdir(parents=True, exist_ok=True)
            temporary = output/(name+'.failure')
            if deadline is not None: worker_failure_guard(deadline)
            temporary.write_text(text)
            if deadline is not None: worker_failure_guard(deadline)
            temporary.replace(target)
        except Exception:
            if deadline is not None: worker_failure_guard(deadline)
            try:
                target.unlink(missing_ok=True)
            except Exception:
                pass


def publish(output, result):
    output = Path(output)
    try:
        output.mkdir(parents=True, exist_ok=True)
        if result['complete'] is not True:
            withdraw(output, RuntimeError('incomplete'))
            return
        encoded = json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n'
        prose = markdown(result)
        (output/'REPORT.md.pending').write_text(prose)
        (output/'results.json.pending').write_text(encoded)
        (output/'REPORT.md.pending').replace(output/'REPORT.md')
        (output/'results.json.pending').replace(output/'results.json')
        for name in ('REPORT.md.pending', 'results.json.pending'):
            (output/name).unlink(missing_ok=True)
    except BaseException as error:
        # A one-shot owner alarm has no remaining guard once it has fired.
        # Propagate that BaseException without starting even an unlink; the
        # supervisor re-arms its single absolute emergency budget before
        # withdrawal. Ordinary direct-call write errors still withdraw locally.
        if isinstance(error, Exception) or signal.getitimer(signal.ITIMER_REAL)[0] > 0:
            remove_success(output)
        raise


def combine(run, output, config, elapsed, returncodes):
    run, output = Path(run), Path(output)
    assert not (output/'failure.json').exists()
    config_limits(config); number(elapsed, PHASE_SECONDS)
    assert type(returncodes) is list and len(returncodes) == 2
    assert all(type(code) is int and code == 0 for code in returncodes)
    contract_hash = sha(HERE/'contract.json')
    production, supervisor = accepted_production(run, config, contract_hash)
    parents = parent50(config)
    arms = []
    for cohort, raw in zip(COHORTS, production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        arm = read(output/(cohort+'.json')); paired = raw['proof']; proof = paired['tightened']
        assert set(arm) == ARM_FIELDS and arm['schema'] == 'gamma.potential-tightening.report-arm.v1'
        assert arm['complete'] is True and arm['validation_loaded'] is False
        assert arm['cohort'] == cohort and arm['contract_sha256'] == contract_hash
        assert arm['production_arm_sha256'] == sha(run/cohort/'results.json')
        assert arm['production_results_sha256'] == sha(run/'results.json')
        assert arm['production_supervisor_sha256'] == sha(run/'supervisor.json')
        assert arm['parent50_evidence_sha256'] == config['parent50_evidence']['sha256']
        assert arm['bindings_sha256'] == digest(raw['bindings'])
        assert arm['checked_proof_sha256'] == digest({key:paired[key] for key in SCIENTIFIC_FIELDS})
        assert arm['top_entries_sha256'] == digest(proof['top_entries'])
        for key in ARM_FIELDS:
            if key.endswith('_sha256'): hash_string(arm[key])
        expected_numbers = {'fit_problems':len(proof['path_numerators']), 'old_occurrences':proof['old_occurrences'],
            'denominator':proof['denominator'], 'path_numerator':sum(proof['path_numerators'].values()),
            'old_charge':proof['old_charge'], 'old_numerator':proof['old_numerator'],
            'old_integer_lower_bound':-(-proof['old_numerator']//proof['denominator']),
            'production_peak_rss_kib':raw['peak_rss_kib']}
        for key,value in expected_numbers.items(): exact(arm[key],value)
        integer(arm['seed_entries'],1,256); integer(arm['old_pool_entries'],arm['seed_entries'])
        exact(arm['old_pool_entries'],config['old_arms'][cohort]['pool_entries'])
        assert paired['reductions']['occurring_old_entries']+paired['reductions']['absent_old_entries'] == arm['old_pool_entries']
        assert arm['source_identity_sha256'] == digest(config['source_hashes'][cohort])
        assert arm['parent_certificate_sha256'] == digest(config['old_arms'][cohort]['certificate'])
        assert arm['banned_set_sha256'] == raw['bindings']['bans_sha256']
        assert arm['source_identity_sha256'] == raw['bindings']['source_hashes_sha256']
        assert arm['old_occurrence_order_sha256'] == proof['occurrence_sha256']
        assert arm['old_path_terms_sha256'] == digest([proof['path_numerators'][pid] for pid in sorted(proof['path_numerators'])])
        assert arm['production_phase_seconds_sha256'] == digest(raw['phase_seconds'])
        exact(arm['production_work'],paired['work']); check_work(paired,arm['report_work'],raw['full_shape'])
        for public,private in [('rows','rows'),('class_counts','class_counts')]: exact(arm[public],proof[private])
        exact(arm['lifted_rows'],paired['lifted']['rows'])
        for public,private in [('paired_digests','digests'),('reductions','reductions'),('deltas','deltas'),('new_only_class_counts','new_only_class_counts')]:
            exact(arm[public],paired[private])
        exact(arm['largest_positive_k'],positive_k(proof))
        exact(arm['lifted_largest_positive_k'],positive_k(paired['lifted']))
        exact(arm['geometry'],raw['full_shape']); exact(arm['production_seconds'],raw['seconds'])
        number(arm['report_worker_seconds'],min(WORKER_SECONDS,elapsed))
        integer(arm['report_peak_rss_kib'],1,ADDRESS_SPACE_BYTES//1024)
        assert arm['shared_dependencies'] == SHARED
        for key in ('all514_independently_replayed','parent50_independently_reconstructed',
                    'old_certificate_independently_replayed','suffix_potential_proof_checked'):
            assert arm[key] is True
        compare50(cohort,arm,paired['lifted'],parents[cohort])
        arms.append(arm)
    predictions = {
        'P1': all(a['path_numerator'] == config['old_arms'][a['cohort']]['certificate']['relaxed_paths_numerator']
                  and all(d['charge_reduction']>=0 and d['integer_bound_gain']>=0 for d in a['deltas']) for a in arms),
        'P2': any(d['charge_reduction']>0 for a in arms for d in a['deltas']),
        'P3': any((a['largest_positive_k'] if a['largest_positive_k'] is not None else -1) >
                  (a['lifted_largest_positive_k'] if a['lifted_largest_positive_k'] is not None else -1) for a in arms),
        'P4': any(a['rows'][256]['integer_lower_bound']>0 for a in arms)}
    assert predictions['P1'] is True
    return {'schema':'gamma.potential-tightening.report.v1','complete':True,'validation_loaded':False,
        'population':'fixed300_fit_only','contract_sha256':contract_hash,
        'production_results_sha256':sha(run/'results.json'),'production_supervisor_sha256':sha(run/'supervisor.json'),
        'parent50_evidence_sha256':config['parent50_evidence']['sha256'],
        'production_seconds':production['seconds'],'report_seconds':elapsed,'arms':arms,
        'verdicts':{'all514_per_cohort_replayed':True,'parent50_reconstructed':True,'pointwise_dominance':True},
        'predictions':predictions,'qualification':{'authority':'Exact original item13 control/scope_joint receipts by source hash only',
            'fresh_jobs':0,'new_witness_packets':0,'inherited_failure':'Item23 later unchanged-source exit137 remains separate.'},
        'coverage_feasibility':'Positive bounds do not establish coverage feasibility at this or any larger support budget.',
        'shared_dependencies':SHARED,'m1_claim':False,'packet_or_witness_claim':False,'validation_or_cases_opened':False,
        'optimality_claim':False,
        'fixed_potential_scope':'Componentwise minimum penalties for these exact old suffix distances; no optimization across potentials or claim about the unrestricted dual optimum.'}


def worker_failure_guard(deadline):
    remaining = deadline-time.monotonic()
    if remaining <= 0: raise HardDeadline('report worker failure publication deadline')
    signal.setitimer(signal.ITIMER_REAL, remaining)


def withdraw_worker(target, failure, deadline):
    worker_failure_guard(deadline)
    try: target.unlink(missing_ok=True)
    except Exception: pass
    worker_failure_guard(deadline)
    write(target.with_name(target.stem+'-failure.json'), failure)
    worker_failure_guard(deadline)


def worker(cohort, work, run, output, deadline):
    started = BOOT_STARTED if BOOT_STARTED is not None else time.monotonic()
    phase, target, fresh = 'setup', Path(output)/(cohort+'.json'), False
    previous = signal.signal(signal.SIGALRM, _expired)
    effective = min(started+WORKER_SECONDS, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(.001, effective-time.monotonic()))
    try:
        if not __debug__:
            raise RuntimeError('independent report requires assertions')
        assert cohort in COHORTS
        number(deadline)
        if time.monotonic() >= effective:
            raise HardDeadline('deadline before report setup')
        resource.setrlimit(resource.RLIMIT_AS, (ADDRESS_SPACE_BYTES,)*2)
        os.sched_setaffinity(0, {6 if cohort == 'R' else 7})
        assert not target.exists(), 'fresh report worker output required'
        fresh = True
        binding = module('potential_tightening_report_binding', HERE/'binding.py')
        config = read(HERE/'contract.json'); config_limits(config)
        binding.check_contract(config)
        contract_hash = sha(HERE/'contract.json')
        phase = 'production_receipts'
        production, supervisor = accepted_production(run, config, contract_hash)
        raw = next(arm for arm in production['arms'] if arm['cohort'] == cohort)
        phase = 'input_identity'
        inputs = binding.load_inputs(config, Path(work), cohort, effective)
        phase = 'fresh_independent_replay'
        checker = module('potential_tightening_report_checker', HERE/'independent.py')
        result = replay(cohort, inputs, raw, checker, config['old_arms'][cohort], config['parent50_arms'][cohort])
        result.update(parent50_evidence_sha256=config['parent50_evidence']['sha256'],
                      production_arm_sha256=sha(Path(run)/cohort/'results.json'),
                      production_results_sha256=sha(Path(run)/'results.json'),
                      production_supervisor_sha256=sha(Path(run)/'supervisor.json'),
                      report_worker_seconds=time.monotonic()-started,
                      report_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        number(result['report_worker_seconds'], WORKER_SECONDS)
        integer(result['report_peak_rss_kib'], 1, ADDRESS_SPACE_BYTES//1024)
        phase = 'worker_publication'
        if time.monotonic() >= effective:
            raise HardDeadline('report deadline before worker publication')
        write(target, result)
        if time.monotonic() >= effective:
            raise HardDeadline('report deadline after worker publication')
        return result
    except BaseException as error:
        if fresh:
            emergency_deadline = min(time.monotonic()+10, effective+10)
            withdraw_worker(target, {**failure_result(error), 'phase': phase,
                            'seconds': time.monotonic()-started}, emergency_deadline)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cohort', choices=COHORTS, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--deadline', type=float, required=True)
    args = parser.parse_args()
    worker(args.cohort, args.work, args.run, args.output, args.deadline)
