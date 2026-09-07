#!/usr/bin/env python3
"""Read closed literal-first artifacts; never import or execute a codec."""
import copy
import hashlib
import json
from pathlib import Path
import resource
import struct

ROOT = Path(__file__).resolve().parents[3]
RUN = Path('results/dualstream_literal_first250k_q0_v1')
NORM = Path('operations/provenance/dualstream_literal_first_terminal_20260907')
JOB = Path('operations/adaptive/completed/909_20260907T183536Z_a3505ed881.json')
EXPERIMENT = Path('operations/adaptive/experiments/dualstream_literal_first250k_q0_v1.json')
PLAN = Path('operations/provenance/dualstream_literal_first250k_q0_v1_plan.json')
checked = {}


def read(path):
    return (ROOT / path).read_bytes()


def obj(path):
    return json.loads(read(path))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ref(path):
    data = read(path)
    return {'path': str(path), 'bytes': len(data), 'sha256': sha(data)}


def check_ref(item):
    got = ref(item['path'])
    assert got['sha256'] == item['sha256'].removeprefix('sha256:'), item['path']
    if 'bytes' in item:
        assert got['bytes'] == item['bytes'], item['path']
    checked[item['path']] = got


def refs_in(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            check_ref(value)
        for child in value.values():
            refs_in(child)
    elif isinstance(value, list):
        for child in value:
            refs_in(child)


def common(report):
    result = copy.deepcopy(report)
    for key in ('mode', 'search_spec', 'repeat_scope', 'raw_encoder_repeat_proved'):
        result.pop(key, None)
    for frame in result['frames']:
        frame.pop('search', None)
    return result


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 ** 2, 512 * 1024 ** 2))
    job = obj(JOB)
    guard_path = job['execution_resources']['guard_path']
    guard = obj(guard_path)
    assert job['state'] == 'completed' and job['returncode'] == 0
    assert job['execution_resources']['cleanup_complete'] is True
    assert guard['status'] == 'complete' and guard['returncode'] == 0
    assert not any(guard['guards'].values())
    assert guard['latest_sample']['processes'] == []
    assert guard['cgroup']['inode'] == job['execution_resources']['cgroup_inode']
    contract, plan = obj(EXPERIMENT), obj(PLAN)
    refs_in(job)
    for item in contract['inputs'] + plan['runtime_files']:
        check_ref(item)
    assert len(contract['inputs']) == 27 and len(plan['runtime_files']) == 21
    assert plan['resources'] == {k: job['resource_budget'][k] for k in plan['resources']}
    assert plan['resources']['cpus'] == [2]
    assert (plan['phase_cpu_seconds'], plan['phase_wall_seconds'], plan['phase_address_bytes']) == (60, 90, 536870912)
    assert guard['peaks']['cgroup_memory_peak_bytes'] <= plan['resources']['memory_bytes']
    assert guard['peaks']['max_sampled_scratch_allocated_bytes'] <= plan['resources']['scratch_bytes']
    assert guard['peaks']['max_sampled_allowed_cpu_count'] == 1
    assert guard['elapsed_s'] <= plan['resources']['wall_seconds']
    raw = read(plan['population']['path'])
    check_ref(plan['population'])
    check_ref(plan['plain_archive'])
    assert len(raw) == 250000
    rows, executions, stdouts, archives = {}, [], {}, {}
    for arm in ('P', 'K', 'D'):
        row = rows[arm] = obj(RUN / (arm + '.result.json'))
        refs_in(row)
        archive = archives[arm] = read(RUN / (arm + '.d2g'))
        assert archive == read(RUN / (arm + '.repeat.d2g'))
        assert raw == read(RUN / (arm + '.raw'))
        assert row['archive_bytes'] == len(archive)
        assert row['exact_inverse'] and row['deterministic_repeat'] and row['raw_encoder_repeat_proved']
        stdouts[arm] = {}
        for phase in ('encode', 'decode', 'repeat'):
            name = arm + '-' + phase
            ex = obj(RUN / (name + '.execution.json'))
            executions.append(ex)
            assert ex['returncode'] == 0 and ex['error'] is None and not ex['timeout']
            assert ex['elapsed_seconds'] < plan['phase_wall_seconds']
            assert ex['system_cpu_seconds'] + ex['user_cpu_seconds'] < plan['phase_cpu_seconds']
            source = 'dualstream_literal_first_v1.py'
            if arm == 'P':
                source = 'dualstream_grammar_decode_dispatch_v1.py' if phase == 'decode' else 'dualstream_grammar_argtokens_v2.py'
            source_input = RUN / (arm + '.d2g') if phase == 'decode' else RUN / (arm + '.raw') if phase == 'repeat' else Path(plan['population']['path'])
            target = RUN / (arm + ('.raw' if phase == 'decode' else '.repeat.d2g' if phase == 'repeat' else '.d2g'))
            expected = ['/usr/bin/python3', str(ROOT / 'tools' / source), 'decode' if phase == 'decode' else 'encode', str(ROOT / source_input), str(ROOT / target)]
            if phase != 'decode':
                expected += ['--mode', 'plain' if arm == 'P' else arm, '--frame-size', '65536']
            assert ex['argv'] == expected, name
            assert str(Path(expected[0]).resolve()) in {r['path'] for r in plan['runtime_files']}
            assert read(RUN / (name + '.stderr')) == b''
            out = stdouts[arm][phase] = obj(RUN / (name + '.stdout'))
            assert out['peak_process_rss_kib'] * 1024 < plan['phase_address_bytes']
            assert out['cpu_seconds'] < plan['phase_cpu_seconds']
            markers = [x['event'] for x in guard['phase_markers'] if x['phase'] == name]
            assert markers == ['start', 'end'], name
        assert stdouts[arm]['encode']['result'] == stdouts[arm]['repeat']['result']
        if arm != 'P':
            assert common(stdouts[arm]['encode']['result']) == stdouts[arm]['decode']['result']
    assert archives['P'] == archives['K'] == archives['D'] == read(plan['plain_archive']['path'])
    # Independently parse stored framing and compare raw-frame hashes. No inflate.
    data = archives['P']
    header, frame_header = struct.Struct('<8sIIQ'), struct.Struct('<IB5I32s')
    magic, frame_size, count, total = header.unpack_from(data)
    assert (magic, frame_size, count, total) == (b'D2GRAM02', 65536, 4, len(raw))
    cursor, raw_cursor, payload, frames = header.size, 0, 0, []
    for index in range(count):
        n, mode, *tail = frame_header.unpack_from(data, cursor)
        lengths, digest = tail[:5], tail[5]
        assert mode == 0 and lengths[:3] == [0, 0, 0] and lengths[4] == 0
        assert digest == hashlib.sha256(raw[raw_cursor:raw_cursor + n]).digest()
        cost = sum(lengths) + frame_header.size
        cursor += cost
        raw_cursor += n
        payload += sum(lengths)
        for arm in rows:
            f = rows[arm]['frames'][index]
            assert f['raw_bytes'] == n and f['raw_sha256'] == digest.hex()
            assert f['complete_frame_bytes'] == cost
            assert f['costs'] == {'deflate_payload': sum(lengths), 'framing': frame_header.size}
            assert f['selected_rules'] == f['calls'] == f['repeated_argument_references'] == 0
            if arm != 'P':
                assert f['output_sha256'] == f['representation_sha256'] == digest.hex()
                assert f['program_sha256'] == f['boundary_sha256'] == sha(b'')
                assert f['execution_steps'] == 1
        k, d = rows['K']['frames'][index]['search'], rows['D']['frames'][index]['search']
        for key in ('proposal_sha256', 'proposals', 'total_proposals', 'proposals_truncated', 'spans', 'total_spans', 'spans_truncated', 'evaluations'):
            assert k[key] == d[key], (index, key)
        assert k['discovery_from_raw'] and d['discovery_from_raw']
        assert k['admission_enabled'] is False and d['admission_enabled'] is True
        assert d['admitted'] == 0
        assert d['spans'] == min(d['total_spans'], plan['search_spec']['max_spans'])
        assert d['spans_truncated'] == d['total_spans'] - d['spans']
        assert d['proposals'] == min(d['total_proposals'], plan['search_spec']['max_proposals'])
        assert d['proposals_truncated'] == d['total_proposals'] - d['proposals']
        evaluations = d['evaluations']
        assert {e['proposal'] for e in evaluations} == set(range(d['proposals']))
        assert len(evaluations) == d['proposals']
        for e in evaluations:
            assert e['round'] == 0 and e['accepted'] is False
            assert e['before'] == cost and e['delta'] == e['before'] - e['candidate'] < 0
            assert len(bytes.fromhex(e['candidate_sha256'])) == 32
        frames.append({'frame': index, 'raw_bytes': n, 'archive_bytes': cost, **{k: d[k] for k in ('spans', 'total_spans', 'spans_truncated', 'proposals', 'total_proposals', 'proposals_truncated')}, 'evaluations': len(evaluations), 'admitted': 0, 'best_delta_bytes': max(e['delta'] for e in evaluations), 'worst_delta_bytes': min(e['delta'] for e in evaluations)})
    assert cursor == len(data) and raw_cursor == len(raw)
    accounting = {'deflate_payload': payload, 'framing': header.size + count * frame_header.size}
    assert sum(accounting.values()) == len(data)
    for row in rows.values():
        assert row['accounting'] == accounting
    # Only now consult reported interpretations and indexes.
    stage, costs, decision = (obj(RUN / p) for p in ('stage-decision.json', 'costs-table.json', 'decision.json'))
    assert stage['arms'] == list(rows.values()) and stage['commands'] == executions
    assert stage['costs'] == costs
    index = obj(RUN / 'artifacts.json')
    assert index['complete'] and len(index['files']) == 40 and len(decision['artifacts']) == 42
    refs_in(index)
    refs_in(decision)
    outputs = set(contract['outputs'])
    actual = {str(p.relative_to(ROOT)) for p in (ROOT / RUN).iterdir() if p.is_file()}
    assert len(outputs) == 43 and actual == outputs
    assert {r['path'] for r in decision['artifacts']} == outputs - {str(RUN / 'decision.json')}
    assert {r['path'] for r in index['files']} == outputs - {str(RUN / p) for p in ('decision.json', 'stage-decision.json', 'artifacts.json')}
    assert costs['archive_bytes'] == {a: len(v) for a, v in archives.items()}
    for key in ('p_minus_d_bytes', 'p_minus_k_bytes', 'k_minus_d_bytes', 'objective_credit_bytes'):
        assert costs[key] == 0
    assert not costs['strict_d_improvement'] and not costs['confirmation_eligible']
    normalized = obj(NORM / 'index.json')
    refs_in(normalized)
    for entry in normalized['arms']:
        arm = entry['arm']
        n = obj(entry['result']['path'])
        refs_in(n)
        assert n['artifacts'] == rows[arm]['artifacts'] == entry['artifacts']
        assert n['data_size'] == len(raw) and n['data_sha256'] == sha(raw)
        assert n['data_md5'] == hashlib.md5(raw).hexdigest()
        assert n['compressed_size'] == len(data) and n['compressed_sha256'] == sha(data)
        assert n['compressed_md5'] == hashlib.md5(data).hexdigest()
        assert n['bits_per_byte'] == 8 * len(data) / len(raw) and n['accounting'] == accounting
        assert n['roundtrip_ok'] and n['raw_encoder_repeat_proved']
        assert n['deterministic_repeat']['single_host_byte_equal']
        assert n['deterministic_repeat']['selection_repeated'] == (arm != 'P')
        assert n['candidate_revision'] == decision['candidateRevision']
        assert n['run_time_s'] == sum(x['elapsed_seconds'] for x in executions if x['phase'].startswith(arm + '-'))
        for field, phase in [('compress_time_s', 'encode'), ('decompress_time_s', 'decode'), ('repeat_time_s', 'repeat')]:
            assert n[field] == stdouts[arm][phase]['elapsed_seconds']
        assert n['encoding_cpu_seconds'] == stdouts[arm]['encode']['cpu_seconds']
        assert n['decoding_cpu_seconds'] == stdouts[arm]['decode']['cpu_seconds']
        assert n['memory_kib']['peak'] == max(x['peak_process_rss_kib'] for x in stdouts[arm].values())
        for field in ('complete_package_bytes', 'full_corpus_score_bytes', 'program_size', 'hutter_score'):
            assert n[field] is None
        for field in ('prize_claimable', 'score_accounting_complete', 'resource_evidence_complete'):
            assert n[field] is False
    root_terminal = obj('operations/provenance/dualstream_literal_first_terminal_20260907.json')
    assert root_terminal['measurements'] == decision['measurements']
    # Exact invoked source/import closure, not a qualified distributable package.
    legacy = 'tools/dualstream_grammar_v1.py'
    argtokens = 'tools/dualstream_grammar_argtokens_v2.py'
    dispatch = 'tools/dualstream_grammar_decode_dispatch_v1.py'
    literal = 'tools/dualstream_literal_first_v1.py'
    inventories = {}
    for label, paths in [('P_encode', [legacy, argtokens]), ('P_encode_decode', [legacy, argtokens, dispatch]), ('K_D_encode_decode', [legacy, literal]), ('all_codec_sources', [legacy, argtokens, dispatch, literal])]:
        files = [ref(p) for p in paths]
        inventories[label] = {'files': files, 'bytes': sum(f['bytes'] for f in files)}
    assert costs['known_source_bytes'] == inventories['all_codec_sources']['bytes'] == 52038
    refs_in(costs)
    report = {
        'schema': 'gamma.enwiki9.literal-first-independent-review.v1',
        'status': 'passed', 'candidate_id': contract['experimentId'],
        'method': 'Closed artifact/hash/command/report/framing audit; no codec imports, codec reruns or fresh corpus executions.',
        'bindings': {'job': ref(JOB), 'contract': ref(EXPERIMENT), 'plan': ref(PLAN), 'guard': ref(guard_path), 'normalized_index': ref(NORM / 'index.json'), 'root_terminal': ref('operations/provenance/dualstream_literal_first_terminal_20260907.json')},
        'checked_unique_hash_bindings': len(checked), 'frozen_inputs': len(contract['inputs']), 'runtime_files': len(plan['runtime_files']),
        'closed_phases': len(executions), 'result_files': len(actual), 'raw_bytes': len(raw),
        'archive_bytes': {a: len(b) for a, b in archives.items()}, 'archive_sha256': sha(data), 'raw_sha256': sha(raw),
        'inverse_byte_equality': True, 'renewed_raw_encode_repeat': True, 'p_k_d_byte_identity': True,
        'k_d_first_round_proposals_and_costs_equal': True, 'decoder_common_projection_equal': True,
        'accounting': accounting, 'frames': frames, 'proposal_evaluations': sum(f['evaluations'] for f in frames),
        'source_inventories': inventories,
        'D_minus_P_command_source_bytes': inventories['K_D_encode_decode']['bytes'] - inventories['P_encode_decode']['bytes'],
        'diagnostic_guard': {'elapsed_seconds': guard['elapsed_s'], 'cgroup_peak_bytes': guard['peaks']['cgroup_memory_peak_bytes'], 'cpus': [2], 'timing_authority': 'diagnostic'},
        'outcome': 'No selected template; exact plain fallback. Fixed candidate does not satisfy strict archive improvement; no confirmation or promotion authority.',
        'limitations': [
            'One opening development population and one capped search; no theorem rejecting grammar compression.',
            '549 spans excluded by frame-three cap; retained spans may overlap and do not measure unique byte coverage.',
            'No selected rules or shared argument references on this corpus gate; nontrivial interpreter paths have only synthetic evidence.',
            'Candidate cost rows and hashes were checked for arithmetic/closure agreement; rejected candidate archives are not retained and were not reconstructed by this audit.',
            'Representation subcategory sizes are pre-Deflate quantities, not additive compressed category credits.',
            'Decoder recompresses with Deflate for canonical checking; no novelty, smallest-decoder or cheap-decompression claim.',
            'Source inventories are uncompressed local files for exact commands; runtime distribution, license closure, invocation accounting and complete package remain unknown.',
            'Bounded shared-host guard is diagnostic; no calibrated qualification or full-corpus score.'
        ],
        'complete_package_bytes': None, 'full_corpus_score_bytes': None, 'objective_credit_bytes': 0,
        'reviewer_source': ref(Path(__file__).relative_to(ROOT))
    }
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
