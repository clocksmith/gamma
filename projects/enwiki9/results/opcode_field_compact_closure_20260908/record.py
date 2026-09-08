#!/usr/bin/env python3
"""Materialize this job's closed receipts; never launches a codec or grants credit."""
import datetime
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import record_driver_result as recorder
import research_contracts
from dualstream_grammar_gate_v1 import write_json

CID = 'opcode_field_compact_v1'
JID = '20260908T154100Z_6b9653a04d'
JOB = 'operations/adaptive/completed/959_' + JID + '.json'
OUT = 'operations/provenance/opcode_field_compact_terminal_20260908'


def read(path):
    return json.loads((ROOT / path).read_text())


def ref(path):
    data = (ROOT / path).read_bytes()
    return dict(path=path, sha256='sha256:' + hashlib.sha256(data).hexdigest())


def check(reference):
    path = recorder.project_path(reference['path'])
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == reference['sha256'].removeprefix('sha256:')
    if 'bytes' in reference:
        assert len(data) == reference['bytes']
    return data


def main():
    job = read(JOB)
    recorder._closed_job((ROOT / JOB).resolve(), job)
    guard_path = job['execution_resources']['guard_path']
    guard = read(guard_path)
    recorder._validate_guard_receipt(ROOT / guard_path, job, guard)
    recorder._guard_identity(job, guard)
    assert guard['status'] != 'running' and guard['returncode'] == 0
    assert not any(guard['guards'].values())
    stage_path = 'results/' + CID + '/stage-decision.json'
    manifest_path = 'results/' + CID + '/artifacts.json'
    stage, manifest = read(stage_path), read(manifest_path)
    assert stage['correctness_pass'] and stage['frozen_inputs_reverified'] and manifest['complete']
    assert [p['name'] for p in stage['populations']] == ['development', 'validation', 'confirmation']
    for item in manifest['files']:
        check(item)
    revision = dict(candidateId=CID, candidateTreeSha256=job['candidate_tree_sha256'],
                    receipt=job['candidate_revision'])
    rows = []
    for pop in stage['populations']:
        assert pop['status'] == 'passed' and len(pop['commands']) == 4
        assert all(pop[k] is True for k in ('retained_archive_identity', 'unobserved_observed_identity',
                   'exact_inverse', 'deterministic_repeat', 'complete_state_witness_identity'))
        raw = check(pop['input']); artifacts = pop['artifacts']
        arc = check(artifacts['encode'])
        assert check(artifacts['decode']) == raw
        assert check(artifacts['plain']) == check(artifacts['repeat']) == arc
        audits = [json.loads(check(x)) for x in pop['audits'].values()]
        assert all(a == audits[0] for a in audits)
        commands = pop['commands']
        assert all(c['returncode'] == 0 and not c['timeout'] and c['error'] is None for c in commands)
        phases = dict(zip(('plain', 'encode', 'decode', 'repeat'), [c.get('codec_resources') for c in commands]))
        missing = [item for c in commands for item in c.get('missing_diagnostics', [])]
        times = lambda key: phases[key]['elapsed_seconds'] if phases[key] is not None else None
        result = dict(schema='gamma.enwiki9.driver-result.v2', program_id=CID,
            program_name='Compact opcode field implementation', arm=pop['name'],
            candidate_revision=revision, timestamp=job['finished_at'], run_source=JOB,
            data_path=pop['input']['path'], data_size=len(raw), data_sha256=hashlib.sha256(raw).hexdigest(),
            data_md5=hashlib.md5(raw).hexdigest(), compressed_size=len(arc),
            compressed_sha256=hashlib.sha256(arc).hexdigest(), compressed_md5=hashlib.md5(arc).hexdigest(),
            roundtrip_ok=True, determinism=dict(scope='single-host', single_host_byte_equal=True),
            shared_state_synchronization=True, bits_per_byte=len(arc)*8/len(raw),
            compress_time_s=times('encode'), decompress_time_s=times('decode'),
            run_time_s=sum(c['elapsed_seconds'] for c in commands), phase_resources=phases,
            memory_kib=dict(peak=max((p['peak_process_rss_kib'] for p in phases.values() if p), default=None)),
            host=dict(machine=platform.machine(), node=platform.node(), python=platform.python_version(), system=platform.system()),
            run_purpose='diagnostic', execution_mode='discovery', timing_authority='diagnostic',
            run_scope_label=pop['name']+'-compact-parity', run_tags=['opcode-field', 'compact', 'parity', pop['name']],
            run_context='Fresh compact implementation replay on a reused measured population. Exact archive and shared state identity to retained D. This is implementation equivalence, not fresh model confirmation.',
            source_inventory=stage['package_files'], local_source_bytes=stage['local_source_bytes'],
            program_size=None, hutter_score=None, full_corpus_score_bytes=None, complete_package_bytes=None,
            score_accounting_complete=False, prize_claimable=False, qualification_status='not-certified',
            resource_evidence_complete=False, missing_diagnostics=missing, closed_guard=ref(guard_path),
            source_stage=ref(stage_path), artifacts=dict(archive=artifacts['encode'], restored=artifacts['decode'], repeat=artifacts['repeat']))
        rows.append((pop, result))
    terminal = dict(schema='gamma.enwiki9.opcode-field-compact-terminal.v1', candidate_id=CID,
        job=ref(JOB), guard=ref(guard_path), stage=ref(stage_path), artifact_manifest=ref(manifest_path),
        candidate_revision=revision, experiment=job['experiment'], target_complete_bytes=90000000,
        historical_frozen_experiment_target_bytes=99000000,
        archive_bytes={p['name']: p['archive_bytes'] for p, _ in rows},
        measurements=dict(correctness_pass=True, local_source_bytes=5746, local_source_saving_bytes=9657,
                          source_delta_from_original_parent_bytes=905, archive_saving_vs_retained_D_bytes=0),
        phases_closed=12, guard_flags=guard['guards'], guard_peaks=guard['peaks'],
        source_zip_cost=ref('operations/provenance/opcode_field_source_zip_cost_20260908.json'),
        synthetic_next_mechanism=ref('results/opcode_wiki_state_diagnostic_20260908/attempt01/receipt.json'),
        full_corpus_score_bytes=None, complete_package_bytes=None, objective_credit_bytes=0,
        next_decision='Retain the smaller equivalent implementation. Do not scale automatically: finish package obligations and test the diagnosed wiki-slot mismatch as one separately frozen prediction successor.',
        limits=['Repeated measured populations prove implementation equivalence only.',
                'Source saving is versus the observed implementation, not a new archive gain.',
                'The conditional twice-counted ZIP delta of1548 exceeds historical1541 archive saving; complete accounting, runtime and licenses remain unresolved.',
                'Shared-host resources are diagnostic; no calibrated qualification or full-corpus projection.'])
    assert not (ROOT / (OUT+'.json')).exists() and not (ROOT / OUT).exists()
    (ROOT / OUT).mkdir()
    write_json(ROOT / (OUT+'.json'), terminal)
    index = dict(schema='gamma.enwiki9.terminal-result-index.v1', job=ref(JOB), guard=ref(guard_path),
                 evidence=[ref(OUT+'.json'), ref(stage_path), ref(manifest_path)], arms=[])
    for pop, result in rows:
        path = OUT+'/'+pop['name']+'.json'
        write_json(ROOT/path, result)
        index['arms'].append(dict(arm=pop['name'], result=ref(path), artifacts=result['artifacts']))
    write_json(ROOT/(OUT+'/index.json'), index)
    print(json.dumps(dict(terminal=OUT+'.json', index=OUT+'/index.json', rows=len(rows), reflection_required=True)))


if __name__ == '__main__':
    main()
