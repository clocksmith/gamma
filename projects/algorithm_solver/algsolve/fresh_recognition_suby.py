"""One sealed fresh-query validation of the unchanged bounded recognition route.

No fresh cases exist until isolated author/reviewer work is authorized. freeze
hashes files without inspecting query/private content; run opens only that seal.
"""
import argparse
import json
import os
import re
from pathlib import Path
import time

from .records import LANE_ROOT
from .rebuild_recognition import Monitor,publish,bound_receipt,sha,digest

NAME='recognition-fresh-suby-v1'
OUTPUT=LANE_ROOT/'runs'/NAME
CONTROL=LANE_ROOT/'runs/recognition-rebuild-dev-suby-v1'
ASSET=LANE_ROOT/'data/reconstruction/recognition-rebuild-dev-suby-v1'
ROUTE=LANE_ROOT/'findings/recognition-requirements-dev-suby-v1/candidate.json'
CONTRACT=LANE_ROOT/'contracts/recognition_fresh_suby_v1.json'


def load(p):return json.loads(p.read_text())


def public_request(case):
    from .recognition_release import public_problem
    required={'id','kind','query','public_examples'}
    if not required<=set(case) or set(case)-required-{'output_comparison'}:
        raise ValueError('Fresh public case has missing or non-public fields')
    if not isinstance(case['id'],str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,64}',case['id']):raise ValueError('Invalid fresh case identifier')
    if case['kind'] not in ('paraphrase','sibling_variant','complete_description','ambiguous_description'):raise ValueError('Unknown fresh query kind')
    if not case['public_examples']:raise ValueError('Accepted fresh cases need initial public examples')
    return public_problem(case)


def retrieval_evidence(result, expected):
    selected=result.get('match',{}).get('candidates',[])
    raw=result.get('requirement_filter',{}).get('raw_retrieval',selected)
    return {'retrieval_executed':bool(raw),
            'top_five':expected is not None and expected in [c['key'] for c in raw[:5]],
            'post_filter_top_five':expected is not None and expected in [c['key'] for c in selected[:5]]}


def verify_review_seal(directory):
    seal=load(directory/'seal.json')
    if not seal.get('author_agent') or not seal.get('reviewer_agent') or seal['author_agent']==seal['reviewer_agent']:
        raise ValueError('Distinct isolated author/reviewer provenance required')
    for name in ('public.json','private.json','dispositions.json','authored.json'):
        if sha(directory/name)!=seal['files_sha256'].get(name):raise ValueError('Fresh review seal changed: '+name)
    for name in ('author_catalog.json','reviewer_sources.json'):
        if sha(directory/name)!=seal['catalog_sha256'].get(name):raise ValueError('Fresh author/reviewer input changed')
    return seal


