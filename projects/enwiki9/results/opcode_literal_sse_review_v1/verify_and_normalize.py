"""Review one terminal corpus comparison; never inspect it as completed early."""
import hashlib
import json
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[2]
CID = 'opcode_literal_sse250k_q0_v1'
JOB = '20260909T023015Z_9564fe8ecc'
OUT = ROOT / 'operations/provenance/opcode_literal_sse_terminal_20260909'


def read(path):
    return json.loads((ROOT / path).read_text())


def ref(path):
    path = Path(path)
    if path.is_absolute(): path = path.relative_to(ROOT)
    return dict(path=str(path), sha256='sha256:'+hashlib.sha256((ROOT/path).read_bytes()).hexdigest())


def verify(row):
    data = (ROOT/row['path']).read_bytes()
    assert hashlib.sha256(data).hexdigest() == row['sha256'].removeprefix('sha256:'), row['path']
    if 'bytes' in row: assert len(data) == row['bytes'], row['path']
    return data


def write(path, value):
    with path.open('x') as f: json.dump(value, f, indent=2); f.write('\n')


def main():
    jobs = list((ROOT/'operations/adaptive/completed').glob('*'+JOB+'.json'))
    assert len(jobs) == 1, 'job has not closed in completed'
    jobpath = jobs[0].relative_to(ROOT); job = read(jobpath)
    guardpath = Path('run_logs/adaptive')/(JOB+'.resources/guard.json'); guard = read(guardpath)
    assert job['state'] == 'completed' and job['returncode'] == 0
    assert job['execution_resources']['cleanup_complete'] is True
    assert guard['status'] == 'complete' and guard['returncode'] == 0
    assert not any(guard['guards'].values()) and not Path(guard['cgroup']['path']).exists()
    stagepath = Path('results')/CID/'stage-decision.json'
    manifestpath = stagepath.parent/'artifacts.json'
    stage, manifest = read(stagepath), read(manifestpath)
    assert stage['status'] == 'passed' and stage['correctness_pass']
    assert stage['frozen_inputs_reverified'] and stage['matching_arm_decoders']
    assert not stage['original_decoder_all_arms']
    assert stage['non_sse_state_equal'] and stage['parse_events_equal']
    assert stage['experiment'] == job['experiment'] and stage['candidate_id'] == CID
    verify(job['experiment']); verify(job['candidate_revision'])
    assert manifest['complete'] and len(stage['commands']) == 10
    assert all(c['returncode'] == 0 and not c['timeout'] for c in stage['commands'])
    for item in manifest['files']: verify(item)
    raw = verify(stage['input']); assert len(raw) == 250000
    plan = read(Path('programs')/CID/'gate-plan.json')
    for category in ('source_files','runtime_files','evidence','package_files'):
        for item in plan[category]: verify(item)
    assert sum(r['bytes'] for r in plan['package_files']) == 7117 and len(plan['package_files']) == 3
    for arm, row in stage['arms'].items():
        arc, repeat, restored = [verify(row['artifacts'][k]) for k in ('archive','repeat','restored')]
        assert arc == repeat and restored == raw and len(arc) == row['archive_bytes']
        audits = [json.loads(verify(row['audits'][k])) for k in ('encode','decode','repeat')]
        assert audits[0] == audits[1] == audits[2] == row['audit']
        assert audits[0]['parent']['checkpoints']
        for key in ('non_sse','parse_sha256','parse_events','updates_by_mode'):
            assert audits[0][key] == stage['arms']['P']['audit'][key]
    assert stage['arms']['P']['audit'] == stage['arms']['K']['audit']
    assert verify(stage['arms']['P']['artifacts']['archive']) == verify(plan['parent_archive'])
    assert stage['arms']['P']['audit']['parent'] == json.loads(verify(plan['parent_audit']))
    assert verify(stage['arms']['P']['artifacts']['archive']) == verify(stage['arms']['K']['artifacts']['archive'])
    assert verify(stage['arms']['D']['artifacts']['archive']) == (ROOT/stagepath.parent/'D.plain.arc').read_bytes()
    gain = stage['arms']['P']['archive_bytes'] - stage['arms']['D']['archive_bytes']
    assert gain == stage['archive_saving_bytes'] and stage['source_delta_bytes'] == 1371
    revision = dict(candidateId=CID, candidateTreeSha256=job['candidate_tree_sha256'],receipt=job['candidate_revision'])
    OUT.mkdir(exist_ok=False)
    summary = dict(schema='gamma.enwiki9.opcode-literal-sse-terminal.v1',status='passed',
        scientific_verdict='archive-gain' if gain>0 else 'archive-loss-or-tie',owner='root_explore',
        candidate_id=CID,job=ref(jobpath),guard=ref(guardpath),experiment=job['experiment'],
        candidate_revision=revision,stage=ref(stagepath),artifact_manifest=ref(manifestpath),
        artifact_files_rehashed=len(manifest['files']),phases_closed=10,population=stage['input'],
        archive_bytes={a:r['archive_bytes'] for a,r in stage['arms'].items()},
        measurements=dict(archive_saving_bytes=gain,correctness_pass=True,controls_equivalent=True,
                          source_delta_bytes=1371,archive_minus_local_source_delta_bytes=gain-1371),
        non_sse_state_equal=True,parse_events_equal=True,matching_arm_decoders=True,
        updates_by_mode=stage['arms']['D']['audit']['updates_by_mode'],
        guard_peaks=guard['peaks'],guard_flags=guard['guards'],guard_elapsed_seconds=guard['elapsed_s'],
        source_files=plan['package_files'],local_source_bytes=7117,complete_package_bytes=None,
        full_corpus_score_bytes=None,objective_credit_bytes=0,
        limits=['One development250KB population; no confirmation or full-corpus inference.',
                'Local source delta is separate from complete runtime/license/options/multiplicity accounting.',
                'Shared-host discovery measurements do not constitute prize resource qualification.'])
    summarypath = OUT.with_suffix('.json');write(summarypath,summary)
    index = dict(schema='gamma.enwiki9.terminal-result-index.v1',job=ref(jobpath),guard=ref(guardpath),
                 arms=[],evidence=[ref(summarypath),ref(stagepath),ref(manifestpath)])
    for arm,row in stage['arms'].items():
        arc = verify(row['artifacts']['archive'])
        resources = {c['phase'].split('-',1)[1]:c.get('codec_resources') for c in row['commands']}
        missing = [k for k,v in resources.items() if v is None or v.get('peak_process_rss_kib') is None]
        def metric(phase,key):
            value=resources.get(phase);return value.get(key) if value else None
        result = dict(schema='gamma.enwiki9.driver-result.v2',arm=arm,program_id=CID,
            program_name='Literal-only SSE training development comparison',candidate_revision=revision,
            timestamp=job['finished_at'],artifacts=row['artifacts'],closed_guard=ref(guardpath),source_stage=ref(stagepath),
            compressed_size=len(arc),compressed_sha256=hashlib.sha256(arc).hexdigest(),compressed_md5=hashlib.md5(arc).hexdigest(),
            data_size=len(raw),data_path=stage['input']['path'],data_sha256=hashlib.sha256(raw).hexdigest(),data_md5=hashlib.md5(raw).hexdigest(),
            bits_per_byte=len(arc)*8/len(raw),compress_time_s=metric('encode','elapsed_seconds'),
            decompress_time_s=metric('decode','elapsed_seconds'),
            run_time_s=sum(v['elapsed_seconds'] for v in resources.values() if v) if all(resources.values()) else None,
            phase_resources=resources,memory_kib=dict(peak=max((v.get('peak_process_rss_kib') or 0 for v in resources.values() if v),default=0) or None),
            missing_diagnostics=missing,roundtrip_ok=True,determinism=dict(scope='single-host',single_host_byte_equal=True),
            shared_state_synchronization=True,
            run_context='Frozen opening250KB, matching-arm decoders, independent inverses/repeats, within-arm full witnesses, unchanged non-SSE state and explicit copy parse.',
            run_purpose='diagnostic',run_scope_label='opening250KB-literal-sse-'+arm,run_source=str(jobpath),
            run_tags=['literal-sse','standalone','development','diagnostic',arm],execution_mode='discovery',
            timing_authority='diagnostic',qualification_status='not-certified',resource_evidence_complete=False,
            score_accounting_complete=False,prize_claimable=False,complete_package_bytes=None,
            full_corpus_score_bytes=None,hutter_score=None,program_size=None,local_source_bytes=7117,
            source_inventory=plan['package_files'],host=dict(machine=platform.machine(),node=platform.node(),
            python=platform.python_version(),system=platform.system()))
        path=OUT/(arm+'.json');write(path,result)
        index['arms'].append(dict(arm=arm,result=ref(path),artifacts=row['artifacts']))
    write(OUT/'index.json',index)
    print(json.dumps(dict(archive_bytes=summary['archive_bytes'],archive_saving_bytes=gain,
                         source_adjusted_difference=gain-1371)))


if __name__ == '__main__':
    main()
