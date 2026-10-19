"""Frozen nine-case named-output development comparison; existing catalog immutable."""
import argparse
import json
from pathlib import Path
import signal
import time
import numpy as np
from algsolve import corpus,library_audit as audit
from algsolve.answer import answer
from algsolve.approved_library import ApprovedLibrary,code_hash,entry_hash,selected_reference
from algsolve.catalog_refresh import query_for
from algsolve.lookup import LookupIndex,load_thresholds
from algsolve.named_output_contracts import bind,declared
from algsolve.qualification_environment import capture,verify
from algsolve.records import DERIVED,LANE_ROOT
from algsolve.routes import Context,Budget

REPORT=Path(__file__).parent
OUT=LANE_ROOT/'runs/known-named-output-1a-128-v1'
CATALOG=LANE_ROOT/'findings/known-catalog-refresh-128-v1/approved-library.json'
INVENTORY=LANE_ROOT/'runs/catalog-refresh-128-v4/inventory.jsonl'
KEYS=['lc:'+name for name in ['closest-divisors','delete-duplicate-folders-in-system','high-access-employees',
    'linked-list-frequency','maximum-number-of-non-overlapping-substrings','maximum-split-of-positive-even-integers',
    'modify-graph-edge-weights','two-out-of-three','word-break-ii']]


def inputs():
    raw,entries,problems,boundary=audit.inputs()
    bykey={e.key:e for e in entries};assert len(KEYS)==len(set(KEYS))==9 and set(KEYS)<=set(bykey)
    return raw,entries,problems,boundary,[bykey[k] for k in KEYS]


def freeze():
    raw,entries,problems,boundary,selected=inputs()
    catalog=ApprovedLibrary.load(CATALOG);catalog.verify_runtime(LANE_ROOT)
    inventory={r['key']:r for r in audit.rows(INVENTORY)}
    files={name:audit.sha(LANE_ROOT/name) for name in catalog.manifest['runtime_files_sha256']}
    extra=[Path(__file__),CATALOG,INVENTORY,DERIVED/'problems.jsonl',DERIVED/'near_duplicates.json',
        LANE_ROOT/'contracts/typed_confirmation_v1.json',LANE_ROOT/'contracts/recognition_qualification_v1.json']
    extra += [LANE_ROOT/'algsolve'/name for name in ['named_output_contracts.py','catalog_refresh.py','imported_examples.py','library_audit.py','recognition_boundary.py']]
    files.update({str(p.relative_to(LANE_ROOT)):audit.sha(p) for p in extra})
    cases=[];testfiles={}
    for entry in selected:
        assert catalog.manifest['excluded'][entry.key]=='exact_answer_path_not_qualified'
        q,_=query_for(entry,problems);c=bind(q)
        for testset in inventory[entry.key]['independent_test_sets']:
            p=Path(testset['path']);p=p if p.is_absolute() else DERIVED/p
            testfiles[str(p.relative_to(DERIVED))]=audit.sha(p)
        cases.append({'key':entry.key,'entry_sha256':entry_hash(entry),'code_sha256':code_hash(selected_reference(entry)['code']),
            'control_query_sha256':audit.digest(json.loads(q.to_json())),'candidate_query_sha256':audit.digest(json.loads(c.to_json())),
            'declared':declared(q.statement),'contract_applied':c.public_tests!=q.public_tests,'public_examples':len(q.public_tests)})
    contract={'schema':'algsolve.named-output-development.v1','population':'all nine named-output candidates fixed in previous catalog report; no dropped cases',
        'keys':KEYS,'inventory':len(raw),'eligible':len(entries),'protected_present':len(raw)-len(entries),
        'boundary_sha256':audit.digest(boundary),'files_sha256':files,'tests_sha256':testfiles,'cases':cases,
        'runtime_environment':capture(),'budget':{'threads':2,'memory_bytes':2*1024**3,'wall_seconds':180,'route_seconds':120,'public_judge_seconds':30,'independent_seconds':30},
        'selection_policy':'query wording only; complete unconditional clauses; preserve explicit comparison, data, inner order and multiplicity',
        'control':'current exact query with public_output_contracts=True, no source catalog exclusion to measure public path',
        'candidate':'same control plus standalone named_output_contracts.bind before answer',
        'scoring':'seal all18 public decisions before fresh independent checks of every selected reference, including public abstentions',
        'threshold':'positive useful answers; zero wrong or harmful changes','timing':'contended shared host; no latency promotion',
        'catalog_policy':'no approval refresh or serving changes; successful candidate is development evidence only','model':False}
    OUT.mkdir(exist_ok=False);audit.write(OUT/'contract.json',contract)
    print(json.dumps({'cases':cases,'frozen':True},indent=2))