def freeze():
    import importlib.metadata,sys
    route=load(ROUTE);protocol=load(CONTRACT)
    if sha(ROUTE)!=protocol['route_candidate_sha256']:raise ValueError('Recognition route candidate changed')
    # Additional composition/evaluation modules do not alter the frozen serving
    # files. Every file originally bound to this candidate must remain identical.
    for relative,h in route['sources_sha256'].items():
        if sha(LANE_ROOT/relative)!=h:raise ValueError('Original serving/contract source changed: '+relative)
    for relative,spec in route['control_snapshot'].items():
        path=CONTROL/relative
        if sha(path)!=spec['sha256'] or path.stat().st_mtime_ns!=spec['mtime_ns']:
            raise ValueError('Original reconstruction changed: '+relative)
    seal=verify_review_seal(OUTPUT) # Metadata/hashes only, no query/private parse.
    if seal.get('route_candidate_sha256')!=protocol['route_candidate_sha256'] or seal['catalog_sha256']!=protocol['prepared_catalog_sha256']:
        raise ValueError('Reviewed route/catalog identity differs from protocol')
    bound=[OUTPUT/n for n in ('seal.json','public.json','private.json','dispositions.json','authored.json')]
    from .rebuild_download import FILES,verify
    candidate={'schema':'algsolve.recognition-fresh-suby-candidate.v1','name':NAME,'route_candidate_sha256':sha(ROUTE),
        'protocol_sha256':sha(CONTRACT),'review_seal_sha256':sha(OUTPUT/'seal.json'),
        'data_sha256':{p.name:sha(p) for p in bound},'original_serving_sources_sha256':route['sources_sha256'],
        'evaluator_sources_sha256':{str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')},
        'payloads':{n:verify(ASSET/n,s) for n,s in FILES.items()},
        'dependencies':{n:importlib.metadata.version(n) for n in ('torch','transformers','numpy')},'python':sys.executable,
        'release_gate_changed':False,'scope':protocol['scope'],'protected_composition_opened':False}
    publish(OUTPUT/'candidate.json',candidate);return candidate


def run(monitor):
    candidate=freeze();candidate_hash=sha(OUTPUT/'candidate.json')
    if (OUTPUT/'summary.json').exists():
        summary=load(OUTPUT/'summary.json')
        if any(sha(OUTPUT/n)!=h for n,h in summary['artifacts_sha256'].items()):raise ValueError('Completed fresh evaluation drift')
        print(json.dumps({'completed_resume':True,'candidate_sha256':candidate_hash}));return
    import numpy as np
    import torch
    from .approved_library import ApprovedLibrary
    from .lookup import LookupIndex
    from .routes import Budget,Context
    from .splits import IndexEntry
    from .clarify import load_profiles
    from .requirement_filter import RequirementFilter,answer_with_policy
    from .embed import Embedder
    torch.set_num_threads(4);torch.set_num_interop_threads(1)
    if not torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.)):raise ValueError('CPU probe failed')
    started=time.perf_counter();entries=[IndexEntry(**e) for e in load(CONTROL/'qualified-entries.json')]
    lookup=LookupIndex(entries,np.stack([np.load(CONTROL/f'embeddings/{i:04d}.npy',allow_pickle=False) for i in range(len(entries))]))
    approved=ApprovedLibrary.load(CONTROL/'approved-library.json');approved.verify_runtime(LANE_ROOT)
    class MeasuredEncoder:
        def __init__(self):self.encoder=None;self.loads=[]
        def encode(self,*a,**kw):
            if self.encoder is None:
                start=time.perf_counter();self.encoder=Embedder(device='cpu');self.loads.append(time.perf_counter()-start)
            return self.encoder.encode(*a,**kw)
    encoder=MeasuredEncoder()
    context=Context(generator=None,embedder=encoder,lookup=lookup,thresholds=load(LANE_ROOT/'contracts/lookup_thresholds.json'),
        classifier=None,entries=entries,budget=Budget.from_contract(load(LANE_ROOT/'contracts/run_contract.json')))
    context.statement_thresholds=load(LANE_ROOT/'contracts/statement_lookup_thresholds.json');policy=RequirementFilter(load_profiles()['profiles'])
    opening={'candidate_sha256':candidate_hash,'context_setup_seconds':time.perf_counter()-started,'index_vectors_cached':True}
    if (OUTPUT/'opening.json').exists():
        if load(OUTPUT/'opening.json')['candidate_sha256']!=candidate_hash:raise ValueError('Opening candidate drift')
    else:publish(OUTPUT/'opening.json',opening)
    public=load(OUTPUT/'public.json');dispositions=load(OUTPUT/'dispositions.json')
    if len(dispositions)!=sum(load(CONTRACT)['planned_population'].values()):raise ValueError('Planned disposition denominator differs')
    from collections import Counter
    expected_counts={k.split('_',1)[1]:v for k,v in load(CONTRACT)['planned_population'].items()}
    if Counter(d['kind'] for d in dispositions)!=expected_counts:raise ValueError('Reviewed query-kind population differs')
    if any(d['status'] not in ('accepted','rejected') for d in dispositions):raise ValueError('Invalid review disposition')
    ids=[d['id'] for d in dispositions]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate case identities')
    if set(public)!={d['id'] for d in dispositions if d['status']=='accepted'}:raise ValueError('Reviewed public population differs')
    response_dir=OUTPUT/'responses';response_dir.mkdir(exist_ok=True);responses={}
    for d in dispositions:
        if d['status']=='rejected':continue
        case=public[d['id']]
        if case['id']!=d['id'] or case['kind']!=d['kind']:raise ValueError('Public/disposition identity mismatch')
        query=public_request(case)
        binding={'candidate_sha256':candidate_hash,'public_case_sha256':digest(case)}
        def decide():
            before=len(encoder.loads);result=answer_with_policy(context,query,approved,policy)
            return {'result':result,'cold_encoder_load_seconds':sum(encoder.loads[before:])}
        result=bound_receipt(response_dir/(d['id']+'.json'),binding,decide);responses[d['id']]=result
        print(json.dumps({'decided':d['id'],'decision':result['result']['decision'],'reason':result['result'].get('reason'),**monitor.counters()}),flush=True)
    publish(OUTPUT/'decisions-seal.json',{'candidate_sha256':candidate_hash,'responses_sha256':{p.name:sha(p) for p in response_dir.glob('*.json')}})
    # Private contents become available only after every public decision is sealed.
    private=load(OUTPUT/'private.json');scoring=OUTPUT/'scoring';scoring.mkdir(exist_ok=True);rows=[]
    if set(private)!=set(public):raise ValueError('Private/public reviewed identities differ')
    from . import validate
    from .recognition_release import declared_examples
    for d in dispositions:
        if d['status']=='rejected':
            rows.append({'id':d['id'],'kind':d['kind'],'review_status':'rejected','reason':d['reason']});continue
        key=d['id'];case=public[key];authority=private[key];response=responses[key]
        binding={'decisions_seal_sha256':sha(OUTPUT/'decisions-seal.json'),'authority_sha256':digest(authority),'response_sha256':digest(response)}
        def score():
            r=response['result'];accepted=r['decision']=='answered';expected=authority['expected_key_or_null'];verdict=None
            if expected is not None and expected not in approved.manifest['approved']:raise ValueError('Reviewed target is outside qualified bounded sources')
            ambiguous=case['kind']=='ambiguous_description'
            if ambiguous!=(expected is None):raise ValueError('Reviewed ambiguity/target contract differs')
            if accepted and expected is not None and authority['private_checks']:
                q=public_request(case);q.entry=r['answer_interface']
                verdict=validate.judge_problem(q,r['code'],declared_examples(dict(case,private_checks=authority['private_checks']),'private_checks')).to_dict()
            unknown=bool(accepted and expected is not None and (not verdict or verdict['reason'] in ('sandbox_error','checker_error','no_tests')))
            identity=expected is not None and r.get('match',{}).get('key')==expected
            return {'id':key,'kind':case['kind'],'review_status':'accepted','family':authority['family'],'difficulty':authority['difficulty'],
               'accepted':accepted,'accepted_and_correct':bool(accepted and identity and not unknown and verdict['passed']),
               'wrong_acceptance':bool(accepted and (not identity or (verdict and not unknown and not verdict['passed']))),
               'accepted_unqualified':unknown,'identity_correct':identity,'independent':verdict,'reason':r.get('reason'),
               'questions':0,'cold_encoder_load_seconds':response['cold_encoder_load_seconds'],'complete_route_seconds':r['seconds'],
               'loaded_route_seconds':max(0.,r['seconds']-response['cold_encoder_load_seconds']),
               **retrieval_evidence(r,expected)}
        rows.append(bound_receipt(scoring/(key+'.json'),binding,score))
    current={str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')}
    if current!=candidate['evaluator_sources_sha256']:raise ValueError('Fresh evaluator source drift')
    result={'schema':'algsolve.recognition-fresh-suby-summary.v1','name':NAME,'candidate_sha256':candidate_hash,
        'planned':len(dispositions),'review_rejected':sum(r['review_status']=='rejected' for r in rows),'rows':rows,
        'release_qualified':False,'protected_composition_opened':False,'resource_counters':monitor.counters(),
        'limitations':[load(CONTRACT)['population_limits'],load(CONTRACT)['acceptance'],'Fresh queries on familiar families; not arbitrary unseen solving or human evidence.']}
    def metrics(rs):
        ts=[r['loaded_route_seconds'] for r in rs]
        return {'executed':len(rs),'correct':sum(r['accepted_and_correct'] for r in rs),'wrong':sum(r['wrong_acceptance'] for r in rs),
            'unqualified':sum(r['accepted_unqualified'] for r in rs),'abstentions':sum(not r['accepted'] for r in rs),
            'questions':sum(r['questions'] for r in rs),'loaded_p50_seconds':float(np.percentile(ts,50)) if ts else None,
            'loaded_p95_seconds':float(np.percentile(ts,95)) if ts else None,'cold_encoder_load_seconds':sum(r['cold_encoder_load_seconds'] for r in rs)}
    executed=[r for r in rows if r['review_status']=='accepted'];result['overall']=metrics(executed)
    result['correct_accepted_per_planned_case']=sum(r['accepted_and_correct'] for r in executed)/len(dispositions)
    result['ambiguous_required_abstentions']=sum(r['kind']=='ambiguous_description' and not r['accepted'] for r in executed)
    from .recognition_metrics import summarize_results
    result['uncertainty']=summarize_results([dict(r,result={'seconds':r['loaded_route_seconds']}) for r in executed])
    result['by_kind']={kind:metrics([r for r in executed if r['kind']==kind]) for kind in sorted({r['kind'] for r in executed})}
    result['artifacts_sha256']={str(p.relative_to(OUTPUT)):sha(p) for p in OUTPUT.rglob('*') if p.is_file() and p.name!='lock' and 'failures' not in p.parts}
    publish(OUTPUT/'summary.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('rows','artifacts_sha256')},indent=2),flush=True)


def main():
    import fcntl
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['freeze','run']);args=parser.parse_args()
    os.environ['ALGSOLVE_EMBEDDING_DIR']=str(ASSET/'encoder');os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    OUTPUT.mkdir(exist_ok=True);lock=(OUTPUT/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if args.action=='freeze':freeze();print(json.dumps({'frozen_candidate_sha256':sha(OUTPUT/'candidate.json'),'opened':False}));return
    monitor=Monitor([ASSET,LANE_ROOT/'runs']);monitor.start()
    print(f'[run-contract] run_name={NAME} pairs_input_spec=sealed-reviewed-fresh-query-validation resume_from=atomic-receipts resume_stage=existing decode=none eval_dataset_paths=fresh-bounded-recognition device=cpu schedule=serial runtime_mode=reviewed-linux-sandbox sweep_mode=none',flush=True)
    try:run(monitor)
    except BaseException as error:
        d=OUTPUT/'failures';d.mkdir(exist_ok=True);publish(d/f'{time.time_ns()}.json',{'type':type(error).__name__,'detail':str(error),'resources':monitor.counters()});raise
    finally:monitor.stop.set()

if __name__=='__main__':main()
