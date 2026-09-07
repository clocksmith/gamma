"""Independent closed-artifact audit; imports and executes no codec or gate."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import stat
import struct
import time

ROOT = Path(__file__).resolve().parents[3]
DEST = Path(__file__).resolve().parent
CID = 'dualstream_event250k_q0_v1'
JID = '20260907T174128Z_3e40a47003'
RESULT = 'results/' + CID + '/'
TERMINAL = 'operations/provenance/dualstream_event_terminal_20260907'
observed = {}


def read(name):
    path = ROOT / name
    assert path.is_file() and not path.is_symlink(), name
    size = path.stat().st_size
    assert size <= 32 << 20, name
    data = path.read_bytes()
    assert len(data) == size
    ref = {'bytes': size, 'sha256': hashlib.sha256(data).hexdigest()}
    assert str(name) not in observed or observed[str(name)] == ref, name
    observed[str(name)] = ref
    return data


def load(name):
    return json.loads(read(name))


def check(row):
    data = read(row['path'])
    assert hashlib.sha256(data).hexdigest() == row['sha256'].removeprefix('sha256:'), row['path']
    assert 'bytes' not in row or len(data) == row['bytes'], row['path']
    return data


def write(name, value):
    with (DEST / name).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2)
        stream.write('\n')


def main():
    os.sched_setaffinity(0, {3})
    resource.setrlimit(resource.RLIMIT_AS, (512 << 20, 512 << 20))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 << 20, 32 << 20))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(180)
    started, cpu = time.monotonic(), time.process_time()
    terminal = load(TERMINAL + '.json')
    index = load(TERMINAL + '/index.json')
    read(TERMINAL + '/record.py')
    for key in ('job', 'guard', 'experiment', 'stage'):
        check(terminal[key])
    job, guard, contract, stage = [load(terminal[key]['path']) for key in ('job', 'guard', 'experiment', 'stage')]
    assert job['job_id'] == JID and job['candidate_id'] == CID
    assert job['state'] == 'completed' and job['returncode'] == 0
    assert job['execution_resources']['cleanup_complete'] is True
    assert guard['status'] == 'complete' and guard['returncode'] == 0
    assert not any(guard['guards'].values()) and not guard['latest_sample']['processes']
    assert contract['experimentId'] == CID and contract['status'] == 'frozen'
    assert contract['registrationTiming'] == 'prospective' and contract['objectiveCreditBytes'] == 0
    assert job['experiment'] == stage['experiment'] == terminal['experiment']
    assert len({r['path'] for r in contract['inputs']}) == len(contract['inputs']) == 32
    for row in contract['inputs']:
        check(row)
    plan = load(next(r['path'] for r in contract['inputs'] if r['id'] == 'grammar-gate-plan'))
    for row in plan['runtime_files']:
        check(row)
    source_entries = {r['id']: r for r in contract['inputs']}
    assert len(contract['pythonSourceClosureEntries']) == 8
    assert all(source_entries[key]['path'].endswith('.py') for key in contract['pythonSourceClosureEntries'])
    check(job['execution_guard'])
    revision = json.loads(check(job['candidate_revision']))
    assert revision['candidateId'] == CID and revision['candidateTreeSha256'] == job['candidate_tree_sha256']
    for row in revision['files']:
        check({'path': row['blobPath'], 'sha256': row['sha256'], 'bytes': row['bytes']})
    assert guard['cgroup']['path'] == job['execution_resources']['cgroup_path']
    assert guard['cgroup']['inode'] == job['execution_resources']['cgroup_inode']
    assert guard['cgroup']['joined_before_exec'] and guard['cgroup']['memory_peak_reset']
    assert guard['cgroup']['memory_max_bytes'] == plan['resources']['memory_bytes']
    assert all(job['resource_budget'][key] == value for key, value in plan['resources'].items())
    assert guard['temporary_disk_limit_bytes'] == plan['resources']['scratch_bytes']
    assert guard['max_logical_cpus'] == 1 and guard['peaks']['max_sampled_allowed_cpu_count'] == 1
    assert guard['elapsed_s'] < plan['resources']['wall_seconds']
    assert guard['wall_time_limit_seconds'] is None  # Canonical diagnostic; outer lab owns the total stop.
    assert hashlib.sha256(b'\0'.join(os.fsencode(x) for x in guard['command'])).hexdigest() == guard['command_sha256']
    assert guard['command'][:3] == ['/usr/bin/taskset', '--cpu-list', '2']
    assert guard['command'][-4:] == ['/usr/bin/python3', str(ROOT / job['tool']), '--candidate', CID]
    assert guard['phase_marker_path'] == str(ROOT / ('run_logs/adaptive/' + JID + '.resources/phases.jsonl'))
    assert guard['sample_count'] == 153 and guard['peaks']['cgroup_memory_peak_bytes'] == 36200448
    assert stage['status'] == 'passed' and stage['native_phases'] == len(stage['commands']) == 15
    assert all(stage[key] for key in ('correctness_pass', 'accounting_pass', 'paired_program_identity_pass', 'frozen_inputs_reverified'))
    manifest = load(RESULT + 'artifacts.json')
    assert manifest['complete'] is True and len(manifest['files']) == 66
    for row in manifest['files']:
        check(row)
    assert {r['path'] for r in manifest['files']} | {RESULT + name for name in ('artifacts.json', 'stage-decision.json', 'decision.json')} == set(contract['outputs'])
    raw = check(plan['population'])
    assert len(raw) == 250000
    reports, sizes, frame_totals = {}, {}, {}
    for arm, indexed, row in zip(plan['arms'], index['arms'], stage['arms'], strict=True):
        key = arm['id']
        assert row == load(RESULT + key + '.result.json') and row['arm'] == arm
        assert indexed['arm'] == key and indexed['artifacts'] == row['artifacts']
        normalized = json.loads(check(indexed['result']))
        artifacts = {name: check(ref) for name, ref in row['artifacts'].items()}
        assert artifacts['restored'] == raw and artifacts['archive'] == artifacts['repeat']
        sizes[key] = len(artifacts['archive'])
        assert sizes[key] == row['archive_bytes'] == sum(row['accounting'].values()) == normalized['compressed_size']
        assert normalized['compressed_sha256'] == hashlib.sha256(artifacts['archive']).hexdigest()
        assert normalized['data_sha256'] == hashlib.sha256(raw).hexdigest() and normalized['artifacts'] == row['artifacts']
        assert normalized['prize_claimable'] is False and normalized['hutter_score'] is None
        assert normalized['raw_encoder_repeat_proved'] is (key == 'R') and normalized['complete_package_bytes'] is None
        wrappers = [load(RESULT + key + '-' + phase + '.stdout') for phase in ('encode', 'decode', 'repeat')]
        reports[key] = wrappers[0]['result']
        assert reports[key] == wrappers[2]['result']
        for phase, wrapper in zip(('encode', 'decode', 'repeat'), wrappers, strict=True):
            execution = load(RESULT + key + '-' + phase + '.execution.json')
            assert execution in stage['commands'] and execution['phase'] == key + '-' + phase
            assert execution['returncode'] == 0 and execution['error'] is None and execution['timeout'] is False
            assert execution['elapsed_seconds'] < plan['phase_wall_seconds']
            assert execution['user_cpu_seconds'] + execution['system_cpu_seconds'] < plan['phase_cpu_seconds']
            assert read(RESULT + key + '-' + phase + '.stderr') == b''
            assert wrapper['complete_package_bytes'] is None and wrapper['full_corpus_score_bytes'] is None
            assert wrapper['peak_process_rss_kib'] * 1024 < plan['phase_address_bytes']
            assert execution['argv'][2] == ('decode' if phase == 'decode' else 'encode')
            assert execution['argv'][4] == str(ROOT / row['artifacts'][{'encode':'archive','decode':'restored','repeat':'repeat'}[phase]]['path'])
        assert reports[key]['frames'] == row['frames']
        if key in ('P', 'B'):
            assert artifacts['archive'] == check(plan['selected_archives'][arm['selection']])
            assert wrappers[1]['result'] == {'raw_bytes': 250000, 'frontend': 'D2GRAM02' if key == 'P' else 'D2GRAM01'}
        else:
            assert reports[key] == wrappers[1]['result']
            archive = artifacts['archive']
            magic, mode, frame_size, count, total = struct.unpack_from('<8sBIIQ', archive)
            assert (magic, mode, frame_size, count, total) == (b'D2EVENT1', {'R':0,'G':1,'X':2}[key],65536,4,250000)
            cursor = struct.calcsize('<8sBIIQ')
            for frame in row['frames']:
                size, kind, payload_size, raw_sha, graph_sha = struct.unpack_from('<IBI32s32s', archive, cursor)
                cursor += 73
                payload = archive[cursor:cursor + payload_size]
                cursor += payload_size
                sync = frame['synchronization']
                assert (size, kind, raw_sha.hex(), graph_sha.hex()) == (frame['raw_bytes'],frame['mode'],frame['raw_sha256'],frame['model_sha256'])
                assert payload[-32:].hex() == sync['state_digest'] and len(payload) == sync['payload_bytes']
                assert sync['canonical_reencode_pass'] and sync['output_sha256'] == frame['raw_sha256']
                assert sum(sync['actual_bytes_by_category'].values()) == payload_size
                assert all(frame['costs'][k] == sync['actual_bytes_by_category'].get(k,0) + (73 if k=='framing' else 0) for k in frame['costs'])
            assert cursor == len(archive)
            assert all(row['accounting'][k] == sum(f['costs'][k] for f in row['frames']) + (25 if k=='framing' else 0) for k in row['accounting'])
        for i, frame in enumerate(row['frames']):
            part = raw[i*65536:(i+1)*65536]
            assert frame['raw_bytes'] == len(part) and frame['raw_sha256'] == hashlib.sha256(part).hexdigest()
            if key in ('B','G','X'):
                assert {k:frame[k] for k in plan['expected_frames'][i]} == plan['expected_frames'][i]
        frame_totals[key] = [f['repeated_argument_references'] for f in row['frames']]
    for g,x in zip(reports['G']['frames'],reports['X']['frames'],strict=True):
        assert all(g[k] == x[k] for k in ('model_sha256','interpreter_sha256','boundary_sha256','boundary_count','execution_steps','stored_nodes'))
        assert all(g['synchronization'][k] == x['synchronization'][k] for k in ('events','binary_events','emitted_bytes','output_sha256'))
    costs = load(RESULT + 'costs-table.json')
    assert costs == terminal['costs'] == stage['costs'] and costs['archive_bytes'] == sizes
    for row in costs['package_source']:
        check(row)
    assert sum(r['bytes'] for r in costs['package_source']) == costs['known_source_bytes'] == 80016
    deltas = {'context_saved_bytes':sizes['G']-sizes['X'], 'grammar_vs_raw_event_saved_bytes':sizes['R']-sizes['X'],
              'event_vs_plain_deflate_saved_bytes':sizes['P']-sizes['X'], 'event_vs_selected_deflate_saved_bytes':sizes['B']-sizes['X']}
    assert all(costs[k] == value == terminal['measurements'][k] for k,value in deltas.items())
    meets = all(sizes['X'] < sizes[k] for k in ('G','R','P'))
    assert not meets and costs['beats_G_R_P'] is meets and terminal['measurements']['beats_G_R_P'] is meets
    assert terminal['objective_credit_bytes'] == 0 and terminal['complete_package_bytes'] is None
    for row in index['evidence']:
        check(row)
    assert index['job'] == terminal['job'] and index['guard'] == terminal['guard']
    for name, ref in list(observed.items()):
        check({'path':name, **ref})
    write('summary.json', {'schema':'gamma.enwiki9.independent-terminal-audit.v1','result':'passed','candidate_id':CID,'job_id':JID,
        'contract_inputs_verified':32,'runtime_files_verified':len(plan['runtime_files']),'declared_source_entries_verified':8,
        'indexed_result_files_verified':66,'closed_phases':15,'archive_bytes':sizes,'saved_bytes':deltas,
        'repeated_argument_references_by_frame':frame_totals,'frozen_G_R_P_condition_pass':meets,
        'conclusion':'X fails its frozen G/R/P condition. Park this fixed grammar/model realization; no confirmation authorized by this result.',
        'exact_inverse_and_repeats':True,'P_B_retained_diagonals_identical':True,'B_G_X_graphs_identical':True,
        'R_G_X_full_encode_decode_repeat_reports_identical':True,'G_X_boundary_execution_hashes_and_event_counts_identical':True,
        'event_schedule_scope':'Identical fixed graph plus deterministic shared interpreter, equal boundary/execution hashes and event counts; no separate mode-independent categorical-event trace was retained.',
        'P_B_decoder_scope':'Legacy decoder reports only raw size/frontend; exact inversion and retained archive identity verified separately.',
        'resources':{'cpu':[2],'shared_host_diagnostic':True,'elapsed_seconds':guard['elapsed_s'],'samples':153,
                     'cgroup_peak_bytes':36200448,'sampled_tree_rss_kib':guard['peaks']['max_sampled_tree_rss_kib'],
                     'sampled_scratch_allocated_bytes':guard['peaks']['max_sampled_scratch_allocated_bytes'],
                     'guards':guard['guards'],'cleanup_complete':True,'outer_wall_stop_seconds':1200,'guard_wall_limit_seconds':None},
        'known_source_union_bytes':80016,'complete_package_bytes':None,'full_corpus_score_bytes':None,'objective_credit_bytes':0,
        'scope':'Read/hash/closed-report comparison only; no codec, scanner, corpus gate or scientific rerun executed.',
        'audit_execution':{'cpu':[3],'address_space_limit_bytes':512<<20,'cpu_limit_seconds':120,'wall_limit_seconds':180,
                           'file_limit_bytes':32<<20,'elapsed_seconds':time.monotonic()-started,'cpu_seconds':time.process_time()-cpu,
                           'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
        'verified_references':observed})
    print('PASS: 32 contract inputs, 21 runtime files, 66 result artifacts, 15 closed phases; X fails G/R/P.')


if __name__ == '__main__':
    main()