def check(contract):
    for p,h in contract['files_sha256'].items():assert audit.sha(LANE_ROOT/p)==h,p
    verify(contract['runtime_environment'])


def run():
    signal.alarm(180);start=time.monotonic();contract=json.loads((OUT/'contract.json').read_text());check(contract)
    _,entries,problems,boundary,selected=inputs();assert audit.digest(boundary)==contract['boundary_sha256']
    assert not (OUT/'decisions.json').exists()
    inventory={r['key']:r for r in audit.rows(INVENTORY)}
    class NoEmbedding:
        def encode(self,*args,**kwargs):raise AssertionError('Exact comparison requested model inference')
    keys=json.loads(corpus.KEYS_PATH.read_text());allowed={e.key for e in entries};indices=[i for i,k in enumerate(keys) if k in allowed]
    ctx=Context(generator=None,embedder=NoEmbedding(),lookup=LookupIndex(entries,np.load(corpus.EMBEDDINGS_PATH)[indices]),
        thresholds=load_thresholds(),classifier=None,entries=entries,budget=Budget.from_contract(json.loads((LANE_ROOT/'contracts/run_contract.json').read_text())))
    decisions=[]
    for entry,case in zip(selected,contract['cases']):
        q,_=query_for(entry,problems)
        for arm,query in [('control',q),('candidate',bind(q))]:
            assert audit.digest(json.loads(query.to_json()))==case[arm+'_query_sha256']
            result=answer(ctx,query,public_output_contracts=True)
            decisions.append({'key':entry.key,'arm':arm,'result':result})
        print('[public]',entry.key,[r['result']['decision'] for r in decisions[-2:]],flush=True)
    audit.write(OUT/'decisions.json',decisions)
    audit.write(OUT/'decisions-seal.json',{'sha256':audit.sha(OUT/'decisions.json'),'count':18})
    check(contract)
    # Independent expected values are first decoded here, after all decisions.
    for path,sha in contract['tests_sha256'].items():assert audit.sha(DERIVED/path)==sha,path
    stored={e.key:audit.independent_score(e,selected_reference(e)['code'],problems,inventory[e.key]) for e in selected}
    bykey={e.key:e for e in selected};scores=[]
    for row in decisions:
        e=bykey[row['key']];result=row['result'];code=result.get('code');reference=selected_reference(e)['code']
        scored=stored[e.key] if code==reference else audit.independent_score(e,code,problems,inventory[e.key])
        identity=(result.get('match') or {}).get('key')==e.key
        scores.append({'key':e.key,'arm':row['arm'],'decision':result['decision'],'reason':result.get('reason'),
            'correct':result['decision']=='answered' and identity and scored['status']=='passed',
            'wrong':result['decision']=='answered' and (not identity or scored['status']=='failed'),
            'unqualified':result['decision']=='answered' and scored['status'] not in ('passed','failed'),
            'public_examples':result['public_example_count'],'public_tests_passed':sum((a.get('public') or {}).get('tests_passed',0) for a in result.get('attempts',[])),
            'independent':scored,'code_sha256':code_hash(code) if code else None})
    audit.write(OUT/'stored-scores.json',stored);audit.write(OUT/'scores.json',scores)
    arms={arm:{'cases':9,'correct':sum(r['correct'] for r in scores if r['arm']==arm),
               'wrong':sum(r['wrong'] for r in scores if r['arm']==arm),'unqualified':sum(r['unqualified'] for r in scores if r['arm']==arm),
               'abstain':sum(r['decision']=='abstain' for r in scores if r['arm']==arm)} for arm in ('control','candidate')}
    paired={key:{r['arm']:r for r in scores if r['key']==key} for key in KEYS}
    useful=[k for k,p in paired.items() if p['candidate']['correct'] and not p['control']['correct']]
    harmful=[k for k,p in paired.items() if p['control']['correct'] and not p['candidate']['correct']]
    check(contract)
    summary={'arms':arms,'useful':useful,'harmful':harmful,'rows':scores,'stored_references_passed':sum(s['status']=='passed' for s in stored.values()),
        'fresh_stored_independent_tests_passed':sum(v['tests_passed'] for s in stored.values() for v in s['verdicts']),
        'useful_independent_tests_passed':sum(v['tests_passed'] for key in useful for v in stored[key]['verdicts']),
        'catalog_changed':False,'catalog_approved':2481,'protected_scored':False,'runtime_unchanged':True,
        'model_loaded':False,'generation':False,'wall_seconds':time.monotonic()-start,'timing':'contended','release_promoted':False}
    audit.write(OUT/'summary.json',summary)
    for name in ['contract.json','decisions-seal.json','stored-scores.json','summary.json']:(REPORT/name).write_bytes((OUT/name).read_bytes())
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'},indent=2),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['freeze','run']);args=parser.parse_args()
    {'freeze':freeze,'run':run}[args.action]()
