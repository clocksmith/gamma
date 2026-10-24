"""Independent item50 certificate replay; private inputs require accepted production.

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
PRODUCTION_COUNTERS = ('repeated_occurrence_work', 'unique_range_queries',
                       'unique_entries_extracted', 'old_trie_transitions')
GEOMETRY_FIELDS = ('source_characters', 'full_groups', 'full_distinct_entries',
                   'exact_ban_occurrences')
SHARED = 'Pinned input/parser binding; item33 Index and suffix/partition/ban verifier.'
ARM_FIELDS = set(('schema complete validation_loaded cohort contract_sha256 bindings_sha256 '
    'source_identity_sha256 banned_set_sha256 parent_certificate_sha256 checked_proof_sha256 '
    'top_entries_sha256 old_occurrence_order_sha256 old_path_terms_sha256 fit_problems '
    'old_pool_entries seed_entries old_occurrences geometry denominator path_numerator '
    'old_charge old_numerator old_integer_lower_bound largest_positive_k class_counts rows production_seconds '
    'production_phase_seconds_sha256 production_peak_rss_kib work shared_dependencies '
    'all257_independently_replayed old_certificate_independently_replayed suffix_potential_proof_checked '
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


def proof_shape(proof):
    assert set(proof) == set(PROOF_FIELDS) | set(PRODUCTION_COUNTERS)
    integer(proof['denominator'], 1)
    integer(proof['old_charge'], 0); integer(proof['old_numerator'])
    integer(proof['old_occurrences'], 0)
    hash_string(proof['occurrence_sha256'])
    assert type(proof['path_numerators']) is dict and proof['path_numerators']
    for pid, value in proof['path_numerators'].items():
        assert type(pid) is str
        integer(value)
    assert set(proof['class_counts']) == set(proof['top_entries']) == {'1', '2'}
    for support in ('1', '2'):
        count = integer(proof['class_counts'][support], 0)
        entries = proof['top_entries'][support]
        assert type(entries) is list and len(entries) == min(256, count)
        for entry in entries:
            assert type(entry) is list and len(entry) == 3
            integer(entry[0], 0); integer(entry[1], 0); integer(entry[2], 1)
        assert entries == sorted(entries, key=lambda e: (-e[0], e[1], e[2]))
        assert len({tuple(e[1:]) for e in entries}) == len(entries)
    assert type(proof['rows']) is list and len(proof['rows']) == 257
    for k, row in enumerate(proof['rows']):
        assert set(row) == {'k', 'charge', 'one_owner_slots', 'shared_slots',
                            'numerator', 'integer_lower_bound'}
        for value in row.values():
            integer(value)
        assert row['k'] == k and row['charge'] >= 0
        assert 0 <= row['one_owner_slots'] <= min(k, proof['class_counts']['1'])
        assert 0 <= row['shared_slots'] <= proof['class_counts']['2']
        assert row['one_owner_slots']+row['shared_slots'] <= 256
        assert row['numerator'] == sum(proof['path_numerators'].values())-row['charge']
        assert row['integer_lower_bound'] == -(-row['numerator']//proof['denominator'])
    for key in PRODUCTION_COUNTERS:
        integer(proof[key], 0)
    assert proof['unique_entries_extracted'] <= 256
    assert proof['unique_range_queries'] >= proof['unique_entries_extracted']
    assert proof['old_trie_transitions'] >= proof['old_occurrences']


def accepted_production(run, config, contract_hash):
    """Only run receipts are read here; this must precede all nine-file access."""
    config_limits(config)
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
        proof_shape(arm['proof'])
        assert set(arm['proof']['path_numerators']) == {str(pid) for pid in config['fit_ids']}
        exact(read(run/arm['cohort']/'results.json'), arm)
    return production, supervisor


def replay(cohort, inputs, raw, checker, expected_old):
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
                            expected_occurrence_sha256=raw['proof']['occurrence_sha256'])
    checked = shaped(checked)
    proof_shape(raw['proof'])
    for key in PROOF_FIELDS:
        exact(raw['proof'][key], checked[key])
    assert checked['old_bellman_edges_checked'] == checked['old_occurrences']
    assert checked['tight_suffix_positions_checked'] == geometry['source_characters']
    assert checked['streamed_allowed_depths'] == geometry['full_distinct_entries']
    assert raw['proof']['repeated_occurrence_work'] <= checked['new_occurrence_contributions']
    return sanitize(cohort, inputs, raw, checked, geometry)


def sanitize(cohort, inputs, raw, checked, geometry):
    """Explicit public allowlist: no raw source, PID paths, q, or top identities."""
    proof = {key: checked[key] for key in PROOF_FIELDS}
    paths = checked['path_numerators']
    denominator, old = checked['denominator'], checked['old_numerator']
    return {'schema': 'gamma.potential-lift.report-arm.v1', 'complete': True,
            'validation_loaded': False, 'cohort': cohort,
            'contract_sha256': raw['contract_sha256'],
            'bindings_sha256': digest(inputs['bindings']),
            'source_identity_sha256': digest(inputs['source_hashes']),
            'banned_set_sha256': digest(sorted(inputs['banned'])),
            'parent_certificate_sha256': digest(inputs['parent_certificate']),
            'checked_proof_sha256': digest(proof),
            'top_entries_sha256': digest(checked['top_entries']),
            'old_occurrence_order_sha256': checked['occurrence_sha256'],
            'old_path_terms_sha256': digest([paths[pid] for pid in sorted(paths)]),
            'fit_problems': len(inputs['texts']), 'old_pool_entries': len(inputs['pool']),
            'seed_entries': len(inputs['seed']), 'old_occurrences': checked['old_occurrences'],
            'geometry': geometry, 'denominator': denominator,
            'path_numerator': sum(paths.values()), 'old_charge': checked['old_charge'],
            'old_numerator': old, 'old_integer_lower_bound': -(-old//denominator),
            'largest_positive_k': max((row['k'] for row in checked['rows']
                                       if row['integer_lower_bound'] > 0), default=None),
            'class_counts': checked['class_counts'], 'rows': checked['rows'],
            'production_seconds': raw['seconds'],
            'production_phase_seconds_sha256': digest(raw['phase_seconds']),
            'production_peak_rss_kib': raw['peak_rss_kib'],
            'work': {**{key: raw['proof'][key] for key in PRODUCTION_COUNTERS},
                     **{key: checked[key] for key in ('old_bellman_edges_checked',
                         'tight_suffix_positions_checked', 'streamed_allowed_depths',
                         'new_entries_streamed', 'new_occurrence_contributions')}},
            'shared_dependencies': SHARED,
            'all257_independently_replayed': True,
            'old_certificate_independently_replayed': True,
            'suffix_potential_proof_checked': True}


def failure_result(error):
    # Exception strings can contain source paths or input data; retain only type.
    name = type(error).__name__ if isinstance(error, BaseException) else 'ReportFailure'
    return {'schema': 'gamma.potential-lift.report.v1', 'complete': False,
            'validation_loaded': False, 'failure_type': name, 'verdicts': None,
            'predictions': {'P1': None, 'P2': None, 'P3': None},
            'm1_claim': False, 'packet_or_witness_claim': False}


def markdown(result):
    if result['complete'] is not True:
        return '# Item 50 incomplete\n\nIndependent report incomplete; no verdict. Partial artifacts are retained.\n'
    lines = ['# Item 50 potential-lift certificate', '',
             'Exact fixed-source bounds for F = 10C − N with at most 256 paid entries.',
             'One-owner means occurrence in exactly one source ID; it does not imply semantic reuse.', '',
             '| Cohort | k | Integer lower bound | One-owner / shared charge slots |',
             '| --- | ---: | ---: | --- |']
    ladder = (0, 1, 2, 4, 8, 16, 32, 64, 128, 256)
    for arm in result['arms']:
        for k in ladder:
            row = arm['rows'][k]
            lines.append(f"| {arm['cohort']} | {k} | {row['integer_lower_bound']} | {row['one_owner_slots']} / {row['shared_slots']} |")
    lines += ['', 'All 257 exact rows are retained in results.json. Positive values exclude aggregate C/N <= 10% only for the fixed cohort and stated support-constrained dictionary class. Nonpositive values are inconclusive; a unique required character may make small-k classes infeasible.',
              '', 'Fresh independent all-depth traversal agrees with the production certificate. '+SHARED,
              '', 'Predictions: '+json.dumps(result['predictions'], sort_keys=True),
              '', 'A positive bound does not establish that the support budget can cover these sources, or that any larger budget is feasible.',
              '', 'Only the exact named original item13 qualification receipts are reused; no fresh qualification jobs run. Item23\'s later unchanged-source exit137 remains a separate inherited failure.',
              '', 'No cases, source execution, feasible dictionary witness, packet decoding, package-cost result, canonical-policy result, optimality or M1 claim.']
    return '\n'.join(lines)+'\n'


def remove_success(output):
    """Minimal withdrawal only; never swallow the caller's hard deadline."""
    output = Path(output)
    for name in ('results.json', 'REPORT.md', 'results.json.pending', 'REPORT.md.pending'):
        try:
            (output/name).unlink(missing_ok=True)
        except Exception:
            pass


