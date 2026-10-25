"""Metadata-only cached comparison freeze. No numpy/model/source/cohort scoring."""
import json
from pathlib import Path
from evaluate import sha,read,binding
HERE=Path(__file__).resolve().parent;BASE=HERE.parent

def spec(path,digest=None):return {'path':str(Path(path).resolve()),'sha256':digest or sha(path)}
def prepare():
    upstream=spec('/workspace/shared/gamma-description-enriched-freeze-20261025-2028/contract.json','2ebc928b7d7c2228e0db8e6ee3593503e381d4e79844475c6e2e9995f111ffaa');f=read(upstream)
    timing=spec(BASE/'persistent-recognition-timing-v1/freeze.json','a0ce32d58b0e4c22ac04626569c1a951eb0e10cc0e76575a51c8266a3eb8b256');indexfreeze=read(timing)
    guardfreeze=spec(BASE/'description-applicability-v2/freeze.json','4b534b02d22cbdedaa8f2ca8d50fa69e4fd9572f28b8189f64e95d3061cf5824');g=read(guardfreeze)
    rows=read(f['development'])['queries'];policies=read(f['policy'])['policy_family']
    if len(rows)!=52 or len(policies)!=20:raise ValueError('fixed cohort/policy denominator')
    identity=f['encoder_cache_identity']
    if identity!=indexfreeze['encoder_cache_identity']:raise ValueError('cache identity changed')
    chunks=[];root=Path('/workspace/shared/gamma-description-enriched-results-20261025-2039/queries-cache')
    for start in range(0,52,4):
        receipt=spec(root/f'{start:04d}.json');info=read(receipt)
        batch=[{'problem_id':q['query_id'],'text':q['text']} for q in rows[start:start+4]]
        expected=binding(identity,batch)
        if info['binding_sha256']!=expected or info['ids']!=[r['problem_id'] for r in batch]:raise ValueError('query cache identity drift')
        array=spec(root/f'{start:04d}.npy',info['array_sha256'])
        if sha(array['path'])!=array['sha256']:raise ValueError('query cache bytes drift')
        chunks.append({'start':start,'receipt':receipt,'array':array,'binding_sha256':expected})
    history=spec('/workspace/shared/gamma-description-enriched-results-20261025-2039/development.json','5c7a3c211f7fade8daf6a993b09c0510d9b4732c2cf4397c20efee2af853a42f')
    # Hash only here; baseline outcomes are consumed only by reviewed evaluation.
    if sha(history['path'])!=history['sha256']:raise ValueError('historical result changed')
    deps=set(g['dependency_code_sha256'])|{'known_spec_service.py','materialize.py','retrieval.py'}
    freeze={'schema':'gamma.cached-guard-development-freeze.v2','approval':'prepared only; main review required before execution',
        'upstream':upstream,'index_provenance':timing,'guard_freeze':guardfreeze,
        'guard_module':spec(BASE/'description-applicability-v2/guard.py',g['files']['guard.py']),
        'cache_module':spec(BASE/'persistent-recognition-timing-v1/artifacts.py',indexfreeze['code_sha256']['artifacts.py']),
        'index':{key:indexfreeze[key] for key in ('stable_ids','replacement_positions','baseline_chunks','delta_chunks','encoder_cache_identity')},
        'query_chunks':chunks,'development':f['development'],'policy':f['policy'],'service':f['service'],
        'document_plan':spec('/workspace/shared/gamma-recognition-documents-v2-20261025-2025b/plan.json','950fcbe6cce0a7c3aad8ae93dcd792c3ac7aa8514688be5f0758bf19ff733ca8'),
        'documents':f['documents'],'historical_result':history,
        'dependency_code_sha256':{name:sha(BASE/name) for name in sorted(deps)},
        'code_sha256':{name:sha(HERE/name) for name in ('evaluate.py','prepare.py','test_evaluate.py')},
        'policy_family_count':20,'population':4081,'development_queries':52,'grammar_changes':False,'new_policy_search':False,
        'encoder_invocations':0,'candidate_executions':0,'candidate_source_reads':0,'confirmation_read':False,
        'resources':{'address_space_bytes':512*1024**2,'cpu_hard_seconds':60,'wall_seconds':60},
        'baseline_comparison':'all historical status/identity/implementation selections and metrics must reproduce before guard conclusions',
        'recognition_qualified':False}
    target=HERE/'freeze.json'
    with target.open('x')as out:out.write(json.dumps(freeze,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'freeze':str(target),'sha256':sha(target),'evaluated':False}))
if __name__=='__main__':prepare()
