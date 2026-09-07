"""Read-only closed-result audit. This script never scans or decodes a population."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import sys
import time

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
ID = 'fx2_causal_field_opportunity_q0_v1'
JOB_ID = '20260907T141904Z_b82cd55283'
JOB = 'operations/adaptive/completed/909_' + JOB_ID + '.json'
REPORT = 'results/' + ID + '/report.json'
PLAN = 'operations/provenance/fx2_causal_field_opportunity_q0_v1_execution.json'
RUNNER = 'tools/causal_field_opportunity_gate_v2.py'
SEEN = {}


def read(name, maximum=8 * 1024**2):
    path = ROOT / name
    assert path.resolve() == path and path.is_relative_to(ROOT), name
    before = path.lstat()
    assert stat.S_ISREG(before.st_mode) and before.st_size <= maximum, name
    value = path.read_bytes()
    after = path.lstat()
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    assert identity(before) == identity(after), name
    row = {'path': name, 'bytes': len(value), 'sha256': hashlib.sha256(value).hexdigest()}
    assert name not in SEEN or SEEN[name] == row, name
    SEEN[name] = row
    return value


def bound(reference):
    data = read(reference['path'])
    assert hashlib.sha256(data).hexdigest() == reference['sha256'].removeprefix('sha256:'), reference
    return data


def load(name):
    return json.loads(read(name))


def command_digest(argv):
    return hashlib.sha256(b'\0'.join(os.fsencode(x) for x in argv)).hexdigest()


def main():
    started, cpu = time.monotonic(), time.process_time()
    assert os.sched_getaffinity(0) == {3}
    assert Path(os.environ['TMPDIR']) == OUT / 'tmp'
    job = load(JOB)
    assert job['job_id'] == JOB_ID and job['candidate_id'] == ID
    assert job['state'] == 'completed' and job['returncode'] == 0
    assert not list((ROOT / 'operations/adaptive/running').glob('*' + JOB_ID + '.json'))
    resources = job['execution_resources']
    assert resources['cleanup_complete'] is True
    guard = load(resources['guard_path'])
    assert guard['status'] == 'complete' and guard['returncode'] == 0
    assert all(value is False for value in guard['guards'].values())
    assert all(value is True for value in guard['measurements'].values())
    assert not Path(resources['cgroup_path']).exists()

    contract = json.loads(bound(job['experiment']))
    assert contract['experimentId'] == ID and contract['status'] == 'frozen'
    assert len(contract['inputs']) == 204
    inputs = {row['path']: row for row in contract['inputs']}
    assert len(inputs) == len(contract['inputs'])
    buffers = {name: bound(reference) for name, reference in inputs.items()}
    plan = json.loads(buffers[PLAN])
    report = load(REPORT)
    assert plan['candidate_id'] == ID == report['candidate_id']
    assert report['job_id'] == JOB_ID and report['experiment'] == job['experiment']
    assert report['execution_plan'] == inputs[PLAN]
    assert report['input_bytes'] == sum(map(len, buffers.values()))
    assert report['local_source_paths'] == sorted(plan['source_paths'])
    assert len(plan['source_paths']) == 193 and len(set(plan['source_paths'])) == 193
    assert set(plan['source_paths']) <= set(inputs)
    assert job['runner'] == {'path': RUNNER, 'sha256': inputs[RUNNER]['sha256']}
    for reference in (job['runner'], job['execution_guard'], job['candidate_revision'], job['proposal']):
        bound(reference)

    # The imports below are already included in the authenticated input closure.
    sys.path.insert(0, str(ROOT / 'tools'))
    import enwiki9_python_source_closure as closure
    import enwiki9_candidate_revisions as revisions
    import research_contracts as contracts
    source_closure = {p.relative_to(ROOT).as_posix() for p in closure.local_source_closure(
        [ROOT / RUNNER, ROOT / 'tools/enwiki9_lab.py', ROOT / job['execution_guard']['path']])}
    assert source_closure <= set(plan['source_paths'])
    revision = json.loads(bound(job['candidate_revision']))
    manifest = revisions.candidate_manifest(ID)
    assert manifest == revision['files']
    assert revisions.candidate_tree_digest(manifest) == job['candidate_tree_sha256'] == revision['candidateTreeSha256']
    for row in revision['files']:
        data = read(row['blobPath'])
        assert len(data) == row['bytes'] and hashlib.sha256(data).hexdigest() == row['sha256']
    assert report['candidate_revision'] == {
        'candidateId': ID, 'candidateTreeSha256': job['candidate_tree_sha256'], 'receipt': job['candidate_revision']}
    validations = {}
    for path in (JOB, job['experiment']['path'], job['candidate_revision']['path'],
                 'results/' + ID + '/decision.json'):
        validations[path] = contracts.validate_artifact(ROOT / path)
    decision = load('results/' + ID + '/decision.json')
    assert decision['promotionPass'] is False and decision['killPass'] is False
    assert decision['objectiveCreditBytes'] == 0 and decision['evidenceClass'] == 'diagnostic'
    assert report['runtime'] == plan['runtime']
    runtime_path = Path(plan['runtime']['path'])
    assert runtime_path.resolve() == runtime_path and runtime_path.is_file()
    runtime = runtime_path.read_bytes()
    assert len(runtime) == plan['runtime']['bytes']
    assert hashlib.sha256(runtime).hexdigest() == plan['runtime']['sha256']

    # Bind both the guard's inner command and the lab's recorded wrapper command.
    assert command_digest(guard['command']) == guard['command_sha256']
    assert guard['command'][-2:] == [str(runtime_path), str(ROOT / RUNNER)]
    assert guard['command'][:3] == ['/usr/bin/taskset', '--cpu-list', '2']
    caps = plan['bounds']
    assert all(job['resource_budget'][k] == v == resources['budget'][k] for k, v in caps.items())
    assert guard['label'] == JOB_ID and guard['phase'] == 'diagnostic'
    assert guard['cgroup']['path'] == resources['cgroup_path']
    assert guard['cgroup']['inode'] == resources['cgroup_inode']
    assert guard['cgroup']['joined_before_exec'] is True
    assert guard['cgroup']['memory_max_bytes'] == caps['memory_bytes']
    assert guard['temporary_disk_limit_bytes'] == caps['scratch_bytes']
    assert guard['max_logical_cpus'] == 1 and report['cpu_affinity'] == caps['cpus'] == [2]
    assert guard['wall_time_limit_seconds'] is None
    assert report['independent_wall_limit_seconds'] == caps['wall_seconds'] == 120
    assert report['elapsed_seconds'] < 120 and report['cpu_seconds'] < 60 and guard['elapsed_s'] < 120
    assert guard['peaks']['cgroup_memory_peak_bytes'] < caps['memory_bytes']
    assert guard['peaks']['max_sampled_scratch_allocated_bytes'] < caps['scratch_bytes']
    assert not any(guard['cgroup_events']['delta'].values())
    marker = 'run_logs/adaptive/' + JOB_ID + '.resources/phases.jsonl'
    assert guard['phase_marker_path'] == str(ROOT / marker)
    markers = [json.loads(line) for line in read(marker).splitlines()]
    assert [row['event'] for row in markers] == ['worker_start', 'opportunity_scan_start', 'opportunity_scan_complete']
    assert [row['event'] for row in guard['phase_markers']] == [row['event'] for row in markers]
    assert guard['latest_sample']['processes'] == []
    limit_kib = str(caps['memory_bytes'] // 1024)
    wrapped = [str(runtime_path), str(ROOT / job['execution_guard']['path']), '--limit-kib', limit_kib,
               '--official-decimal-limit-kib', limit_kib, '--limit-mode', 'tree',
               '--cgroup-path', resources['cgroup_path'], '--cgroup-memory-max-bytes', str(caps['memory_bytes']),
               '--temporary-disk-limit-bytes', str(caps['scratch_bytes']), '--phase-marker-path', str(ROOT / marker),
               '--max-logical-cpus', '1', '--guard-json', str(ROOT / resources['guard_path']),
               '--label', JOB_ID, '--phase', 'diagnostic']
    for name in sorted(guard['scratch_paths']):
        wrapped += ['--scratch-path', name]
    wrapped += ['--', *guard['command']]
    assert command_digest(wrapped) == resources['guard_command_sha256']

    population = plan['population']
    original = json.loads(buffers[population['terminal_result_path']])['program_stats']['phase']['adapter']
    assert report['adapter'] == original
    assert report['raw_bytes'] == population['raw_bytes'] == original['raw_bytes'] == 250000
    assert report['raw_sha256'] == population['raw_sha256'] == original['raw_sha256']
    modeled = buffers[population['modeled_path']]
    assert report['modeled_bytes'] == len(modeled) == original['modeled_bytes'] == 151210
    assert report['modeled_sha256'] == hashlib.sha256(modeled).hexdigest() == original['modeled_sha256']
    assert report['every_byte_state_agreement'] is True and report['exact_raw_identity'] is True
    assert report['retained_terminal_state_agreement'] is True
    assert len(bytes.fromhex(report['state_chain_sha256'])) == 32
    d = report['diagnostics']
    assert sum(d['eligibility'].values()) == d['start_values'] == 141
    assert d['eligibility']['eligible'] == 106 and d['eligibility']['no_earlier_field'] == 35
    for name in ('conditional', 'recency', 'rotated'):
        assert sum(d[name].values()) == 106
    assert d['conditional'] == {'exact_compatible_hit': 0, 'incompatible_wrt_entry_state': 0,
        'no_exact_first_value': 50, 'no_matching_template': 56,
        'no_template_first_key_later_key': 0, 'no_template_later_key': 0}
    assert d['recency']['compatible_route_hit'] == 50 and d['rotated']['no_exact_tuple'] == 106
    assert d['inherited_selected_starts'] == original['selected_values'] == 0
    assert len(d['first_events']) == d['first_event_limit'] == 32
    assert len(d['first_events']) + d['omitted_events'] == 141 + d['parser_invalidation_transitions']
    assert d['parser_invalidation_transitions'] == original['rejected_invocations'] == 84
    assert d['end_state']['finished'] is True and d['end_state']['failed'] is False
    assert d['end_state']['parser_prefix_incomplete'] is False and d['end_state']['wrt_event_incomplete'] is False
    assert report['archive_bytes'] is None and report['complete_package_bytes'] is None
    assert report['objective_credit_bytes'] == d['objective_credit_bytes'] == 0
    assert d['qualification_authority'] is False and d['corpus_execution_authorized'] is False
    for name, row in list(SEEN.items()):
        assert hashlib.sha256(read(name)).hexdigest() == row['sha256']
    audit = {'schema': 'gamma.enwiki9.causal-field-opportunity-terminal-review.v1', 'verdict': 'passed',
        'job_id': JOB_ID, 'candidate_id': ID, 'input_files_verified': 204,
        'source_paths_verified': 193, 'resolved_source_closure_files': len(source_closure),
        'candidate_revision_tree_and_blobs_verified': True, 'guard_commands_and_closure_verified': True,
        'report': SEEN[REPORT], 'job': SEEN[JOB], 'guard': SEEN[resources['guard_path']],
        'raw_bytes': 250000, 'modeled_bytes': 151210, 'full_original_T_stats_match': True,
        'reported_per_byte_agreement': True, 'partition_arithmetic_pass': True,
        'counts': {'value_starts': 141, 'no_earlier_field': 35, 'eligible': 106,
            'no_prior_template': 56, 'same_route_without_exact_first_value': 50,
            'exact_compatible_hits': 0, 'recency_compatible_hits': 50,
            'parser_invalidations': 84, 'completed_invocations': original['completed_invocations'],
            'associations': original['associations'], 'evictions': original['evictions'],
            'retained_examples': 32, 'omitted_examples': d['omitted_events']},
        'resources': {'guard_samples': guard['sample_count'], 'guard_elapsed_seconds': guard['elapsed_s'],
            'peak_cgroup_bytes': guard['peaks']['cgroup_memory_peak_bytes'],
            'sampled_peak_tree_rss_kib': guard['peaks']['max_sampled_tree_rss_kib'],
            'runner_reported_ru_maxrss_kib': report['peak_rss_kib'],
            'scope': 'Shared-host discovery; sampled RSS, reported ru_maxrss and cgroup peak are distinct measurements.'},
        'conclusion': 'All eligible starts are explained by missing prior template history or a missing exact first value on an otherwise repeated route. No recorded WRT-state or entry-alignment exclusion explains T inactivity.',
        'next_question': 'Within recurring template/target routes, does an earlier completed field other than the physical first field supply repeated byte-identical selector values?',
        'limitations': ['No scan, replay, decoding or probability inference was performed by this audit.',
            'Per-byte equality is supported by the closed receipt and reviewed hash-bound runner; its rolling chain was not recomputed.',
            'No exact retained tuple hits does not establish global uniqueness of first-field values.',
            'The first 32 events are an opening-biased sample; invalidation context does not classify all grammar failures.',
            'No archive, compression gain, standalone package, promotion or qualification credit.'],
        'archive_bytes': None, 'complete_package_bytes': None, 'objective_credit_bytes': 0,
        'canonical_validations': validations, 'audit_cpu_seconds': time.process_time() - cpu,
        'audit_wall_seconds': time.monotonic() - started,
        'audit_peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    (OUT / 'verified-files.json').write_text(json.dumps(list(SEEN.values()), indent=2) + '\n')
    (OUT / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
