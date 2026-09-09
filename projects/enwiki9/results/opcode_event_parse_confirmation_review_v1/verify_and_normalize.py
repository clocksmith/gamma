"""Review the one closed frozen confirmation; preserve all measured source."""
import datetime
import hashlib
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[2]
CID = 'opcode_event_parse_confirmation1m_q0_v1'
JOB = '20260909T005909Z_a4db760844'
OUT = ROOT / 'operations/provenance/opcode_event_parse_confirmation_terminal_20260909'


def read(path):
    return json.loads((ROOT / path).read_text())


def ref(path):
    path = Path(path)
    if path.is_absolute():
        path = path.relative_to(ROOT)
    return dict(path=str(path), sha256='sha256:' + hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def verify(row):
    data = (ROOT / row['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256'].removeprefix('sha256:'), row['path']
    if 'bytes' in row:
        assert len(data) == row['bytes'], row['path']
    return data


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2) + '\n')


def main():
    jobs = list((ROOT / 'operations/adaptive/completed').glob('*' + JOB + '.json'))
    assert len(jobs) == 1, 'job has not closed in completed'
    jobpath = jobs[0].relative_to(ROOT)
    job = read(jobpath)
    guardpath = Path('run_logs/adaptive') / (JOB + '.resources/guard.json')
    guard = read(guardpath)
    assert job['state'] == 'completed' and job['returncode'] == 0
    assert job['execution_resources']['cleanup_complete'] is True
    assert guard['status'] == 'complete' and guard['returncode'] == 0
    assert not any(guard['guards'].values())
    assert not Path(guard['cgroup']['path']).exists(), 'owned cgroup remains'
    stagepath = Path('results') / CID / 'stage-decision.json'
    manifestpath = stagepath.parent / 'artifacts.json'
    stage, manifest = read(stagepath), read(manifestpath)
    assert stage['status'] == 'passed' and stage['correctness_pass'] is True
    assert stage['frozen_inputs_reverified'] and stage['original_decoder_all_arms']
    assert manifest['complete'] and len(stage['commands']) == 10
    assert all(c['returncode'] == 0 and not c['timeout'] for c in stage['commands'])
    for artifact in manifest['files']:
        verify(artifact)
    raw = verify(stage['input'])
    assert len(raw) == 1000000
    plan = read(Path('programs') / CID / 'gate-plan.json')
    for category in ['source_files', 'runtime_files', 'evidence', 'package_files']:
        for artifact in plan[category]:
            verify(artifact)
    assert sum(a['bytes'] for a in plan['package_files']) == 7742
    assert len(plan['package_files']) == 3
    for arm, row in stage['arms'].items():
        archive, repeated, restored = [verify(row['artifacts'][k]) for k in ['archive', 'repeat', 'restored']]
        assert archive == repeated and restored == raw
        audits = [json.loads(verify(row['audits'][k])) for k in ['encode', 'decode', 'repeat']]
        assert audits[0] == audits[1] == audits[2] == row['audit']
        assert audits[0]['parent']['checkpoints']
    assert stage['arms']['P']['audit'] == stage['arms']['K']['audit']
    assert verify(stage['arms']['P']['artifacts']['archive']) == verify(stage['arms']['K']['artifacts']['archive'])
    assert verify(stage['arms']['D']['artifacts']['archive']) == (ROOT / stagepath.parent / 'D.plain.arc').read_bytes()
    gain = stage['arms']['P']['archive_bytes'] - stage['arms']['D']['archive_bytes']
    assert gain == stage['archive_saving_bytes']
    assert stage['added_source_zip_bytes'] == 1895
    assert stage['archive_minus_one_source_zip_delta_bytes'] == gain - 1895
    assert stage['source_component_gate_pass'] == (gain > 1895)
    verify(job['candidate_revision'])
    revision = dict(candidateId=CID, candidateTreeSha256=job['candidate_tree_sha256'], receipt=job['candidate_revision'])
    OUT.mkdir(exist_ok=False)
    summary = dict(schema='gamma.enwiki9.opcode-event-parse-confirmation-terminal.v1', status='passed',
        scientific_verdict='source-component-pass' if gain > 1895 else 'source-component-failure',
        owner='root_explore', candidate_id=CID, job=ref(jobpath), guard=ref(guardpath),
        experiment=job['experiment'], candidate_revision=revision, stage=ref(stagepath),
        artifact_manifest=ref(manifestpath), artifact_files_rehashed=len(manifest['files']), phases_closed=10,
        population=stage['input'], population_identity=ref('operations/provenance/opcode_event_parse_confirmation_population_v1.json'),
        archive_bytes={a:r['archive_bytes'] for a,r in stage['arms'].items()},
        measurements=dict(archive_saving_bytes=gain, correctness_pass=True, controls_equivalent=True,
                          source_delta_bytes=1996), guard_peaks=guard['peaks'], guard_flags=guard['guards'],
        guard_elapsed_seconds=guard['elapsed_s'], source_files=plan['package_files'], local_source_bytes=7742,
        source_zip_cost=ref('results/opcode_event_parse_source_zip_v1/attempt01/cost.json'),
        added_source_zip_bytes=1895, archive_minus_one_source_zip_delta_bytes=gain-1895,
        source_component_gate_pass=gain > 1895,
        complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
        limits=['One separately frozen1MB confirmation; no tuning or automatic10MB launch.',
                'The fixed one-source-ZIP predicate is not complete submission accounting.',
                'Runtime, licenses, options and official multiplicities remain unresolved.',
                'Shared-host discovery guard evidence is not prize resource qualification.'])
    summarypath = OUT.with_suffix('.json')
    write(summarypath, summary)
    index = dict(schema='gamma.enwiki9.terminal-result-index.v1', job=ref(jobpath), guard=ref(guardpath), arms=[],
                 evidence=[ref(summarypath), ref(stagepath), ref(manifestpath), summary['source_zip_cost']])
    for arm, row in stage['arms'].items():
        archive = verify(row['artifacts']['archive'])
        resources = {c['phase'].split('-',1)[1]: c['codec_resources'] for c in row['commands']}
        missing = [k for k,v in resources.items() if v.get('peak_process_rss_kib') is None]
        result = dict(schema='gamma.enwiki9.driver-result.v2', arm=arm, program_id=CID,
            program_name='Fixed codec1MB event-pricing confirmation', candidate_revision=revision,
            timestamp=job['finished_at'], artifacts=row['artifacts'], closed_guard=ref(guardpath), source_stage=ref(stagepath),
            compressed_size=len(archive), compressed_sha256=hashlib.sha256(archive).hexdigest(),
            compressed_md5=hashlib.md5(archive).hexdigest(), data_size=len(raw), data_path=stage['input']['path'],
            data_sha256=hashlib.sha256(raw).hexdigest(), data_md5=hashlib.md5(raw).hexdigest(),
            bits_per_byte=len(archive)*8/len(raw), compress_time_s=resources['encode']['elapsed_seconds'],
            decompress_time_s=resources['decode']['elapsed_seconds'],
            run_time_s=sum(r['elapsed_seconds'] for r in resources.values()), phase_resources=resources,
            memory_kib=dict(peak=max((r.get('peak_process_rss_kib') or 0) for r in resources.values()) or None),
            missing_diagnostics=missing, roundtrip_ok=True, determinism=dict(scope='single-host',single_host_byte_equal=True),
            shared_state_synchronization=True, run_context='Frozen reserved1MB confirmation: unchanged codec, original decoder, exact inverses, repeats, complete witnesses and observation parity. Archive gain and fixed source increment remain separate.',
            run_purpose='diagnostic', run_scope_label='reserved1MB-event-pricing-'+arm,
            run_source=str(jobpath), run_tags=['event-pricing','standalone','confirmation','diagnostic',arm],
            execution_mode='discovery', timing_authority='diagnostic', qualification_status='not-certified',
            resource_evidence_complete=False, score_accounting_complete=False, prize_claimable=False,
            complete_package_bytes=None, full_corpus_score_bytes=None, hutter_score=None, program_size=None,
            local_source_bytes=7742, source_inventory=plan['package_files'],
            host=dict(machine=platform.machine(),node=platform.node(),python=platform.python_version(),system=platform.system()))
        path = OUT / (arm+'.json')
        write(path, result)
        index['arms'].append(dict(arm=arm,result=ref(path),artifacts=row['artifacts']))
    write(OUT / 'index.json', index)
    print(json.dumps(dict(archive_bytes=summary['archive_bytes'],archive_saving_bytes=gain,source_component_delta=gain-1895)))


if __name__ == '__main__':
    main()