def withdraw(output, error):
    """Caller supplies the absolute failure-I/O guard; hard deadlines propagate.

    Withdraw both success markers before starting potentially slow failure
    serialization/writes. Ordinary per-file errors remain independent, but a
    BaseException deadline from ANY supervisor class ends all further I/O.
    """
    output = Path(output)
    remove_success(output)
    failed = failure_result(error)
    for name, text in (('REPORT.md', markdown(failed)),
                       ('results.json', json.dumps(failed, sort_keys=True, indent=2)+'\n')):
        target = output/name
        try:
            output.mkdir(parents=True, exist_ok=True)
            temporary = output/(name+'.failure')
            temporary.write_text(text); temporary.replace(target)
        except Exception:
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
        # The owner's alarm may already have fired. Do not start new receipt
        # writes here; the supervisor owns a separately bounded failure phase.
        remove_success(output)
        raise


def combine(run, output, config, elapsed, returncodes):
    run, output = Path(run), Path(output)
    assert not (output/'failure.json').exists()
    config_limits(config)
    number(elapsed, PHASE_SECONDS)
    assert type(returncodes) is list and len(returncodes) == 2
    assert all(type(code) is int and code == 0 for code in returncodes)
    contract_hash = sha(HERE/'contract.json')
    production, supervisor = accepted_production(run, config, contract_hash)
    arms = []
    for cohort, raw in zip(COHORTS, production['arms']):
        assert not (output/(cohort+'-failure.json')).exists()
        arm = read(output/(cohort+'.json'))
        assert set(arm) == ARM_FIELDS
        assert arm['schema'] == 'gamma.potential-lift.report-arm.v1'
        assert arm['complete'] is True and arm['validation_loaded'] is False
        assert arm['cohort'] == cohort and arm['contract_sha256'] == contract_hash
        assert arm['production_arm_sha256'] == sha(run/cohort/'results.json')
        assert arm['production_results_sha256'] == sha(run/'results.json')
        assert arm['production_supervisor_sha256'] == sha(run/'supervisor.json')
        assert arm['bindings_sha256'] == digest(raw['bindings'])
        assert arm['checked_proof_sha256'] == digest({key: raw['proof'][key] for key in PROOF_FIELDS})
        assert arm['top_entries_sha256'] == digest(raw['proof']['top_entries'])
        for key in ARM_FIELDS:
            if key.endswith('_sha256'):
                hash_string(arm[key])
        expected_numbers = {'fit_problems': len(raw['proof']['path_numerators']),
            'old_occurrences': raw['proof']['old_occurrences'],
            'denominator': raw['proof']['denominator'],
            'path_numerator': sum(raw['proof']['path_numerators'].values()),
            'old_charge': raw['proof']['old_charge'], 'old_numerator': raw['proof']['old_numerator'],
            'old_integer_lower_bound': -(-raw['proof']['old_numerator']//raw['proof']['denominator']),
            'production_peak_rss_kib': raw['peak_rss_kib']}
        for key, value in expected_numbers.items():
            exact(arm[key], value)
        integer(arm['seed_entries'], 1, 256)
        integer(arm['old_pool_entries'], arm['seed_entries'])
        exact(arm['old_pool_entries'], config['old_arms'][cohort]['pool_entries'])
        assert arm['source_identity_sha256'] == digest(config['source_hashes'][cohort])
        assert arm['parent_certificate_sha256'] == digest(config['old_arms'][cohort]['certificate'])
        assert arm['banned_set_sha256'] == raw['bindings']['bans_sha256']
        assert arm['source_identity_sha256'] == raw['bindings']['source_hashes_sha256']
        assert arm['old_occurrence_order_sha256'] == raw['proof']['occurrence_sha256']
        assert arm['old_path_terms_sha256'] == digest([raw['proof']['path_numerators'][pid]
                                                      for pid in sorted(raw['proof']['path_numerators'])])
        assert arm['production_phase_seconds_sha256'] == digest(raw['phase_seconds'])
        assert arm['shared_dependencies'] == SHARED
        assert set(arm['work']) == set(PRODUCTION_COUNTERS) | {
            'old_bellman_edges_checked', 'tight_suffix_positions_checked', 'streamed_allowed_depths',
            'new_entries_streamed', 'new_occurrence_contributions'}
        for value in arm['work'].values():
            integer(value, 0)
        for key in PRODUCTION_COUNTERS:
            exact(arm['work'][key], raw['proof'][key])
        assert arm['work']['old_bellman_edges_checked'] == arm['old_occurrences']
        assert arm['work']['tight_suffix_positions_checked'] == raw['full_shape']['source_characters']
        assert arm['work']['streamed_allowed_depths'] == raw['full_shape']['full_distinct_entries']
        assert arm['work']['new_entries_streamed'] <= arm['work']['streamed_allowed_depths']
        assert arm['work']['new_occurrence_contributions'] >= arm['work']['new_entries_streamed']
        exact(arm['rows'], raw['proof']['rows'])
        exact(arm['largest_positive_k'], max((row['k'] for row in arm['rows']
                                             if row['integer_lower_bound'] > 0), default=None))
        exact(arm['class_counts'], raw['proof']['class_counts'])
        exact(arm['geometry'], raw['full_shape'])
        exact(arm['production_seconds'], raw['seconds'])
        number(arm['report_worker_seconds'], min(WORKER_SECONDS, elapsed))
        integer(arm['report_peak_rss_kib'], 1, ADDRESS_SPACE_BYTES//1024)
        assert arm['all257_independently_replayed'] is True
        assert arm['old_certificate_independently_replayed'] is True
        assert arm['suffix_potential_proof_checked'] is True
        arms.append(arm)
    predictions = {'P1': all(a['path_numerator'] == config['old_arms'][a['cohort']]['certificate']['relaxed_paths_numerator']
                              and a['rows'][0]['numerator'] >= a['old_numerator'] for a in arms),
                   'P2': any(row['integer_lower_bound'] > 0 for a in arms for row in a['rows'][1:]),
                   'P3': any(a['rows'][256]['integer_lower_bound'] > 0 for a in arms)}
    assert predictions['P1'] is True
    return {'schema': 'gamma.potential-lift.report.v1', 'complete': True,
            'validation_loaded': False, 'population': 'fixed300_fit_only',
            'contract_sha256': contract_hash, 'production_results_sha256': sha(run/'results.json'),
            'production_supervisor_sha256': sha(run/'supervisor.json'),
            'production_seconds': production['seconds'], 'report_seconds': elapsed,
            'arms': arms, 'verdicts': {'all257_replayed': True,
                'k0_preserves_old_bound': all(a['rows'][0]['numerator'] >= a['old_numerator'] for a in arms)},
            'predictions': predictions,
            'qualification': {'authority': 'Exact original item13 control/scope_joint receipts by source hash only',
                              'fresh_jobs': 0, 'new_witness_packets': 0,
                              'inherited_failure': 'Item23 later unchanged-source exit137 remains separate.'},
            'coverage_feasibility': 'Positive bounds do not establish coverage feasibility at this or any larger support budget.',
            'shared_dependencies': SHARED, 'm1_claim': False, 'packet_or_witness_claim': False,
            'validation_or_cases_opened': False, 'optimality_claim': False}


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
        binding = module('potential_lift_report_binding', HERE/'binding.py')
        config = read(HERE/'contract.json'); config_limits(config)
        binding.check_contract(config)
        contract_hash = sha(HERE/'contract.json')
        phase = 'production_receipts'
        production, supervisor = accepted_production(run, config, contract_hash)
        raw = next(arm for arm in production['arms'] if arm['cohort'] == cohort)
        phase = 'input_identity'
        inputs = binding.load_inputs(config, Path(work), cohort, effective)
        phase = 'fresh_independent_replay'
        checker = module('potential_lift_report_checker', HERE/'independent.py')
        result = replay(cohort, inputs, raw, checker, config['old_arms'][cohort])
        result.update(production_arm_sha256=sha(Path(run)/cohort/'results.json'),
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
        signal.setitimer(signal.ITIMER_REAL, 10)
        if fresh:
            try:
                target.unlink(missing_ok=True)
            finally:
                write(Path(output)/(cohort+'-failure.json'), {
                    **failure_result(error), 'phase': phase, 'seconds': time.monotonic()-started})
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
