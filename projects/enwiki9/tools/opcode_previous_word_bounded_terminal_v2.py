#!/usr/bin/env python3
"""Close the fixed confirmation from retained evidence; never execute a codec."""
import hashlib
import json
from pathlib import Path
import platform
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import opcode_previous_word_bounded_gate_v2 as gate
from tools import record_driver_result as recorder

CID = gate.CID
JID = '20260912T213632Z_3ebb7f46fa'
OUT = ROOT / 'operations/provenance/opcode_previous_word_confirmation_v3_terminal_20260912'


def read(path):
    return json.loads(path.read_text())


def ref(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def write(path, data):
    with path.open('x') as f:
        json.dump(data, f, sort_keys=True, indent=2)
        f.write('\n')


def truth(values):
    values = list(values)
    return False if False in values else None if None in values else True


def main():
    jobs = [p for state in ('completed','failed','cancelled')
            for p in (ROOT/'operations/adaptive'/state).glob('*_'+JID+'.json')]
    assert len(jobs) == 1, 'Job must be closed before terminal measurement'
    jobpath = jobs[0]; job = read(jobpath)
    assert job["state"] == "failed" and job["returncode"] == 1
    recorder._closed_job(jobpath, job)
    reconciliation_path = ROOT/"operations/provenance/opcode_word_v3_enospc_reconciliation_20260912.json"
    reconciliation = read(reconciliation_path)
    assert reconciliation["job"] == ref(jobpath)
    assert reconciliation["cgroup_absent"] and not reconciliation["matching_codec_processes"]
    gp = ROOT/job['execution_resources']['guard_path']; guard = read(gp)
    recorder._guard_identity(job, guard)
    assert guard['status'] == 'running' and guard['returncode'] is None
    assert ref(gp) == reconciliation['guard']
    assert '[Errno 28] No space left on device' in (ROOT/reconciliation['log']['path']).read_text()
    guard_schema = 'nonterminal-v3-snapshot; no final resource certification'
    OUT.mkdir(exist_ok=False)
    directory = ROOT/'results'/CID
    plan = read(ROOT/gate.INPUTS)
    stagepath = directory/'stage-decision.json'
    stage = read(stagepath) if stagepath.exists() else {}
    binding_errors=[]
    for collection in ['source_files','runtime_files','evidence','materialization','package_files']:
        for row in plan[collection]:
            path=ROOT/row['path']
            if not path.is_file() or len(path.read_bytes())!=row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
                binding_errors.append(row['path'])
    for key in ['input','parent_archive','parent_audit']:
        row=plan[key];assert ref(ROOT/row['path'])==row
    raw=(ROOT/plan['input']['path']).read_bytes()
    with (ROOT/'data/enwik9').open('rb') as f:
        f.seek(819000000);assert f.read(1000000)==raw
    rows={}; audits={}; failures=[]; phases=[]
    for arm in ['P','K','D','S','release-D']:
        where=directory/('release' if arm=='release-D' else 'controls'); a='D' if arm=='release-D' else arm
        records={}; observed={}; artifacts={}; resources={}
        for mode in ['encode','decode','repeat']+(['plain'] if a=='D' else []):
            ep=where/(a+'-'+mode+'.execution.json')
            if ep.exists():
                record=read(ep);phases.append(dict(arm=arm,mode=mode,evidence=ref(ep),record=record));records[mode]=record
                if record.get('timeout') or record.get('returncode')!=0:
                    err=where/(a+'-'+mode+'.stderr');text=err.read_text() if err.exists() else ''
                    failures.append(dict(arm=arm,phase=mode,returncode=record.get('returncode'),timeout=record.get('timeout'),memory_stop='MemoryError' in text,stderr=ref(err) if err.exists() else None))
                stdout=where/(a+'-'+mode+'.stdout')
                if stdout.exists():
                    try:resources[mode]=read(stdout)
                    except ValueError:pass
            ap=where/(a+'-'+mode+'.audit.json')
            if ap.exists() and records.get(mode,{}).get('returncode')==0:
                observed[mode]=gate.base.read_audit(ap)
        for key,suffix,mode in [('archive','.arc','encode'),('restored','.raw','decode'),('repeat','.repeat.arc','repeat'),('plain','.plain.arc','plain')]:
            p=where/(a+suffix)
            if p.exists() and records.get(mode,{}).get('returncode')==0:artifacts[key]=ref(p)
        inverse=((ROOT/artifacts['restored']['path']).read_bytes()==raw) if 'restored' in artifacts else None
        repeat=((ROOT/artifacts['archive']['path']).read_bytes()==(ROOT/artifacts['repeat']['path']).read_bytes()) if {'archive','repeat'}<=artifacts.keys() else None
        state=truth(observed['encode']==observed[m] if 'encode' in observed and m in observed else None for m in ['decode','repeat'])
        plain=((ROOT/artifacts['archive']['path']).read_bytes()==(ROOT/artifacts['plain']['path']).read_bytes()) if {'archive','plain'}<=artifacts.keys() else None
        size=artifacts.get('archive',{}).get('bytes')
        rows[arm]=dict(archive_bytes=size,exact_inverse=inverse,encode_decode_state_identity=(observed['encode']==observed['decode']) if {'encode','decode'}<=observed.keys() else None,repeat_byte_identity=repeat,state_synchronization=state,observed_plain_identity=plain if a=='D' else 'not-required',artifacts=artifacts,audits={m:ref(where/(a+'-'+m+'.audit.json')) for m in observed},phase_resources=resources)
        audits[arm]=observed
    def equal_archives(a,b):
        x=rows[a]['artifacts'].get('archive');y=rows[b]['artifacts'].get('archive')
        return (ROOT/x['path']).read_bytes()==(ROOT/y['path']).read_bytes() if x and y else None
    def audit_equal(a,b,field=None):
        x=audits[a].get('encode');y=audits[b].get('encode')
        return (x[field]==y[field] if field else x==y) if x and y else None
    controls=dict(PK_archive_byte_identity=equal_archives('P','K'),PK_authoritative_state=audit_equal('P','K','parent'),
        released_D_archive_byte_identity=equal_archives('D','release-D'),released_D_predictive_state=audit_equal('D','release-D'))
    p=rows['P']['artifacts'].get('archive');pa=audits['P'].get('encode')
    retained=read(ROOT/plan['parent_audit']['path']);retained=retained.get('parent',retained)
    controls['retained_P_archive_byte_identity']=(ROOT/p['path']).read_bytes()==(ROOT/plan['parent_archive']['path']).read_bytes() if p else None
    controls['retained_P_authoritative_state']=pa['parent']==retained if pa else None
    for arm in 'KDS':
        for field in ['parse_sha256','parse_events','updates_by_mode']:controls[arm+'_'+field]=audit_equal('P',arm,field)
    for arm in 'DS':
        for field in ['word_history_sha256','word_checkpoints','completed_words_hex','modeled_field']:controls[arm+'_'+field]=audit_equal('K',arm,field)
    correctness=truth([r['exact_inverse'] for r in rows.values()]+[r['state_synchronization'] for r in rows.values()]+list(controls.values())+[not binding_errors])
    repeatability=truth(r['repeat_byte_identity'] for r in rows.values())
    observer=truth(rows[a]['observed_plain_identity'] for a in ['D','release-D'])
    correctness=truth([correctness,observer])
    resource_failure=any(guard['guards'].values()) or any(x['timeout'] or x['memory_stop'] or x['returncode'] in [-9,-24,-25,124,137] for x in failures)
    resource_complete=False
    resource=False  # Observed host ENOSPC fails this execution's resource gate.
    failures.append(dict(arm='K',phase='repeat',returncode=None,timeout=None,memory_stop=None,classification='host-storage-exhaustion',required_execution_record_missing=True))
    complete=stage.get('status')=='passed' and len(phases)==17 and not failures and not binding_errors
    # A completed experimental comparison remains measurable if release execution fails.
    parent_valid=truth([rows[a]['exact_inverse'] for a in 'PKD']+[rows[a]['state_synchronization'] for a in 'PKD']+[v for k,v in controls.items() if not k.startswith(('released_','S_'))])
    delayed_valid=truth([rows[a]['exact_inverse'] for a in 'PKDS']+[rows[a]['state_synchronization'] for a in 'PKDS']+[v for k,v in controls.items() if not k.startswith('released_')])
    experimental=truth([parent_valid,delayed_valid])
    g_p=rows['P']['archive_bytes']-rows['D']['archive_bytes'] if parent_valid is True else None
    g_s=rows['S']['archive_bytes']-rows['D']['archive_bytes'] if delayed_valid is True else None
    summary=dict(schema='gamma.enwiki9.opcode-word-confirmation-terminal.v1',candidate_id=CID,job=ref(jobpath),guard=ref(gp),decision_policy=plan['decision_policy'],experiment=ref(ROOT/job['experiment']['path']),
        storage_reconciliation=ref(reconciliation_path),original_returncode=job["returncode"],execution_end_time=job["finished_at"],resource_evidence_complete=False,observed_resource_failure='host-storage-exhaustion (ENOSPC)',peaks_scope='Last retained nonterminal sample; final peaks unknown',
        population='[819000000, 820000000)',input=plan['input'],retained_parent_archive=plan['parent_archive'],retained_parent_audit=plan['parent_audit'],cold_initialization=True,prior_exposure='Previously exposed to other mechanisms; no previous-word tuning or sample switching.',
        execution_complete=complete,correctness_pass=correctness,repeatability_pass=repeatability,resource_gate_pass=resource,guard_schema=guard_schema,guard_measurements=guard['measurements'],guard_flags=guard['guards'],resource_peaks=guard['peaks'],elapsed_seconds=guard['elapsed_s'],phase_failures=failures,binding_errors=binding_errors,controls=controls,arms=rows,
        g_P=g_p,g_S=g_s,n_1=g_p-110 if g_p is not None else None,n_2=g_p-220 if g_p is not None else None,sensitivity_label='historical source-cost sensitivities',final_packaging_delta=None,
        comparison_validity=dict(parent=parent_valid,delayed=delayed_valid),
        measurement_scope='Completed comparisons only; release parity and repeatability remain separate dimensions',
        verdict=gate.decision(g_p,g_s,complete,correctness,repeatability,resource),complete_package_bytes=None,full_corpus_score_bytes=None,objective_credit_bytes=0)
    summary['retained_artifacts']=[ref(p) for p in sorted(directory.rglob('*')) if p.is_file()]
    summary['phases']=phases
    terminal=OUT.parent/(OUT.name+'.json');write(terminal,summary)
    index=dict(schema='gamma.enwiki9.partial-arm-evidence-index.v1',publication_limitation='Not eligible for terminal-index recording: original guard is nonterminal; ordinary diagnostic rows preserve partial observations only',job=ref(jobpath),guard=ref(gp),arms=[],evidence=[ref(terminal),plan['decision_policy']])
    for arm,row in rows.items():
        size=row['archive_bytes'];arts=row['artifacts'];res=row['phase_resources']
        result=dict(schema='gamma.enwiki9.driver-result.v2',arm=arm,program_id=CID,program_name='Cold 1MB previous-word '+arm,
            candidate_revision=dict(candidateId=CID,candidateTreeSha256=job['candidate_tree_sha256'],receipt=job['candidate_revision']),timestamp=job['finished_at'],artifacts=arts,
            nonterminal_guard_snapshot=ref(gp),source_terminal=ref(terminal),audit_files=row['audits'],compressed_size=size,compressed_sha256=arts.get('archive',{}).get('sha256'),data_size=1000000,data_path=plan['input']['path'],data_sha256=plan['input']['sha256'],data_md5=hashlib.md5(raw).hexdigest(),
            bits_per_byte=8*size/1000000 if size is not None else None,compress_time_s=res.get('encode',{}).get('elapsed_seconds'),decompress_time_s=res.get('decode',{}).get('elapsed_seconds'),phase_resources=res,
            roundtrip_ok=row['exact_inverse'],determinism=dict(scope='single-host',single_host_byte_equal=row['repeat_byte_identity']),shared_state_synchronization=row['state_synchronization'],
            run_context='Fixed cold [819000000, 820000000). Missing results remain unknown; refer to separate terminal dimensions.',run_purpose='diagnostic',run_scope_label='cold-1MB-previous-word-'+arm,run_source=str(jobpath.relative_to(ROOT)),run_tags=['previous-word','cold-1MB','diagnostic',arm],execution_mode='discovery',timing_authority='diagnostic',qualification_status='not-certified',resource_evidence_complete=False,discovery_resource_gate_pass=resource,score_accounting_complete=False,prize_claimable=False,complete_package_bytes=None,full_corpus_score_bytes=None,hutter_score=None,program_size=None,objective_credit_bytes=0,host=dict(hostname=platform.node()),missing_diagnostics=['Original guard returncode and continuous final resource evidence are missing; ENOSPC interrupted execution.'])
        if 'archive' in arts:result['compressed_md5']=hashlib.md5((ROOT/arts['archive']['path']).read_bytes()).hexdigest()
        path=OUT/(arm+'.json');write(path,result)
        index['arms'].append(dict(arm=arm,result=ref(path),artifacts=arts))
    write(OUT/'index.json',index)
    print(json.dumps({k:summary[k] for k in ['verdict','g_P','g_S','n_1','n_2','correctness_pass','repeatability_pass','resource_gate_pass']}))

if __name__=='__main__':main()
