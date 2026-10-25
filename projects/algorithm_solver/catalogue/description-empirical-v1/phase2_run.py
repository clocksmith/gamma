"""Frozen authored-cohort calibration. Confirmation is a separate explicit stage."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import time

from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
from projects.algorithm_solver.catalogue.empirical_recognition import decide, rank, score_decisions, select_policy
from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pinned(path, digest):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=digest: raise ValueError('frozen input changed')
    return json.loads(raw)
def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,indent=2,sort_keys=True)+'\n');os.replace(temp,path)


def run(args):
    base=Path(__file__).parent; catalogue=base.parent
    freeze=pinned(base/'policy-freeze.json',args.freeze_sha256)
    execution=pinned(args.execution_freeze,args.execution_sha256)
    for path,digest in execution['code_sha256'].items():
        if sha(catalogue/path)!=digest:raise ValueError('execution code changed: '+path)
    if execution['policy_sha256']!=args.freeze_sha256:raise ValueError('policy/execution mismatch')
    index=pinned(args.index,freeze['index_sha256'])['documents']
    if len(index)!=4081 or len({r['problem_id'] for r in index})!=4081:raise ValueError('competitor universe changed')
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(180,185))
    import numpy as np
    service=KnownSpecService.from_config(args.service_config,execution['service_config_sha256'])
    encoder=PinnedCPUEncoder(args.model_root,encoder_manifest=catalogue/'ENCODER-PROVISIONING-PROPOSAL-v1.json',
        encoder_manifest_sha256=execution['encoder_manifest_sha256'],cpu_manifest=catalogue/'CPU-ENVIRONMENT-PROPOSAL-v1.json',
        cpu_manifest_sha256=execution['cpu_manifest_sha256'],native_python_sha256=execution['native_python_sha256'],threads=2,batch_size=4)
    output=Path(args.output);output.mkdir(exist_ok=True);cache=output/'cache';cache.mkdir(exist_ok=True)
    phase1=pinned(args.phase1_receipt,execution['phase1_receipt_sha256'])
    if phase1['exit_code']!=152 or phase1['index_completed']!=4081:raise ValueError('phase1 lineage mismatch')
    frozen_chunks={r['start']:r for r in phase1['chunks']}
    identity={'index_sha256':freeze['index_sha256'],'encoder_adapter_sha256':freeze['encoder_adapter_sha256'],
        'encoder_manifest_sha256':execution['encoder_manifest_sha256'],'cpu_manifest_sha256':execution['cpu_manifest_sha256'],
        'native_python_sha256':execution['native_python_sha256'],'threads':2,'batch_size':4}
    if (cache/'identity.json').exists():
        if json.loads((cache/'identity.json').read_text())!=identity:raise ValueError('cache identity mismatch')
    else:save(cache/'identity.json',identity)
    started=time.monotonic(); matrices=[]; chunks=[]
    for start in range(0,len(index),64):
        rows=index[start:start+64];path=cache/f'{start:04d}.npy';receipt=cache/f'{start:04d}.json'
        if path.exists() and receipt.exists():
            expected_chunk=frozen_chunks[start]
            if sha(receipt)!=expected_chunk['receipt_sha256'] or sha(path)!=expected_chunk['array_sha256']:raise ValueError('phase1 cache anchor changed')
            info=json.loads(receipt.read_text())
            if info['start']!=start or info['ids']!=[r['problem_id'] for r in rows] or sha(path)!=info['sha256']:
                raise ValueError('cached chunk identity mismatch')
            array=np.load(path,allow_pickle=False)
        else:
            raise ValueError('phase2 requires complete pinned phase1 cache; no index recomputation')
        if array.shape!=(len(rows),1024) or not np.isfinite(array).all() or not np.allclose(np.linalg.norm(array,axis=1),1,atol=1e-4):
            raise ValueError('invalid cached embeddings')
        matrices.append(array);chunks.append(info['sha256'])
        save(output/'progress.json',{'phase':'index','completed':start+len(rows),'total':4081,'elapsed_seconds':time.monotonic()-started})
    docs=np.concatenate(matrices)
    if args.stage=='development':
        queries=pinned(args.queries,freeze['development_sha256'])['queries'];policies=freeze['policy_family']
    else:
        selection=pinned(args.selection,args.selection_sha256)
        if selection['policy_freeze_sha256']!=args.freeze_sha256 or selection['selected_policy'] not in freeze['policy_family']:
            raise ValueError('confirmation selection not bound to frozen family')
        queries=pinned(args.queries,freeze['confirmation_sha256'])['queries'];policies=[selection['selected_policy']]
    vectors=encoder.encode([q['text'] for q in queries],query=True);request=encoder.last_request_info
    scores=vectors@docs.T;ids=[r['problem_id'] for r in index]
    rankings=[rank(s,ids) for s in scores]
    results=[]
    for policy in policies:
        decisions=[decide(r,policy,service,truncated=request['truncated'][i]) for i,r in enumerate(rankings)]
        results.append({'policy':policy,'metrics':score_decisions(queries,decisions),'decisions':decisions})
    selected=select_policy(results) if args.stage=='development' else policies[0]
    report={'schema':'gamma.authored-description-empirical-result.v1','stage':args.stage,'phase':2,'phase1_receipt_sha256':execution['phase1_receipt_sha256'],'resource_policy':{'cpu_seconds':180,'wall_seconds':240,'address_space_bytes':8*1024**3},'resumed_cache_not_cold_full_1c':True,'policy_freeze_sha256':args.freeze_sha256,
        'execution_freeze_sha256':args.execution_sha256,'selected_policy':selected,'results':results,
        'query_metadata':request,'index_chunks_sha256':chunks,'total_seconds':time.monotonic()-started,
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'population_risk_certificate':False,
        'sampling':'authored/non-IID; no all4081 generalization','source_reads':0,'protected_payload_reads':0,
        'qualification_scope':'finite authored cohort only; no semantic soundness or production release'}
    save(output/(args.stage+'.json'),report)
    if args.stage=='development':save(output/'selection.json',{'policy_freeze_sha256':args.freeze_sha256,
        'development_report_sha256':sha(output/'development.json'),'selected_policy':selected})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('freeze-sha256','execution-freeze','execution-sha256','index','service-config','model-root','output','queries','phase1-receipt'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--stage',choices=('development','confirmation'),required=True)
    p.add_argument('--selection');p.add_argument('--selection-sha256')
    run(p.parse_args())
