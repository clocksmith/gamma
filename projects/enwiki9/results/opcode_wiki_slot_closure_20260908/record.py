"""Validate and normalize the closed wiki-slot job before its reflection."""
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import record_driver_result as recorder
from dualstream_grammar_gate_v1 import write_json
CID='opcode_wiki_slot_v1'
JID='20260908T162205Z_46ebdbaee4'
JOB='operations/adaptive/completed/909_'+JID+'.json'
OUT='operations/provenance/opcode_wiki_slot_terminal_20260908'


def read(path):return json.loads((ROOT/path).read_text())
def ref(path):return dict(path=path,sha256='sha256:'+hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
def check(row):
    path=recorder.project_path(row['path']);data=path.read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['sha256'].removeprefix('sha256:')
    assert 'bytes' not in row or len(data)==row['bytes']
    return data


def main():
    job=read(JOB);recorder._closed_job((ROOT/JOB).resolve(),job)
    guard_path=job['execution_resources']['guard_path'];guard=read(guard_path)
    recorder._validate_guard_receipt(ROOT/guard_path,job,guard);recorder._guard_identity(job,guard)
    assert guard['status']!='running' and guard['returncode']==0 and not any(guard['guards'].values())
    stage_path='results/'+CID+'/stage-decision.json';manifest_path='results/'+CID+'/artifacts.json'
    stage=read(stage_path);manifest=read(manifest_path)
    assert stage['status']=='passed' and stage['correctness_pass'] and stage['frozen_inputs_reverified']
    assert manifest['complete'] and len(stage['commands'])==10
    for row in manifest['files']:check(row)
    raw=check(stage['input'])
    revision=dict(candidateId=CID,candidateTreeSha256=job['candidate_tree_sha256'],receipt=job['candidate_revision'])
    results=[]
    for arm in 'PKD':
        data=stage['arms'][arm];a=data['artifacts'];arc=check(a['archive'])
        assert raw==check(a['restored']) and arc==check(a['repeat'])
        audits=[json.loads(check(r)) for r in data['audits'].values()]
        assert all(x==audits[0] for x in audits) and audits[0]==data['audit']
        commands=data['commands'];assert all(c['returncode']==0 and not c['timeout'] and c['error'] is None for c in commands)
        resources=dict(zip(('encode','decode','repeat'),[c.get('codec_resources') for c in commands]))
        def timing(name):return resources[name]['elapsed_seconds'] if resources[name] else None
        result=dict(schema='gamma.enwiki9.driver-result.v2',program_id=CID,program_name='Decoded wiki-slot comparison',
            arm=arm,candidate_revision=revision,timestamp=job['finished_at'],run_source=JOB,
            data_path=stage['input']['path'],data_size=len(raw),data_sha256=hashlib.sha256(raw).hexdigest(),data_md5=hashlib.md5(raw).hexdigest(),
            compressed_size=len(arc),compressed_sha256=hashlib.sha256(arc).hexdigest(),compressed_md5=hashlib.md5(arc).hexdigest(),
            roundtrip_ok=True,determinism=dict(scope='single-host',single_host_byte_equal=True),shared_state_synchronization=True,
            bits_per_byte=len(arc)*8/len(raw),compress_time_s=timing('encode'),decompress_time_s=timing('decode'),
            run_time_s=sum(c['elapsed_seconds'] for c in commands),phase_resources=resources,
            memory_kib=dict(peak=max((r['peak_process_rss_kib'] for r in resources.values() if r),default=None)),
            host=dict(machine=platform.machine(),node=platform.node(),python=platform.python_version(),system=platform.system()),
            run_purpose='diagnostic',execution_mode='discovery',timing_authority='diagnostic',run_scope_label='opening250KB-wiki-slot-'+arm,
            run_tags=['wiki-slot','standalone','diagnostic',arm],
            run_context='One fixed development comparison exposing only the decoder-reconstructed wiki slot. P/K identity, independent inverses, raw repeats and complete state witnesses pass. Package economics are separate.',
            source_inventory=stage['package_files'],local_source_bytes=stage['local_source_bytes'],
            program_size=None,hutter_score=None,full_corpus_score_bytes=None,complete_package_bytes=None,
            score_accounting_complete=False,prize_claimable=False,qualification_status='not-certified',resource_evidence_complete=False,
            missing_diagnostics=[x for c in commands for x in c.get('missing_diagnostics',[])],closed_guard=ref(guard_path),source_stage=ref(stage_path),artifacts=a)
        results.append(result)
    assert stage['arms']['P']['audit']['parent']==stage['arms']['K']['audit']['parent']
    assert check(stage['arms']['P']['artifacts']['archive'])==check(stage['arms']['K']['artifacts']['archive'])
    gain=stage['archive_saving_bytes'];cost_path='results/opcode_wiki_slot_source_zip_20260908/attempt01/cost.json';cost=read(cost_path)
    terminal=dict(schema='gamma.enwiki9.opcode-wiki-slot-terminal.v1',candidate_id=CID,job=ref(JOB),guard=ref(guard_path),
        stage=ref(stage_path),artifact_manifest=ref(manifest_path),candidate_revision=revision,experiment=job['experiment'],
        target_complete_bytes=90000000,population=stage['input'],archive_bytes={a:stage['arms'][a]['archive_bytes'] for a in 'PKD'},
        measurements=dict(correctness_pass=True,controls_equivalent=True,archive_saving_bytes=gain,source_delta_bytes=stage['source_delta_bytes'],
                          conditional_source_adjusted_saving_bytes=gain-cost['conditional_added_counted_source_bytes']),
        post_update_slot_occupancy={a:{k:stage['arms'][a]['audit'][k] for k in ['slot_byte_counts','changed_slot_bytes','mode_slot_byte_counts','mode_changed_slot_bytes']} for a in 'PKD'},
        opportunity_definition='Counts are slot occupancy immediately after each decoded modeled byte, not a count of improved predictions. Copy-mode allocation is explicit; byte-wise predictive loss attribution was not recorded.',
        source_zip_cost=ref(cost_path),phases_closed=10,guard_flags=guard['guards'],guard_peaks=guard['peaks'],
        interpretation=stage['interpretation'],full_corpus_score_bytes=None,complete_package_bytes=None,objective_credit_bytes=0,
        next_decision='Review development archive change, activation and package costs before selecting one new action. No automatic confirmation or larger gate.',
        limits=['Development only; no fresh transfer evidence.','A positive archive delta is not a complete-package result.',
                'No causal attribution to individual slots follows from occupancy or arithmetic output timing.',
                'Concurrent timing is diagnostic; resource calibration, license closure and full-corpus replay remain unresolved.'])
    assert not (ROOT/(OUT+'.json')).exists() and not (ROOT/OUT).exists()
    (ROOT/OUT).mkdir();write_json(ROOT/(OUT+'.json'),terminal)
    index=dict(schema='gamma.enwiki9.terminal-result-index.v1',job=ref(JOB),guard=ref(guard_path),
               evidence=[ref(OUT+'.json'),ref(stage_path),ref(manifest_path)],arms=[])
    for result in results:
        path=OUT+'/'+result['arm']+'.json';write_json(ROOT/path,result)
        index['arms'].append(dict(arm=result['arm'],result=ref(path),artifacts=result['artifacts']))
    write_json(ROOT/(OUT+'/index.json'),index)
    print(json.dumps(dict(terminal=OUT+'.json',index=OUT+'/index.json',archive_saving_bytes=gain,reflection_required=True)))


if __name__=='__main__':main()
