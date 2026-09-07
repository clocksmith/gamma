#!/usr/bin/env python3
"""Normalize only the closed, published enumerative diagnostic; never run a codec."""
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import research_contracts

CID = 'dualstream_enumerative250k_q0_v3'
JID = '20260907T163610Z_dfcedb020f'
DEST = 'operations/provenance/dualstream_enumerative_terminal_20260907'


def load(path):
    return json.loads((ROOT/path).read_text())


def ref(path):
    data = (ROOT/path).read_bytes()
    return dict(path=path, sha256='sha256:'+hashlib.sha256(data).hexdigest())


def verify(row):
    assert ref(row['path'])['sha256'].removeprefix('sha256:') == row['sha256'].removeprefix('sha256:'),row['path']
    if 'bytes' in row:
        assert (ROOT/row['path']).stat().st_size == row['bytes'],row['path']


def main():
    contract_path='operations/adaptive/experiments/'+CID+'.json'
    contract=load(contract_path)
    research_contracts.validate_artifact(ROOT/contract_path,verify_files=True)
    job_path='operations/adaptive/completed/909_'+JID+'.json'
    guard_path='run_logs/adaptive/'+JID+'.resources/guard.json'
    job,guard=load(job_path),load(guard_path)
    result_dir='results/'+CID+'/'
    stage=load(result_dir+'stage-decision.json')
    assert job['state']=='completed' and job['returncode']==0
    assert job['execution_resources']['cleanup_complete'] and guard['status']=='complete'
    assert guard['returncode']==0 and not any(guard['guards'].values())
    assert not guard['latest_sample']['processes']
    assert stage['correctness_pass'] and stage['accounting_pass'] and stage['paired_program_identity_pass']
    assert stage['frozen_inputs_reverified'] and stage['native_phases']==15
    assert len(stage['commands'])==15 and all(p['returncode']==0 and not p['timeout'] and p['error'] is None for p in stage['commands'])
    for row in contract['inputs']:verify(row)
    for row in load(result_dir+'artifacts.json')['files']:verify(row)
    objective=contract['objective']
    revision=dict(candidateId=CID,candidateTreeSha256=job['candidate_tree_sha256'],receipt=job['candidate_revision'])
    outputs={}
    idx=dict(schema='gamma.enwiki9.terminal-result-index.v1',job=ref(job_path),guard=ref(guard_path),arms=[],
             evidence=[ref(result_dir+'stage-decision.json'),ref(result_dir+'costs-table.json')])
    raw_path='operations/evidence/fixtures/dualstream_opening250k_v1.raw'
    raw=(ROOT/raw_path).read_bytes()
    for row in stage['arms']:
        arm=row['arm']['id']
        for artifact in row['artifacts'].values():verify(artifact)
        archive=(ROOT/row['artifacts']['archive']['path']).read_bytes()
        restored=(ROOT/row['artifacts']['restored']['path']).read_bytes()
        repeated=(ROOT/row['artifacts']['repeat']['path']).read_bytes()
        assert raw==restored and archive==repeated
        assert len(archive)==row['archive_bytes']==sum(row['accounting'].values())
        encode=load(result_dir+arm+'-encode.stdout')
        decode=load(result_dir+arm+'-decode.stdout')
        repeat=load(result_dir+arm+'-repeat.stdout')
        assert encode['result']==repeat['result']
        if row['arm']['backend']=='enumerative':
            assert encode['result']['section_hashes']==decode['result']['section_hashes']
        result=dict(schema='gamma.enwiki9.driver-result.v2',program_id=CID,program_name='Fixed enumerative grammar '+arm,
            arm=arm,candidate_revision=revision,objective=objective,timestamp=job['finished_at'],
            run_source=job_path,run_purpose='diagnostic',run_scope_label='opening250KB-fixed-program-'+arm,
            run_tags=['enumerative','fixed-program-reserialization','diagnostic',arm],
            data_path=raw_path,data_size=len(raw),data_sha256=hashlib.sha256(raw).hexdigest(),data_md5=hashlib.md5(raw).hexdigest(),
            compressed_size=len(archive),compressed_sha256=hashlib.sha256(archive).hexdigest(),compressed_md5=hashlib.md5(archive).hexdigest(),
            bits_per_byte=8*len(archive)/len(raw),program_size=None,hutter_score=None,
            hutter_score_kind='diagnostic-fixed-program-reserialization',complete_package_bytes=None,full_corpus_score_bytes=None,
            prize_claimable=False,score_accounting_complete=False,resource_evidence_complete=False,
            qualification_status='not-certified',execution_mode='discovery',timing_authority='diagnostic',
            roundtrip_ok=True,determinism=dict(scope='raw-encoder-determinism-unmeasured',single_host_byte_equal=None),
            deterministic_reserialization_repeat=True,raw_encoder_repeat_proved=False,repeat_scope='fixed-program-reserialization',
            compress_time_s=None,decompress_time_s=decode['elapsed_seconds'],
            reserialization_validation_time_s=encode['elapsed_seconds'],reserialization_validation_cpu_seconds=encode['cpu_seconds'],
            reserialization_repeat_time_s=repeat['elapsed_seconds'],
            run_time_s=sum(p['elapsed_seconds'] for p in stage['commands'] if p['phase'].startswith(arm+'-')),
            run_time_scope='Fixed selected-program serialization, separate decode and fixed-source repeat; raw discovery excluded.',
            memory_kib=dict(peak=max(encode['peak_process_rss_kib'],decode['peak_process_rss_kib'],repeat['peak_process_rss_kib'])),
            host=dict(machine=platform.machine(),node=platform.node(),python=platform.python_version(),system=platform.system()),
            paired_program_identity_pass=True,accounting=row['accounting'],artifacts=row['artifacts'],
            missing_diagnostics=job['execution_resources']['missing_diagnostics'],closed_guard=ref(guard_path),closed_job=ref(job_path),
            source_arm_result=ref(result_dir+arm+'.result.json'),
            run_context='Byte-alphabet multiset ranks over fixed serialized grammar sections; exact inverse and fixed-source repeats, no raw search or package qualification.',
            reserialization_repeat=dict(single_host_byte_equal=True,selection_repeated=False,
                first_run_sha256=hashlib.sha256(archive).hexdigest(),second_run_sha256=hashlib.sha256(repeated).hexdigest(),
                first_run_md5=hashlib.md5(archive).hexdigest(),second_run_md5=hashlib.md5(repeated).hexdigest(),first_divergence_byte=None))
        out=DEST+'/normalized/'+arm+'.json';outputs[out]=result
        data=(json.dumps(result,indent=2,sort_keys=True)+'\n').encode()
        idx['arms'].append(dict(arm=arm,result=dict(path=out,sha256='sha256:'+hashlib.sha256(data).hexdigest()),artifacts=row['artifacts']))
    costs=stage['costs']
    measurements=dict(correctness_pass=True,frozen_inputs_reverified=True,continuous_guard_pass=True,artifact_closure_pass=True,
        accounting_pass=True,paired_program_identity_pass=True,promotion_authorized=False,scientific_rejection_applicable=False,
        native_phases=15,raw_bytes=len(raw),**{k:costs[k] for k in ['enum_vs_fixed_deflate_saved_bytes','token_argument_saved_bytes','enum_vs_plain_deflate_saved_bytes']})
    artifacts=[dict(id='artifact-'+str(i),**ref(p)) for i,p in enumerate(contract['outputs']) if p!=result_dir+'decision.json']
    def evaluations(key):
        return [dict(p,observed=measurements[p['measurement']],passed=measurements[p['measurement']]==p['threshold']) for p in contract[key]]
    decision=dict(schema='gamma.enwiki9.adaptive-experiment-result.v1',objective=objective,experiment=ref(contract_path),
        candidateId=CID,candidateRevision=revision,evidenceClass='diagnostic',objectiveCreditBytes=0,measurements=measurements,
        promotionPredicates=evaluations('promotionPredicates'),killPredicates=evaluations('killPredicates'),
        promotionPass=False,killPass=False,decision='retry',artifacts=artifacts,generatedUtc=job['finished_at'])
    outputs[result_dir+'decision.json']=decision
    outputs[DEST+'/index.json']=idx
    audit=dict(schema='gamma.enwiki9.enumerative-terminal.v1',candidate_id=CID,job=ref(job_path),guard=ref(guard_path),
        experiment=ref(contract_path),stage=ref(result_dir+'stage-decision.json'),measurements=measurements,costs=costs,
        enum_rank_payload_bytes=sum(v for k,v in stage['arms'][2]['accounting'].items() if k.endswith('_rank_bytes')),
        gate_resources=dict(elapsed_seconds=guard['elapsed_s'],peaks=guard['peaks'],samples=guard['sample_count'],guards=guard['guards']),
        repeated_argument_references={r['arm']['id']:sum(f['repeated_argument_references'] for f in r['frames']) for r in stage['arms']},
        known_source_union_bytes=sum(f['bytes'] for f in costs['package_source']),
        result='Both fixed grammar enumeration and token argument realization lose complete archive bytes; retain evaluator, park exact configuration.',
        limits=['No full-corpus size certificate.','No new grammar discovery or corpus shared-binding mutation.',
                'Complete counted package/runtime/license/options closure unknown.','Fixed-source repeats only.',
                'No conclusion about all grammars, other chunking or token-alphabet enumeration.'],
        full_corpus_score_bytes=None,complete_package_bytes=None,objective_credit_bytes=0)
    outputs['operations/provenance/dualstream_enumerative_terminal_20260907.json']=audit
    print(json.dumps(outputs))


if __name__=='__main__':
    main()
