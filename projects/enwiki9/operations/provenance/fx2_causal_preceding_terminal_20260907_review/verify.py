"""Independently inspect one authorized closed replay; execute no codec."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
import traceback
from types import ModuleType

ROOT = Path('/home/x/deco/gamma/projects/enwiki9')
OUT = Path(__file__).resolve().parent
ID = 'fx2_causal_preceding_wrt250k_q0_v1'
JID = '20260907T153225Z_61daf1a29b'
JOB = 'operations/adaptive/completed/090_' + JID + '.json'
JOB_SHA = 'd08d8ab6e547c80c2fd41bf4b854261313a2559767ea30133dc373dee63930df'
CONTRACT_SHA = 'fcfa667d4048e1a75a681844918ce2398ba4a94c0280550d87a5d50c825980d5'
RUNNER = 'tools/fx2_causal_field_preceding_gate_v2.py'
CORE = 'tools/fx2_causal_field_preceding_replay_v1.py'
ARMS, PHASES = 'PKTORS', ('encode', 'decode', 'repeat')
CAPS = {'cpus': [2], 'memory_bytes': 1073741824, 'scratch_bytes': 268435456,
        'swap_bytes': 0, 'wall_seconds': 900}
BASIS = 'operations/provenance/fx2_causal_field_wrt_terminal_20260907/review/audit_terminal.py'
BASIS_SHA = 'd931667cc58a2d488c3ff7084390db1d7471a257d990b36fc08490d3890d5f30'
basis_bytes = (ROOT / BASIS).read_bytes()
assert hashlib.sha256(basis_bytes).hexdigest() == BASIS_SHA
helper = ModuleType('_closed_terminal_read_helpers')
helper.__file__ = str(ROOT / BASIS)
exec(compile(basis_bytes, str(ROOT / BASIS), 'exec'), helper.__dict__)
require, sha, norm = helper.require, helper.sha, helper.normalized
fingerprint, verify, load, equal = helper.fingerprint, helper.verify, helper.load, helper.equal
RESULT = ROOT / 'results' / ID
R = lambda name: RESULT / name
MEANINGFUL = (*helper.MEANINGFUL, 'adapter_policy_id', 'adapter_constructor_arm', 'decoder_arm_option_bytes')
cmdsha = lambda argv: sha(b'\0'.join(map(os.fsencode, argv)))


def audit(output):
    require(os.sched_getaffinity(0) == {3}, 'review CPU differs')
    require(Path(os.environ['TMPDIR']) == OUT / 'tmp', 'review scratch differs')
    verify({'path': JOB, 'sha256': JOB_SHA})
    job = load(JOB)
    require(job['job_id'] == JID and job['candidate_id'] == ID and job['state'] == 'completed'
            and job['returncode'] == 0 and job['finished_at'], 'not the authorized completed job')
    require(not list((ROOT / 'operations/adaptive/running').glob('*' + JID + '.json')), 'job still recorded running')
    resources = job['execution_resources']
    require(resources['cleanup_complete'] is True and not resources.get('cleanup_errors'), 'cleanup incomplete')
    require(not any(Path(group['path']).exists() for group in resources['groups']), 'owned cgroup remains')
    guard = load(resources['guard_path'])
    require(guard['status'] == 'complete' and guard['returncode'] == 0 and guard['label'] == JID,
            'guard not closed or wrong owner')
    require(all(value is False for value in guard['guards'].values())
            and all(value is True for value in guard['measurements'].values()), 'guard failure or missing resource evidence')
    require(guard['latest_sample']['processes'] == [] and guard['latest_sample']['tree_live_threads'] == 0,
            'guard final process sample not empty')
    output['closed_identity_before_payload_reads'] = True
    for name in ('experiment', 'runner', 'execution_guard', 'candidate_revision', 'proposal'):
        verify(job[name])
    require(norm(job['experiment']['sha256']) == CONTRACT_SHA, 'contract authorization changed')
    contract = load(job['experiment']['path'])
    inputs = {ref['path']: ref for ref in contract['inputs']}
    require(len(inputs) == len(contract['inputs']) == 209, 'input inventory differs')
    require(contract['experimentId'] == ID and contract['status'] == 'frozen'
            and contract['objective']['targetScoreBytes'] == 99000000, 'frozen objective differs')
    for ref in inputs.values():
        verify(ref)
    planref = next(ref for ref in contract['inputs'] if ref.get('id') == 'preceding-field-gate-plan')
    plan = load(planref['path'])
    require(plan['candidate_id'] == ID and plan['resources'] == CAPS, 'execution plan differs')
    pop = plan['population']
    require(job['runner'] == {'path': RUNNER, 'sha256': inputs[RUNNER]['sha256']}, 'runner binding differs')
    require(norm(inputs[RUNNER]['sha256']) == '45fdf46247353a9c7889f9e216da4e5e204b133d6d8d89583252a0d3b7f6e29c'
            and norm(inputs[CORE]['sha256']) == 'db81958de9edd98ebdb61158a8ceb3a7c117bbf024b423dd5d04bfea7564754a',
            'independently reviewed source differs')
    sys.path[:0] = [str(ROOT / 'tools'), str(ROOT)]
    import enwiki9_python_source_closure as closure
    import research_contracts as contracts
    # This helper is reviewer tooling, not an asserted codec dependency.
    fingerprint('tools/enwiki9_candidate_revisions.py')
    import enwiki9_candidate_revisions as revisions
    package_names = {ref['path'] for ref in plan['local_package_files']}
    codec_closure = {p.relative_to(ROOT).as_posix() for p in closure.local_source_closure([ROOT / CORE])}
    require(codec_closure <= package_names, 'static codec dependency omitted from package')
    required_dynamic = {'tools/causal_field_preceding_adapter250k_v1.py', 'tools/causal_field_preceding_selector_v1.py',
        'tools/causal_field_wrt_adapter_v1.py', 'tools/causal_field_dependency_v1.py', 'tools/wrt_exact.py',
        'tools/causal_field_parent_coder_v1.py'}
    require(required_dynamic <= package_names <= set(inputs), 'dynamic dependency omitted')
    declared_closure = {p.relative_to(ROOT).as_posix() for p in closure.local_source_closure([ROOT / CORE, ROOT / 'tools/research_contracts.py'])}
    declared_closure.update(p.relative_to(ROOT).as_posix() for p in (ROOT / 'lib').glob('*.py'))
    declared_closure.update(required_dynamic | {RUNNER})
    require(declared_closure <= set(inputs), 'required runner/driver/source closure incomplete')
    revision = load(job['candidate_revision']['path'])
    manifest = revisions.candidate_manifest(ID)
    require(manifest == revision['files'] and revisions.candidate_tree_digest(manifest)
            == revision['candidateTreeSha256'] == job['candidate_tree_sha256'], 'candidate tree or current files differ')
    for row in manifest:
        verify({'path': row['blobPath'], 'sha256': row['sha256'], 'bytes': row['bytes']})
    output['canonical_validations'] = {name: contracts.validate_artifact(ROOT / name)
        for name in (JOB, job['experiment']['path'], job['candidate_revision']['path'])}
    for ref in plan['runtime_files']:
        path = Path(ref['path'])
        require(path.resolve() == path and path.is_file() and path.stat().st_size == ref['bytes'], 'runtime path/size differs')
        with path.open('rb') as stream:
            require(hashlib.file_digest(stream, 'sha256').hexdigest() == norm(ref['sha256']), 'runtime changed')

    stage = load(R('stage-decision.json'))
    require(stage['status'] == 'passed' and stage['candidate_id'] == ID and stage['experiment'] == job['experiment']
            and stage['child_closure_ok'] is True, 'stage identity or closure failed')
    helper.no_score(stage)
    for key in ('comparison', 'artifacts', 'artifact_index_diagnostics'):
        verify(stage[key])
    comparison = load(stage['comparison']['path'])
    package = load(R('package.json'))
    helper.no_score(comparison)
    helper.no_score(package)
    require(package['counted_files'] == plan['local_package_files'] and len(package_names) == 7
            and package['counted_bytes'] == sum(ref['bytes'] for ref in package['counted_files']) == 72134,
            'seven-file source accounting differs')
    require(package['decoder_arm_option_bytes_per_archive'] == 1 and package['dependency_closure_complete'] is False,
            'option or incomplete package claim differs')
    for ref in package['external_decode_dependencies']:
        verify(ref)
    require(package['external_decode_dependency_bytes'] == sum(ref['bytes'] for ref in package['external_decode_dependencies']) == 2831356,
            'external decoding dependencies differ')

    require(all(job['resource_budget'][key] == value == resources['budget'][key] for key, value in CAPS.items()), 'resource budgets differ')
    require(guard['phase'] == 'diagnostic' and guard['cgroup']['path'] == resources['cgroup_path']
            and guard['cgroup']['inode'] == resources['cgroup_inode'] and guard['cgroup']['joined_before_exec'] is True,
            'resource group identity differs')
    require(guard['cgroup']['memory_max_bytes'] == CAPS['memory_bytes'] and guard['temporary_disk_limit_bytes'] == CAPS['scratch_bytes']
            and guard['max_logical_cpus'] == 1 and guard['wall_time_limit_seconds'] is None, 'guard limits differ')
    require(0 <= guard['elapsed_s'] <= 900 and guard['sample_count'] > 0
            and not any(guard['cgroup_events']['delta'].values()), 'resource stop or limit event')
    require(guard['peaks']['cgroup_memory_peak_bytes'] <= CAPS['memory_bytes']
            and guard['peaks']['max_sampled_scratch_allocated_bytes'] <= CAPS['scratch_bytes']
            and guard['peaks']['max_sampled_scratch_logical_bytes'] <= CAPS['scratch_bytes']
            and guard['peaks']['max_sampled_allowed_cpu_count'] == 1, 'sampled bound exceeded')
    require(cmdsha(guard['command']) == guard['command_sha256'] and guard['command'][:3] == ['/usr/bin/taskset', '--cpu-list', '2']
            and guard['command'][-2:] == [plan['python_executable'], str(ROOT / RUNNER)], 'inner guard command differs')
    limit = str(CAPS['memory_bytes'] // 1024)
    wrapped = [plan['python_executable'], str(ROOT / job['execution_guard']['path']), '--limit-kib', limit,
        '--official-decimal-limit-kib', limit, '--limit-mode', 'tree', '--cgroup-path', resources['cgroup_path'],
        '--cgroup-memory-max-bytes', str(CAPS['memory_bytes']), '--temporary-disk-limit-bytes', str(CAPS['scratch_bytes']),
        '--phase-marker-path', guard['phase_marker_path'], '--max-logical-cpus', '1', '--guard-json',
        str(ROOT / resources['guard_path']), '--label', JID, '--phase', 'diagnostic']
    for path in guard['scratch_paths']:
        wrapped.extend(['--scratch-path', path])
    wrapped.extend(['--', *guard['command']])
    require(cmdsha(wrapped) == resources['guard_command_sha256'], 'outer guard command differs')
    outer = stage['outer_controller_admission']
    require(outer['guard_pid'] == job['worker_pid'] and outer['guard_proc_start_ticks'] == job['worker_proc_start_ticks']
            and outer['boot_id'] == resources['boot_id'] and outer['job_id'] == JID
            and outer['proc_start_ticks'] <= job['worker_proc_start_ticks'], 'recorded controller/guard identity differs')
    expected_outer = [plan['python_executable'], str(ROOT / 'tools/enwiki9_lab.py'), 'run', '--candidate', ID,
                      '--max-workers', '1', '--min-free-mib', '16384', '--max-load', '24']
    require(outer['command'] == expected_outer and outer['command_sha256'] == cmdsha(expected_outer)
            and outer['controller_source'] == inputs['tools/enwiki9_lab.py']
            and outer['cwd'] == str(ROOT) and outer['job_wall_budget_seconds'] == 900
            and outer['timer_owner'] == 'enwiki9_lab.wait_for_budgeted_worker'
            and outer['qualification_authority'] is False, 'outer wall-stop controller binding differs')

    index = load(stage['artifacts']['path'])
    diagnostics = load(stage['artifact_index_diagnostics']['path'])
    excludes = {'comparison.json', 'stage-decision.json', 'artifacts.json', 'artifact-index-diagnostics.json'}
    require(diagnostics['complete'] and not diagnostics['errors'] and set(diagnostics['index_metadata_excluded']) == excludes,
            'index not complete')
    indexed = {ref['path'] for ref in index}
    require(len(indexed) == len(index) == diagnostics['indexed_files'], 'duplicate index rows')
    actual = set()
    for path in RESULT.rglob('*'):
        require(not path.is_symlink(), 'symlink in result tree')
        if path.is_file() and path.relative_to(RESULT).as_posix() not in excludes | {'decision.json'}:
            actual.add(path.relative_to(ROOT).as_posix())
    require(actual == indexed, 'result tree not fully indexed')
    for ref in index:
        verify(ref)
    helper.ARMS = ARMS
    require(all(R(name).is_file() for name in helper.expected_outputs(inputs)), 'mandatory output missing')
    for name, ref in inputs.items():
        if Path(name).suffix in ('.py', '.cpp', '.h', '.hpp') or Path(name).name == 'LICENSE':
            verify({**ref, 'path': str(R('work/source/' + name).relative_to(ROOT))})
    for name in ('raw', 'modeled', 'q16', 'dictionary'):
        equal([R('work/' + name + '.bin'), ROOT / pop[name + '_path']])
    rawref, modeledref, qref = (fingerprint(R('work/' + name + '.bin')) for name in ('raw', 'modeled', 'q16'))
    require(rawref['bytes'] == 250000 and modeledref['bytes'] == 151210 and qref['bytes'] == 2419360, 'population coordinates differ')
    projection = load(R('projection.json'))
    original_projection = load(pop['projection_path'])
    require(projection['reused_projection'] == original_projection and projection['source'] == inputs[pop['projection_path']]
            and projection['truth_trace_reprocessed'] is False and projection['native_prediction_rerun'] is False, 'projection reuse differs')
    require(original_projection['q16_sha256'] == qref['sha256'] and original_projection['q16_bytes'] == qref['bytes']
            and original_projection['native_intervals_and_payload_exact'] is True
            and original_projection['decoder_receives_truth_trace'] is False, 'retained projection authority differs')
    parent = fingerprint(pop['parent_archive_path'])
    require(parent['bytes'] == 33429 and parent['sha256'] == original_projection['parent_archive_sha256'], 'parent archive differs')
    with (ROOT / pop['parent_archive_path']).open('rb') as stream:
        prefix = stream.read(46)
    phases = [arm + '-' + op for arm in ARMS for op in PHASES]
    require([row['phase'] for row in stage['commands']] == phases, 'phase count/order differs')
    expected_markers = [(phase, event) for phase in phases for event in ('start', 'end')]
    require([(row['phase'], row['event']) for row in guard['phase_markers'] if row['event'] in ('start', 'end')] == expected_markers,
            'guard phase markers differ')
    arms, phase_rows = {}, []
    for arm in ARMS:
        reports = []
        for op in PHASES:
            phase = arm + '-' + op
            command, report = load(R(phase + '.execution.json')), load(R(phase + '.stdout'))
            require(command == stage['commands'][phases.index(phase)] and command['returncode'] == 0
                    and not command['launch_error'], 'phase execution failed or replaced')
            require(0 < command['elapsed_cap_seconds'] <= 180 and command['elapsed_seconds'] <= command['elapsed_cap_seconds'] + 2,
                    'phase elapsed cap failed')
            source = R('work/' + arm + '-encode.bin') if op == 'decode' else R('work/modeled.bin')
            argv = [plan['python_executable'], '-B', str(ROOT / CORE), op, str(source), str(R('work/' + phase + '.bin')),
                '--sync', str(R('work/' + phase + '.sync')), '--q16', str(R('work/q16.bin')),
                '--dictionary', str(R('work/dictionary.bin')), '--arm', arm, '--prefix', prefix.hex(),
                '--raw-bytes', '250000', '--raw-sha256', rawref['sha256']]
            require(command['command'] == ['/usr/bin/timeout', '--signal=TERM', '--kill-after=2', str(command['elapsed_cap_seconds']), *argv],
                    'separate decoder or phase command differs')
            require(report['operation'] == op and report['arm'] == arm and report['cpu_affinity'] == [2]
                    and report['source_sha256'] == norm(inputs[CORE]['sha256']), 'phase/source identity differs')
            helper.no_score(report)
            require(report['standalone_decoder'] is False and report['exact_raw_inverse'] is True
                    and report['raw_sha256'] == rawref['sha256'] and report['modeled_sha256'] == modeledref['sha256']
                    and report['raw_bytes'] == 250000 and report['modeled_bytes'] == 151210, 'phase inverse/coordinates differ')
            require(report['external_parent_q16_sha256'] == qref['sha256'] and report['external_parent_q16_bytes'] == qref['bytes']
                    and report['dictionary_sha256'] == norm(inputs[pop['dictionary_path']]['sha256']), 'decoder dependency differs')
            policy = 'causal-field-original-first-wrt-v1' if arm in 'PO' else 'causal-field-immediately-preceding-wrt250k-v1'
            require(report['adapter_policy_id'] == policy and report['adapter_constructor_arm'] == ('T' if arm == 'O' else arm)
                    and report['decoder_arm_option_bytes'] == 1, 'selector identity or option differs')
            require(0 <= report['changed_probability_bits'] <= report['donor_present_bits'] <= 1209680
                    and report['prefix_bytes'] == 46 and report['archive_bytes'] == 46 + report['payload_bytes'], 'activity/framing differs')
            require(0 <= report['cpu_seconds'] <= 60 and report['peak_rss_kib'] * 1024 <= 536870912, 'phase resource bound differs')
            syncref = fingerprint(R('work/' + phase + '.sync'))
            require(syncref['bytes'] == 151210 * 32 and syncref['sha256'] == report['synchronization_file_sha256']
                    and report['synchronization_rows'] == 151210, 'full synchronization evidence differs')
            with (ROOT / syncref['path']).open('rb') as stream:
                stream.seek(-32, 2)
                require(stream.read(32).hex() == report['synchronization_digest'], 'terminal chain differs')
            reports.append(report)
            phase_rows.append({'phase': phase, 'execution': fingerprint(R(phase + '.execution.json')),
                'report': fingerprint(R(phase + '.stdout')), 'cpu_seconds': report['cpu_seconds'],
                'wall_seconds': command['elapsed_seconds'], 'peak_rss_kib': report['peak_rss_kib']})
        require(all({key: report[key] for key in MEANINGFUL} == {key: reports[0][key] for key in MEANINGFUL} for report in reports),
                'complete within-arm state/probability projections differ')
        equal([R('work/' + arm + '-' + op + '.sync') for op in PHASES])
        equal([R('work/raw.bin'), R('work/' + arm + '-decode.bin'), R(arm + '/restored.bin')])
        archive_paths = [R(arm + '/archive.bin'), R(arm + '/repeat.bin'), R('work/' + arm + '-encode.bin'), R('work/' + arm + '-repeat.bin')]
        if arm in 'PK':
            archive_paths.append(ROOT / pop['parent_archive_path'])
        equal(archive_paths)
        archive = fingerprint(archive_paths[0])
        require(archive['bytes'] == reports[0]['archive_bytes'] and archive['sha256'] == reports[0]['archive_sha256'], 'archive report differs')
        require(comparison['reports'][arm] == reports[0], 'comparison report replaced')
        driver = load(R(arm + '/result.json'))
        require(driver['program_id'] == ID and driver['roundtrip_ok'] is True and driver['determinism']['single_host_byte_equal'] is True
                and driver['data_sha256'] == rawref['sha256'] and driver['compressed_sha256'] == archive['sha256'], 'driver content differs')
        require(driver['program_size'] == 72134 and driver['hutter_score'] == 72134 + archive['bytes']
                and driver['prize_claimable'] is False and driver['score_accounting_complete'] is False, 'driver local score scope differs')
        require(driver['run_tags'] == ['arm:' + arm, 'external-parent-q16-replay'] and driver['arm'] is None
                and driver['run_scope_label'] == 'opening250k-' + arm and driver['program_stats']['phase'] == reports[0], 'driver arm metadata differs')
        summary = load(R(arm + '-synchronization.json'))
        require(summary['records'] == 151210 and summary['every_modeled_byte_identical'] is True
                and summary['report_projection_identical'] is True, 'synchronization summary differs')
        arms[arm] = {'archive': archive, 'selected_values': reports[0]['adapter']['selected_values'],
                     'changed_probability_bits': reports[0]['changed_probability_bits'], 'donor_present_bits': reports[0]['donor_present_bits'],
                     'adapter': reports[0]['adapter'], 'probability_digest': reports[0]['probability_digest']}
        require(arms[arm]['donor_present_bits'] % 8 == 0, 'donor residency is not byte-aligned')
        arms[arm].update(donor_present_modeled_bytes=arms[arm]['donor_present_bits'] // 8,
            changed_probability_modeled_bytes=None, eligible_transition_count=None,
            diagnostic_archive_source_dependency_and_option_bytes=archive['bytes'] + 72134 + 2831356 + 1,
            measurement_note='Donor presence is constant within each modeled byte in the frozen loop. Distinct bytes with changed probability and an eligible-transition denominator were not collected.')
    original = load(pop['original_result_path'])['program_stats']['phase']
    equal([R('O/archive.bin'), ROOT / pop['original_archive_path']])
    equal([R('work/O-encode.sync'), ROOT / pop['original_sync_path']])
    for key in helper.MEANINGFUL:
        if key not in ('arm', 'source_sha256'):
            require(comparison['reports']['O'][key] == original[key], 'O original T mismatch: ' + key)
    require(arms['P']['archive']['sha256'] == arms['K']['archive']['sha256']
            and arms['P']['probability_digest'] == arms['K']['probability_digest']
            and arms['P']['changed_probability_bits'] == arms['K']['changed_probability_bits'] == 0, 'P/K identity failed')
    sizes = {arm: row['archive']['bytes'] for arm, row in arms.items()}
    active = {arm: arms[arm]['selected_values'] > 0 and arms[arm]['changed_probability_bits'] > 0 for arm in 'TRS'}
    saved = sizes['P'] - sizes['T']
    beats = all(sizes['T'] < sizes[arm] for arm in 'ORS')
    classification = ('inconclusive_inactive_opportunities_or_controls' if not all(active.values()) else
                      'failed_causal_controls' if not beats else 'weak_compression' if saved <= 0 else 'conditional_archive_gain')
    require(stage['failure_class'] == comparison['failure_class'] == classification and comparison['archive_saved_bytes'] == saved
            and comparison['required_controls_active'] == active and comparison['treatment_beats_controls'] == beats, 'scientific conclusion differs')
    require(comparison['local_source_paying'] == (saved > 72135) and comparison['external_decode_dependency_bytes'] == 2831356
            and comparison['decoder_arm_option_bytes_per_archive'] == 1 and comparison['larger_gate_authorized'] is False, 'accounting authority differs')
    if R('decision.json').exists():
        output['later_canonical_decision'] = fingerprint(R('decision.json'))
        output['canonical_validations']['decision'] = contracts.validate_artifact(R('decision.json'))
    output.update(status='passed_closed_evidence_audit', job=fingerprint(JOB), guard=fingerprint(resources['guard_path']),
        contract=fingerprint(job['experiment']['path']), stage=fingerprint(R('stage-decision.json')),
        comparison=fingerprint(R('comparison.json')), input_count=209, declared_source_closure_files=len(declared_closure),
        indexed_result_files=len(index), candidate_tree_and_blobs_match=True, independent_phases=phase_rows,
        arms=arms, archive_bytes=sizes, controls_active=active, classification=classification,
        scientific_rejection_pass=all(active.values()) and not (saved > 0 and beats),
        source_bytes=72134, local_source_file_count=7, external_Q16_bytes=2419360, external_dictionary_bytes=411996,
        external_decode_dependency_bytes=2831356, decoder_arm_option_bytes=1, archive_saved_bytes=saved,
        matched_diagnostic_package_delta_bytes={arm: sizes[arm] - sizes['P'] for arm in ARMS},
        historical_local_source_increment_bytes=72134 - 66054,
        original_O_exact_old_T=True, P_K_identity=True, every_byte_state_chains_equal=True,
        resources={'guard_samples': guard['sample_count'], 'elapsed_seconds': guard['elapsed_s'], 'peaks': guard['peaks'],
            'guards': guard['guards'], 'cleanup_complete': True, 'outer_stop_seconds': 900, 'guard_wall_seconds': None,
            'outer_controller_binding': outer, 'timing_authority': 'shared-host diagnostic'},
        limitations=['No codec, parser or probability replay performed by this audit; exact closed bytes and digest chains compared.',
            'The preceding projection is authenticated and reused; no truth trace is read or reprocessed.',
            'Source file count is seven; the frozen measurement description saying six is stale wording. Numeric accounting is unchanged.',
            'External Q16 replay does not independently execute the native parent predictor. Runtime, license and complete-package closure remain unresolved.',
            'This rejects only the frozen tested realization when the active-control predicates fail, not the information source generally.'],
        complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0, launch_authorized=False)


def main():
    require(not (OUT / 'audit.json').exists(), 'audit output already exists')
    resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(120)
    started, cpu = time.monotonic(), time.process_time()
    output = {'schema': 'gamma.enwiki9.independent-preceding-terminal-audit.v1', 'status': 'failed',
              'closed_identity_before_payload_reads': False, 'new_codec_runs': 0, 'source_edits': False,
              'process_monitoring_or_control': False, 'basis': {'path': BASIS, 'sha256': BASIS_SHA}}
    try:
        audit(output)
    except Exception as error:
        output.update(error=type(error).__name__ + ': ' + str(error), traceback=traceback.format_exc())
    output.update(read_bindings=list(helper.bindings.values()), read_bytes=helper.read_bytes,
        audit_wall_seconds=time.monotonic() - started, audit_cpu_seconds=time.process_time() - cpu,
        audit_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        script_sha256=sha(Path(__file__).read_bytes()), observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    with (OUT / 'audit.json').open('x') as stream:
        json.dump(output, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps({key: output.get(key) for key in ('status', 'classification', 'archive_bytes', 'error')}))
    return 0 if output['status'] == 'passed_closed_evidence_audit' else 1


if __name__ == '__main__':
    raise SystemExit(main())
