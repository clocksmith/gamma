"""Metadata-only freeze preparation. Never load an encoder or numpy arrays."""
import hashlib,json
from pathlib import Path
from artifacts import pinned,sha,check_pin,first_queries,query_identity
from pipeline import POLICY
from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
UPSTREAM={'path':'/workspace/shared/gamma-description-enriched-freeze-20261025-2028/contract.json','sha256':'2ebc928b7d7c2228e0db8e6ee3593503e381d4e79844475c6e2e9995f111ffaa'}
RESULT={'path':'/workspace/shared/gamma-description-enriched-results-20261025-2039/development.json','sha256':'5c7a3c211f7fade8daf6a993b09c0510d9b4732c2cf4397c20efee2af853a42f'}
PLAN={'path':'/workspace/shared/gamma-recognition-documents-v2-20261025-2025b/plan.json','sha256':'950fcbe6cce0a7c3aad8ae93dcd792c3ac7aa8514688be5f0758bf19ff733ca8'}

def spec(path,digest=None):return {'path':str(path),'sha256':digest or sha(path)}
def freeze():
    f=pinned(UPSTREAM);completed=pinned(RESULT)
    if completed['freeze_sha256']!=UPSTREAM['sha256'] or completed['selected_policy']!=POLICY:raise ValueError('fixed selected policy provenance')
    policy=pinned(f['policy'])
    if len(policy['policy_family'])!=20 or POLICY not in policy['policy_family']:raise ValueError('original20 policies changed')
    plan=pinned(PLAN);gate=pinned(plan['boundary_gate'])
    for row in plan['authorities']:
        authorize_before_open(row['problem_id'],gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
    docs=pinned(f['documents']);old=pinned(f['baseline'])['documents'];new=docs['documents'];ids=[r['problem_id'] for r in new]
    if len(ids)!=4081 or len(set(ids))!=4081 or [r['problem_id'] for r in old]!=ids:raise ValueError('complete stable population')
    replacements=[i for i in range(4081) if old[i]['text']!=new[i]['text']]
    if len(replacements)!=54 or {ids[i] for i in replacements}!={r['problem_id'] for r in plan['authorities']}:raise ValueError('exact permitted54 changes')
    identity=pinned(f['baseline_identity'])
    if identity!=f['encoder_cache_identity']:raise ValueError('encoder cache identity drift')
    phase1=pinned(f['phase1']);chunks=[]
    for row in phase1['chunks']:
        start=row['start'];root=Path(f['baseline_cache'])
        receipt=spec(root/f'{start:04d}.json',row['receipt_sha256']);array=spec(root/f'{start:04d}.npy',row['array_sha256'])
        pinned(receipt);check_pin(array);chunks.append({'start':start,'receipt':receipt,'array':array})
    deltas=[];delta_root=Path(RESULT['path']).parent/'documents-cache'
    for start in range(0,54,4):
        receipt=spec(delta_root/f'{start:04d}.json');info=pinned(receipt)
        batch=[new[i] for i in replacements[start:start+4]]
        binding=hashlib.sha256(json.dumps({'identity':identity,'query':False,'rows':batch},sort_keys=True).encode()).hexdigest()
        if info['binding_sha256']!=binding or info['ids']!=[r['problem_id'] for r in batch]:raise ValueError('delta receipt binding')
        array=spec(delta_root/f'{start:04d}.npy',info['array_sha256']);check_pin(array)
        deltas.append({'start':start,'receipt':receipt,'array':array,'binding_sha256':binding})
    dependencies={name:sha(BASE/name) for name in ('cpu_encoder.py','provision_encoder.py','empirical_recognition.py','known_spec_service.py','materialize.py','catalogue.py','retrieval.py','boundary_policy.py')}
    for name,value in dependencies.items():
        if value!=f['code_sha256'][name]:raise ValueError('upstream dependency drift: '+name)
    return {'schema':'gamma.persistent-recognition-timing-freeze.v1','approval':'pending independent main review; preparation is not launch authorization',
        'predecessor_freeze':spec(HERE/'source-ada6c1c84cca/freeze.json','ada6c1c84cca0eaf55ba91e30c359626054e886f54632c111e48cf7208ef5de8'),
        'successor_reason':'Handled SIGTERM/SIGHUP/SIGINT with restored handlers, flag-only launch-race-safe signals, observed nonexecuting process group after cleanup; predecessor proposals remain unrun and preserved.',
        'upstream':UPSTREAM,'completed_development_result':RESULT,'documents':f['documents'],'documents_plan':PLAN,
        'development':f['development'],'query_selection':query_identity(first_queries(f['development'])),
        'selection_rule':'positions0..3 existing development order; identity/text only; no labels/outcomes',
        'policy':POLICY,'passes':2,'description_requests':8,'exact_ids':['leetcode:802','leetcode:875','leetcode:2406'],
        'exact_id_requests':6,'candidate_executions':0,'confirmation_read':False,'query_vector_cache':False,
        'service':f['service'],'encoder_cache_identity':identity,
        'encoder_manifest':spec(BASE/'ENCODER-PROVISIONING-PROPOSAL-v1.json',identity['encoder_manifest_sha256']),
        'cpu_manifest':spec(BASE/'CPU-ENVIRONMENT-PROPOSAL-v1.json',identity['cpu_manifest_sha256']),
        'model_root':'/workspace/shared/gamma-encoder-runtime-20261025/model',
        'python':'/workspace/shared/gamma-encoder-runtime-20261025/venv/bin/python',
        'stable_ids':ids,'replacement_positions':replacements,'baseline_chunks':chunks,'delta_chunks':deltas,
        'dependency_code_sha256':dependencies,
        'code_sha256':{name:sha(HERE/name) for name in ('pipeline.py','artifacts.py','prepare.py','run.py','launch.py','test_pipeline.py')},
        'resources':f['resources'],'recognition_qualified':False,'goal_1c_qualified':False,
        'prior_recognition_evidence':'Unqualified selected policy9/40; diagnostic latency does not promote.',
        'cache_state':'cold process; OS/page cache uncontrolled; persistent model/service/index; fresh encode per request'}

if __name__=='__main__':
    value=freeze();target=HERE/'freeze.json'
    with target.open('x') as stream:stream.write(json.dumps(value,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'freeze':str(target),'sha256':sha(target),'description_requests':8,'exact_id_requests':6,'launched':False}))
