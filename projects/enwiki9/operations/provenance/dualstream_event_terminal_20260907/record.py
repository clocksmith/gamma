#!/usr/bin/env python3
"""Print normalized records for this closed diagnostic; never execute a codec."""
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import research_contracts

CID = 'dualstream_event250k_q0_v1'
JID = '20260907T174128Z_3e40a47003'
DEST = 'operations/provenance/dualstream_event_terminal_20260907'
RESULT = 'results/' + CID + '/'


def load(path):
    return json.loads((ROOT / path).read_text())


def ref(path):
    return dict(path=path, sha256='sha256:' + hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def verify(row):
    assert ref(row['path'])['sha256'].removeprefix('sha256:') == row['sha256'].removeprefix('sha256:'), row['path']
    if 'bytes' in row:
        assert (ROOT / row['path']).stat().st_size == row['bytes'], row['path']


def main():
    contract_path = 'operations/adaptive/experiments/' + CID + '.json'
    contract = load(contract_path)
    research_contracts.validate_artifact(ROOT / contract_path, verify_files=True)
    job_path = 'operations/adaptive/completed/909_' + JID + '.json'
    guard_path = 'run_logs/adaptive/' + JID + '.resources/guard.json'
    job, guard = load(job_path), load(guard_path)
    stage = load(RESULT + 'stage-decision.json')
    assert job['state'] == 'completed' and job['returncode'] == 0
    assert job['execution_resources']['cleanup_complete'] and guard['status'] == 'complete'
    assert guard['returncode'] == 0 and not any(guard['guards'].values())
    assert not guard['latest_sample']['processes']
    assert all(stage[k] for k in ('correctness_pass', 'accounting_pass', 'paired_program_identity_pass', 'frozen_inputs_reverified'))
    assert stage['native_phases'] == len(stage['commands']) == 15
    assert all(p['returncode'] == 0 and not p['timeout'] and p['error'] is None for p in stage['commands'])
    for row in contract['inputs']:
        verify(row)
    for row in load(RESULT + 'artifacts.json')['files']:
        verify(row)
    revision = dict(candidateId=CID, candidateTreeSha256=job['candidate_tree_sha256'], receipt=job['candidate_revision'])
    outputs = {}
    index = dict(schema='gamma.enwiki9.terminal-result-index.v1', job=ref(job_path), guard=ref(guard_path), arms=[],
                 evidence=[ref(RESULT + 'stage-decision.json'), ref(RESULT + 'costs-table.json')])
    raw_path = 'operations/evidence/fixtures/dualstream_opening250k_v1.raw'
    raw = (ROOT / raw_path).read_bytes()
    for row in stage['arms']:
        arm = row['arm']['id']
        for artifact in row['artifacts'].values():
            verify(artifact)
        archive = (ROOT / row['artifacts']['archive']['path']).read_bytes()
        inverse = (ROOT / row['artifacts']['restored']['path']).read_bytes()
        repeat = (ROOT / row['artifacts']['repeat']['path']).read_bytes()
        assert inverse == raw and archive == repeat
        assert len(archive) == row['archive_bytes'] == sum(row['accounting'].values())
        encoded, decoded, repeated = [load(RESULT + arm + '-' + p + '.stdout') for p in ('encode', 'decode', 'repeat')]
        assert encoded['result'] == repeated['result']
        if row['arm']['backend'] == 'event':
            assert encoded['result'] == decoded['result']
        raw_repeat = arm == 'R'
        result = dict(schema='gamma.enwiki9.driver-result.v2', program_id=CID, program_name='Fixed grammar event ' + arm,
            arm=arm, candidate_revision=revision, objective=contract['objective'], timestamp=job['finished_at'],
            run_source=job_path, run_purpose='diagnostic', run_scope_label='opening250KB-event-' + arm,
            run_tags=['typed-event-coding', 'fixed-grammar', 'diagnostic', arm],
            data_path=raw_path, data_size=len(raw), data_sha256=hashlib.sha256(raw).hexdigest(), data_md5=hashlib.md5(raw).hexdigest(),
            compressed_size=len(archive), compressed_sha256=hashlib.sha256(archive).hexdigest(), compressed_md5=hashlib.md5(archive).hexdigest(),
            bits_per_byte=8 * len(archive) / len(raw), program_size=None, hutter_score=None,
            hutter_score_kind='diagnostic-fixed-grammar-event-coding', complete_package_bytes=None, full_corpus_score_bytes=None,
            prize_claimable=False, score_accounting_complete=False, resource_evidence_complete=False,
            qualification_status='not-certified', execution_mode='discovery', timing_authority='diagnostic', roundtrip_ok=True,
            determinism=dict(scope='raw-context-encoder' if raw_repeat else 'raw-discovery-determinism-unmeasured',
                             single_host_byte_equal=True if raw_repeat else None),
            deterministic_reserialization_repeat=not raw_repeat, raw_encoder_repeat_proved=raw_repeat, repeat_scope=row['repeat_scope'],
            compress_time_s=encoded['elapsed_seconds'] if raw_repeat else None, decompress_time_s=decoded['elapsed_seconds'],
            reserialization_validation_time_s=None if raw_repeat else encoded['elapsed_seconds'],
            encoding_cpu_seconds=encoded['cpu_seconds'], decoding_cpu_seconds=decoded['cpu_seconds'],
            repeat_time_s=repeated['elapsed_seconds'],
            run_time_s=sum(p['elapsed_seconds'] for p in stage['commands'] if p['phase'].startswith(arm + '-')),
            run_time_scope='R raw encoding; G/X fixed graph encoding; P/B retained diagonal; independent decode and repeat.',
            memory_kib=dict(peak=max(p['peak_process_rss_kib'] for p in (encoded, decoded, repeated))),
            host=dict(machine=platform.machine(), node=platform.node(), python=platform.python_version(), system=platform.system()),
            paired_program_identity_pass=True, accounting=row['accounting'], artifacts=row['artifacts'],
            missing_diagnostics=job['execution_resources']['missing_diagnostics'], closed_guard=ref(guard_path), closed_job=ref(job_path),
            source_arm_result=ref(RESULT + arm + '.result.json'),
            run_context='Typed events with fixed selected graph; X alone adds causal interpreter context. Package qualification unknown.',
            reserialization_repeat=dict(single_host_byte_equal=True, selection_repeated=False,
                first_run_sha256=hashlib.sha256(archive).hexdigest(), second_run_sha256=hashlib.sha256(repeat).hexdigest(),
                first_run_md5=hashlib.md5(archive).hexdigest(), second_run_md5=hashlib.md5(repeat).hexdigest(), first_divergence_byte=None))
        out = DEST + '/normalized/' + arm + '.json'
        outputs[out] = result
        data = (json.dumps(result, indent=2, sort_keys=True) + '\n').encode()
        index['arms'].append(dict(arm=arm, result=dict(path=out, sha256='sha256:' + hashlib.sha256(data).hexdigest()), artifacts=row['artifacts']))
    costs = stage['costs']
    measurements = dict(correctness_pass=True, frozen_inputs_reverified=True, continuous_guard_pass=True, artifact_closure_pass=True,
        accounting_pass=True, paired_program_identity_pass=True, promotion_authorized=False, scientific_rejection_applicable=False,
        native_phases=15, raw_bytes=len(raw), **{k:costs[k] for k in ('context_saved_bytes', 'grammar_vs_raw_event_saved_bytes',
        'event_vs_plain_deflate_saved_bytes', 'event_vs_selected_deflate_saved_bytes', 'beats_G_R_P')})
    artifacts = [dict(id='artifact-' + str(i), **ref(p)) for i, p in enumerate(contract['outputs']) if p != RESULT + 'decision.json']
    def predicates(key):
        return [dict(p, observed=measurements[p['measurement']], passed=measurements[p['measurement']] == p['threshold']) for p in contract[key]]
    outputs[RESULT + 'decision.json'] = dict(schema='gamma.enwiki9.adaptive-experiment-result.v1', objective=contract['objective'],
        experiment=ref(contract_path), candidateId=CID, candidateRevision=revision, evidenceClass='diagnostic', objectiveCreditBytes=0,
        measurements=measurements, promotionPredicates=predicates('promotionPredicates'), killPredicates=predicates('killPredicates'),
        promotionPass=False, killPass=False, decision='retry', artifacts=artifacts, generatedUtc=job['finished_at'])
    outputs[DEST + '/index.json'] = index
    sizes = costs['archive_bytes']
    outputs['operations/provenance/dualstream_event_terminal_20260907.json'] = dict(schema='gamma.enwiki9.event-terminal.v1',
        candidate_id=CID, job=ref(job_path), guard=ref(guard_path), experiment=ref(contract_path), stage=ref(RESULT + 'stage-decision.json'),
        measurements=measurements, costs=costs,
        gate_resources=dict(elapsed_seconds=guard['elapsed_s'], peaks=guard['peaks'], samples=guard['sample_count'], guards=guard['guards']),
        repeated_argument_references={r['arm']['id']:sum(f['repeated_argument_references'] for f in r['frames']) for r in stage['arms']},
        known_source_union_bytes=costs['known_source_bytes'],
        route='Eligible to propose fresh confirmation; no promotion' if costs['beats_G_R_P'] else 'Park this fixed grammar/model realization; no confirmation',
        context_result='X smaller than G' if sizes['X'] < sizes['G'] else 'X does not improve G',
        limits=['No full-corpus score or size projection.', 'No new grammar discovery or binding mutation.',
                'Source/runtime/license/options qualification unresolved.', 'Only R repeats raw encoder discovery-free input.',
                'Specific context-key hashing and this population only; no theorem against structural models.'],
        full_corpus_score_bytes=None, complete_package_bytes=None, objective_credit_bytes=0)
    print(json.dumps({path: json.dumps(value, indent=2, sort_keys=True) + '\n' for path, value in outputs.items()}))


if __name__ == '__main__':
    main()
