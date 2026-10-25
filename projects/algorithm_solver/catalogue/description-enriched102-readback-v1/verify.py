"""Independent readback: bytes, cache shape, aggregate arithmetic and recorded cleanup.
Does not attest clocks, encoder execution, semantic truth or unseen generalization.
"""
import argparse,hashlib,json,math
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def check_metrics(m):
    assert m['positive_count']==40 and m['control_count']==12
    assert all(type(v)is int and v>=0 for v in m.values())
    assert m['correct_accepts']+m['wrong_positive_accepts']<=40
    assert m['control_accepts']<=12
    assert m['abstentions']+m['correct_accepts']+m['wrong_positive_accepts']+m['control_accepts']==52

def check_cleanup(s):
    assert s['status']=='completed' and s['exit_code']==0 and not s['wall_timeout'] and s['error_type']is None
    c=s['owned_group_cleanup'];assert c['leader_reaped'] and c['no_executing_group_members_observed']
    assert c['live_members']==[] and c['inspection_unreadable_pids']==[]

def verify(root,freeze,freeze_sha):
    import numpy as np
    root=Path(root);f=load(freeze);r=load(root/'results/report.json');s=load(root/'supervisor.json')
    assert sha(freeze)==freeze_sha==r['freeze_sha256']==s['freeze_sha256'];check_cleanup(s)
    assert r['status']=='completed' and r['population']==4081 and r['query_count']==52 and r['policy_count']==20
    assert r['new_encode_document_count']==r['document_vector_count']==48 and r['query_encode_document_count']==0
    assert r['reused_vectors']=={'existing_authoritative':54,'remaining_title_only':3979,'queries':52}
    for k in ('source_availability_ranking_filter','confirmation_read','recognition_qualified'):assert r[k]is False
    assert r['candidate_source_reads']==r['candidate_executions']==0 and r['historical_baseline_reproduced']is True
    assert r['matched_service_sha256']==f['matched_service']['sha256'] and r['historical_service_sha256']==f['historical_service']['sha256']
    assert load(root/'results/progress.json')=={'phase':'completed','completed_documents':48}
    assert not (root/'results/failure.json').exists()
    assert 0<r['wall_seconds']<=s['wall_seconds']<245 and 0<r['cpu_seconds']<300 and 0<r['peak_rss_kib']<8*1024**2
    assert len(r['delta_receipts'])==len(f['delta_batches'])==12
    cache_hashes=[]
    for receipt,batch in zip(r['delta_receipts'],f['delta_batches']):
        assert {k:receipt[k]for k in ('start','ids','binding_sha256')}==batch
        name=f"{batch['start']:04d}";p=root/'results/documents-cache'/f'{name}.npy'
        assert load(p.with_suffix('.json'))==receipt and sha(p)==receipt['array_sha256']
        a=np.load(p,allow_pickle=False);assert a.shape==(4,1024) and a.dtype==np.float32 and np.isfinite(a).all()
        assert np.allclose(np.linalg.norm(a,axis=1),1,atol=1e-4)
        request=receipt['request'];assert request['query']is False and request['rows']==4 and request['truncated']==[False]*4
        cache_hashes.append(receipt['array_sha256'])
    rows=r['results'];assert len(rows)==20 and len({x['policy']['id']for x in rows})==20
    arms=('historical54_v8','baseline54_v16','expanded102_v16')
    for row in rows:
        for arm in arms:check_metrics(row[arm])
        for key,a,b in [('service_only_delta_v16_minus_v8',arms[0],arms[1]),('document_only_delta_102_minus_54_at_v16',arms[1],arms[2])]:
            assert row[key]=={k:row[b][k]-row[a][k]for k in row[a]}
        for arm in arms[1:]:
            ds=row[arm+'_decisions'];assert len(ds)==52 and len({d['query_id']for d in ds})==52
            assert all(d['status']in ('accepted','abstain')for d in ds)
            assert sum(d['status']=='abstain'for d in ds)==row[arm]['abstentions']
    for arm,p in r['selected_policies'].items():assert next(x for x in rows if x['policy']==p)[arm]['wrong_positive_accepts']==0
    return {'schema':'gamma.enriched102-independent-readback.v1','status':'passed','freeze_sha256':freeze_sha,'report_sha256':sha(root/'results/report.json'),'supervisor_sha256':sha(root/'supervisor.json'),'cache_array_sha256':cache_hashes,'all20_metric_arithmetic_checked':True,'all48_vector_shapes_hashes_norms_checked':True,'recorded_cleanup_checked':True,'clock_or_encoder_execution_attested':False,'semantic_correctness_independently_attested':False,'source_reads':0,'model_execution':False,'confirmation_read':False,'recognition_qualified':False}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--freeze',required=True);p.add_argument('--freeze-sha256',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=verify(a.root,a.freeze,a.freeze_sha256);Path(a.output).write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(result['status'])
