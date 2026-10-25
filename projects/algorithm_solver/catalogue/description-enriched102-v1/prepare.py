"""Freeze102-doc CPU successor only; no model/vector load or evaluation."""
import json
from pathlib import Path
from run import pinned,file_sha,load_document_pair,alignment,batch_binding
HERE=Path(__file__).resolve().parent;BASE=HERE.parent

def spec(path,digest=None):return {'path':str(Path(path).resolve()),'sha256':digest or file_sha(path)}
def prepare():
    upstream_spec=spec('/workspace/shared/gamma-description-enriched-freeze-20261025-2028/contract.json','2ebc928b7d7c2228e0db8e6ee3593503e381d4e79844475c6e2e9995f111ffaa');upstream=pinned(upstream_spec)
    cache_spec=spec(BASE/'description-applicability-evaluation-v2/freeze.json','63cc9a9a7adecab59bbc22611f1d834e484a2f640403a7873232b1a926a1558f');cache=pinned(cache_spec)
    f={'schema':'gamma.enriched102-cpu-freeze.v1','approval':'Prepared for independent main review; not permission to launch.',
       'upstream54_experiment':upstream_spec,'cache_plan':cache_spec,
       'old_document_plan':spec('/workspace/shared/gamma-recognition-documents-v2-20261025-2025b/plan.json','950fcbe6cce0a7c3aad8ae93dcd792c3ac7aa8514688be5f0758bf19ff733ca8'),
       'old_documents':upstream['documents'],
       'new_document_plan':spec('/workspace/shared/gamma-recognition-documents-102-v1-20261025-2146/plan.json','6ea599e726b2982f139d59450eb3db32e4c59abc9136248b294f26f1378f7bfb'),
       'new_documents':spec('/workspace/shared/gamma-recognition-documents-102-v1-20261025-2146/documents.json','702b551906239906725bc705a45242749f0a472e57874b70fa8fd8773918393f'),
       'encoder_cache_identity':upstream['encoder_cache_identity'],
       'cache_module':cache['cache_module'],'query_cache_module':spec(BASE/'description-applicability-evaluation-v2/evaluate.py',cache['code_sha256']['evaluate.py']),
       'development':upstream['development'],'policy':upstream['policy'],'historical_result':cache['historical_result'],
       'historical_service':upstream['service'],
       'matched_service':spec('/workspace/shared/gamma-known-spec-service-v16-20261025-2124/config.json','f5eeba3b017e804b353e47674c08377cced8e073bca4a997a3e6129f59ed192d'),
       'encoder_manifest':spec(BASE/'ENCODER-PROVISIONING-PROPOSAL-v1.json',upstream['encoder_cache_identity']['encoder_manifest_sha256']),
       'cpu_manifest':spec(BASE/'CPU-ENVIRONMENT-PROPOSAL-v1.json',upstream['encoder_cache_identity']['cpu_manifest_sha256']),
       'model_root':'/workspace/shared/gamma-encoder-runtime-20261025/model','python':'/workspace/shared/gamma-encoder-runtime-20261025/venv/bin/python',
       'new_encode_documents':48,'query_encode_documents':0,'expected_population':4081,'expected_policy_count':20,'expected_query_count':52,
       'resources':upstream['resources'],'confirmation_read':False,'candidate_execution':False,'source_availability_ranking_filter':False,
       'comparison_design':{'historical_reproduction':'54documents/v8service vs stored historicalv8 result',
          'service_effect':'54documents/v16service minus54documents/v8service',
          'document_effect':'102documents/v16service minus54documents/v16service',
          'threshold_family':'unchanged original20, separate existing selection criterion per arm','query_vectors':'same exact52cached vectors for all arms'},
       'recognition_qualified':False}
    if cache['index']['encoder_cache_identity']!=f['encoder_cache_identity']:raise ValueError('cache encoder identity')
    old,new=load_document_pair(f);positions=alignment(old,new);f['replacement_positions']=positions
    if cache['index']['stable_ids']!=old['stable_ids']:raise ValueError('cache/doc universe identity')
    f['delta_batches']=[]
    for start in range(0,48,4):
        rows=[new['documents'][i]for i in positions[start:start+4]]
        f['delta_batches'].append({'start':start,'ids':[r['problem_id']for r in rows],'binding_sha256':batch_binding(f['encoder_cache_identity'],f['new_documents']['sha256'],rows)})
    for name in ('cache_module','query_cache_module','encoder_manifest','cpu_manifest','historical_service','matched_service','policy','development','historical_result'):
        if file_sha(f[name]['path'])!=f[name]['sha256']:raise ValueError('dependency artifact drift: '+name)
    # Authenticate cache bytes without loading any numpy array or inspecting text.
    for chunk in cache['index']['baseline_chunks']+cache['index']['delta_chunks']+cache['query_chunks']:
        for name in ('receipt','array'):
            if file_sha(chunk[name]['path'])!=chunk[name]['sha256']:raise ValueError('cache bytes drift')
    f['dependency_code_sha256']={name:file_sha(BASE/name)for name in ('cpu_encoder.py','provision_encoder.py','empirical_recognition.py','known_spec_service.py','materialize.py','catalogue.py','retrieval.py','boundary_policy.py')}
    for name,pin in f['dependency_code_sha256'].items():
        if pin!=upstream['code_sha256'][name]:raise ValueError('original runtime dependency drift')
    f['code_sha256']={name:file_sha(HERE/name)for name in ('run.py','launch.py','prepare.py','test_run.py')}
    output=HERE/'freeze.json'
    with output.open('x')as stream:stream.write(json.dumps(f,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'freeze':str(output),'sha256':file_sha(output),'new_documents':48,'query_encodes':0,'launched':False}))
if __name__=='__main__':prepare()
