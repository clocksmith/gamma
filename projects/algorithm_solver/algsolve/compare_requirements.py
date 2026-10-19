"""Frozen, paired DEVELOPMENT comparison of contradiction-only recognition.

No downloads, fitting, protected inputs or source qualification expansion.
--freeze binds implementation and all inputs before --run can infer or judge.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import importlib.metadata
import json
import os
from pathlib import Path
import resource
import sys
import time

from .records import LANE_ROOT, Problem
from .rebuild_recognition import Monitor, bound_receipt, digest, publish, sha

NAME = 'recognition-requirements-dev-suby-v1'
CONTROL = LANE_ROOT/'runs/recognition-rebuild-dev-suby-v1'
OUTPUT = LANE_ROOT/'runs'/NAME
ASSET = LANE_ROOT/'data/reconstruction/recognition-rebuild-dev-suby-v1'
CONTROL_SHA = '64f10768b5004782cf8549215357d8d08ee2be8cd74b8b6198fe8c7ced83a33e'
CONTRACT = LANE_ROOT/'contracts/recognition_requirements_dev_suby_v1.json'


def load(path): return json.loads(path.read_text())


def snapshot(root):
    return {str(p.relative_to(root)): {'sha256': sha(p), 'mtime_ns': p.stat().st_mtime_ns}
            for p in sorted(root.rglob('*')) if p.is_file() and p.name != 'lock'}


def check_control(snapshot_value):
    if snapshot(CONTROL) != snapshot_value:
        raise ValueError('Original reconstruction control changed')


def source_hashes():
    paths = list((LANE_ROOT/'algsolve').rglob('*.py'))
    paths += [CONTRACT, LANE_ROOT/'contracts/clarification_profiles_v1.json']
    paths += [LANE_ROOT/'tests/test_requirement_filter.py', LANE_ROOT/'tests/test_requirement_comparison.py']
    return {str(p.relative_to(LANE_ROOT)): sha(p) for p in sorted(paths)}


def dependencies():
    if Path(sys.prefix) != LANE_ROOT.parents[1]/'.venv':
        raise ValueError('Use the approved repository .venv interpreter')
    return {'python_executable': sys.executable, 'python_version': sys.version,
            **{n: importlib.metadata.version(n) for n in ('torch','transformers','numpy')}}


def freeze():
    from .approved_library import ApprovedLibrary
    from .clarify import load_profiles
    from .rebuild_download import FILES, verify
    from .requirement_filter import RequirementFilter
    if sha(CONTROL/'candidate.json') != CONTROL_SHA: raise ValueError('Unexpected control candidate')
    summary = load(CONTROL/'summary.json')
    for path, h in summary['artifacts_sha256'].items():
        if sha(CONTROL/path) != h: raise ValueError('Control artifact changed: '+path)
    approved = ApprovedLibrary.load(CONTROL/'approved-library.json')
    approved.verify_runtime(LANE_ROOT)
    checks = load(OUTPUT/'checks.json')
    if checks.get('passed') is not True or checks.get('sources_sha256') != source_hashes():
        raise ValueError('Passing deterministic checks do not bind this candidate')
    catalog = load_profiles(); RequirementFilter(catalog['profiles'])
    entries = load(CONTROL/'qualified-entries.json'); fixtures = load(CONTROL/'fixtures.json')
    by_hash = {p['statement_sha256']:p for p in catalog['profiles']}
    import hashlib
    bindings = [{'key':e['key'], 'statement_sha256':hashlib.sha256(e['statement'].encode()).hexdigest()}
                for e in entries if hashlib.sha256(e['statement'].encode()).hexdigest() in by_hash]
    contract = load(CONTRACT)
    candidate = {'schema':'algsolve.requirements-paired-candidate.v1', 'name':NAME,
        'scope':'consumed development only; no new holdout/generalization/release evidence',
        'contract':contract, 'sources_sha256':source_hashes(), 'dependencies':dependencies(),
        'control_candidate_sha256':CONTROL_SHA, 'control_snapshot':snapshot(CONTROL),
        'payloads':{name:verify(ASSET/name,spec) for name,spec in FILES.items()},
        'entries':len(entries), 'requests':len(fixtures), 'source_profile_bindings':bindings,
        'source_profile_review':'Existing 22 bound source contracts inspected against permitted indexed statements before inference. Curated metadata, not semantic proof; no profiles added or changed.',
        'source_approval':'Reuse exactly the original 16-source qualification and all exclusions; unchanged answer/execution implementation verified against its manifest.',
        'deterministic_check_receipt_sha256':sha(OUTPUT/'checks.json')}
    if len(entries)!=66 or len(fixtures)!=24 or len(bindings)!=22: raise ValueError('Frozen cohort differs')
    publish(OUTPUT/'candidate.json',candidate)
    print(json.dumps({'frozen_candidate_sha256':sha(OUTPUT/'candidate.json'),'name':NAME,
                      'entries':66,'requests':24,'inference_started':False}),flush=True)


def verify_candidate():
    candidate = load(OUTPUT/'candidate.json')
    if candidate['sources_sha256'] != source_hashes() or candidate['dependencies'] != dependencies():
        raise ValueError('Frozen candidate code or dependencies changed')
    if candidate['deterministic_check_receipt_sha256'] != sha(OUTPUT/'checks.json'):
        raise ValueError('Deterministic check receipt changed')
    check_control(candidate['control_snapshot'])
    from .rebuild_download import FILES, verify
    if candidate['payloads'] != {n:verify(ASSET/n,s) for n,s in FILES.items()}:
        raise ValueError('Payload identity changed')
    return candidate


class SharedInputs:
    """Replay the same measured retrieval into both arms; not inference timing."""
    def __init__(self, lookup, text, vector, candidates):
        self.lookup, self.text, self.vector, self.candidates = lookup, text, vector, candidates
    def __getattr__(self,name): return getattr(self.lookup,name)
    def encode(self,texts,*,query=False):
        import numpy as np
        if texts != [self.text] or not query or self.vector is None:
            raise ValueError('Shared embedding request identity differs')
        return np.array([self.vector],copy=True)
    def scored_candidates(self,text,vector):
        import numpy as np
        if text != self.text or not np.array_equal(vector,self.vector):
            raise ValueError('Shared retrieval request identity differs')
        return copy.deepcopy(self.candidates)


def infra(result):
    return any(a.get('public',{}).get('reason') in ('sandbox_error','checker_error') for a in result.get('attempts',[]))


def score_pair_receipts(root, index, binding, score_arm):
    result={}
    for arm in ('control','candidate'):
        path=root/arm/f'{index:04d}.json';path.parent.mkdir(parents=True,exist_ok=True)
        result[arm]=bound_receipt(path,dict(binding,arm=arm),lambda:score_arm(arm))
    return result


def summarize(rows):
    import numpy as np
    def metrics(arm, group):
        rs=[r[arm] for r in group]; times=[r['charged_route_seconds'] for r in rs]
        return {'requests':len(rs),'accepted_correct':sum(r['correct'] for r in rs),
                'accepted':sum(r['accepted'] for r in rs),'wrong_accepted':sum(r['wrong'] for r in rs),
                'unqualified_accepted':sum(r['unqualified'] for r in rs),
                'abstentions':sum(not r['accepted'] for r in rs),'infrastructure_errors':sum(r['infrastructure_error'] for r in rs),
                'p50_charged_route_seconds':float(np.percentile(times,50)),
                'p95_charged_route_seconds':float(np.percentile(times,95)), 'max_charged_route_seconds':max(times)}
    specified=[r for r in rows if r['kind'] in ('informal','changed_signature')]
    useful=[r['id'] for r in rows if r['candidate']['correct'] and not r['control']['correct']]
    harmful=[r['id'] for r in rows if (r['control']['correct'] and not r['candidate']['correct']) or
             (r['candidate']['wrong'] and not r['control']['wrong']) or
             (r['candidate']['unqualified'] and not r['control']['unqualified']) or
             (r['candidate']['infrastructure_error'] and not r['control']['infrastructure_error'])]
    overall={a:metrics(a,rows) for a in ('control','candidate')}
    eligible=bool(useful and not harmful and not any(overall['candidate'][k] for k in
        ('wrong_accepted','unqualified_accepted','infrastructure_errors')) and all(
            r[a]['within_route_budget'] for r in rows for a in ('control','candidate')))
    return {'overall':overall,'specified':{a:metrics(a,specified) for a in ('control','candidate')},
            'no_example_pre_retrieval_controls':{a:metrics(a,[r for r in rows if r not in specified]) for a in ('control','candidate')},
            'useful_changes':useful,'harmful_changes':harmful,'retain_as_development_candidate':eligible,
            'release_qualified':False,'fresh_confirmation':False}


def run(monitor):
    candidate=verify_candidate(); candidate_sha=sha(OUTPUT/'candidate.json')
    if (OUTPUT/'summary.json').exists():
        saved=load(OUTPUT/'summary.json')
        if any(sha(OUTPUT/p)!=h for p,h in saved['artifacts_sha256'].items()): raise ValueError('Completed comparison artifact drift')
        print(json.dumps({'resumed_complete':True,'candidate_sha256':candidate_sha,'summary_sha256':sha(OUTPUT/'summary.json')}),flush=True)
        return
    import numpy as np
    import torch
    from dataclasses import replace
    from .approved_library import ApprovedLibrary
    from .answer import answer
    from .clarify import load_profiles
    from .lookup import LookupIndex
    from .routes import Budget, Context
    from .splits import IndexEntry
    from .requirement_filter import RequirementFilter, answer_with_policy
    torch.set_num_threads(4); torch.set_num_interop_threads(1)
    if not torch.equal(torch.ones((2,2))@torch.ones((2,2)),torch.full((2,2),2.)): raise ValueError('CPU compute probe failed')
    print(json.dumps({'python':sys.executable,'torch':torch.__version__,'transformers':candidate['dependencies']['transformers'],
                      'cuda_available':torch.cuda.is_available(),'cuda_count':torch.cuda.device_count(),'device':'cpu'}),flush=True)
    entries=[IndexEntry(**e) for e in load(CONTROL/'qualified-entries.json')]
    vectors=np.stack([np.load(CONTROL/f'embeddings/{i:04d}.npy',allow_pickle=False) for i in range(len(entries))])
    if vectors.shape!=(66,1024) or not np.isfinite(vectors).all(): raise ValueError('Invalid fixed vectors')
    lookup=LookupIndex(entries,vectors);fixtures=load(CONTROL/'fixtures.json')
    approved=ApprovedLibrary.load(CONTROL/'approved-library.json');approved.verify_runtime(LANE_ROOT)
    policy=RequirementFilter(load_profiles()['profiles'])
    budget=Budget.from_contract(load(LANE_ROOT/'contracts/run_contract.json'))
    thresholds=load(LANE_ROOT/'contracts/lookup_thresholds.json');statement_thresholds=load(LANE_ROOT/'contracts/statement_lookup_thresholds.json')
    encoder=None; setup=[]
    def get_encoder():
        nonlocal encoder
        if encoder is None:
            from .embed import Embedder
            start=time.perf_counter();encoder=Embedder(device='cpu')
            setup.append({'encoder_load_hash_verification_seconds':time.perf_counter()-start})
        return encoder
    def check():
        if source_hashes()!=candidate['sources_sha256']:raise ValueError('Source drift during comparison')
    for part in ('shared','responses/control','responses/candidate','scores/control','scores/candidate','requests'):(OUTPUT/part).mkdir(parents=True,exist_ok=True)
    responses=[]
    for i,fixture in enumerate(fixtures):
        check(); request_start=time.perf_counter();query=Problem.from_dict(fixture['query'])
        shared_path=OUTPUT/f'shared/{i:04d}.json'
        binding={'candidate_sha256':candidate_sha,'fixture_sha256':digest(fixture['query'])}
        def retrieve():
            exact=lookup.exact_problem_key(query) or lookup.exact_key(query.query_text())
            if not query.public_tests or exact is not None:
                return {'text':query.statement,'candidates':[],'vector_sha256':None,'vector':None,'vector_dtype':None,'embedding_seconds':0.,'retrieval_seconds':0.,'shared_seconds':0.,'gate':'no_examples' if not query.public_tests else 'exact'}
            model=get_encoder() # Setup is reported separately, never charged as warm inference.
            started=time.perf_counter();v=model.encode([query.statement],query=True)[0]
            embedded=time.perf_counter();cs=lookup.scored_candidates(query.statement,v);retrieved=time.perf_counter()
            import hashlib
            return {'text':query.statement,'candidates':cs,'vector_sha256':hashlib.sha256(v.tobytes()).hexdigest(),
                    'vector':v.tolist(),'vector_dtype':str(v.dtype),
                    'embedding_seconds':embedded-started,'retrieval_seconds':retrieved-embedded,
                    'shared_seconds':retrieved-started,'gate':None}
        shared=bound_receipt(shared_path,binding,retrieve)
        v=None
        if shared['vector_sha256']:
            import hashlib
            v=np.asarray(shared['vector'],dtype=shared['vector_dtype'])
            if hashlib.sha256(v.tobytes()).hexdigest()!=shared['vector_sha256']:raise ValueError('Shared query vector drift')
            if v.shape!=(1024,) or not np.isfinite(v).all():raise ValueError('Invalid shared query vector')
        cache=SharedInputs(lookup,query.statement,v,shared['candidates'])
        order=['control','candidate'] if i%2==0 else ['candidate','control'];pair={}
        for arm in order:
            rp=OUTPUT/f'responses/{arm}/{i:04d}.json'
            rb={**binding,'arm':arm,'shared_receipt_sha256':sha(shared_path)}
            def decide_arm():
                remaining=budget.route_wall_seconds-shared['shared_seconds']
                if remaining<=0:
                    return {'result':{'decision':'abstain','reason':'budget_exhausted','seconds':0.,'attempts':[]},
                            'cached_arm_seconds':0.,'charged_route_seconds':shared['shared_seconds'],'within_route_budget':False}
                context=Context(generator=None,embedder=cache,lookup=cache,thresholds=thresholds,classifier=None,entries=entries,
                                budget=replace(budget,route_wall_seconds=remaining))
                context.statement_thresholds=statement_thresholds
                start=time.perf_counter()
                result=(answer(context,query,approved_library=approved) if arm=='control' else answer_with_policy(context,query,approved,policy))
                result['candidate_qualification_audit']=[{'key':c['key'], **approved.check(entries[lookup.by_key[c['key']]])} for c in shared['candidates']]
                elapsed=time.perf_counter()-start;check()
                return {'result':result,'cached_arm_seconds':elapsed,'charged_route_seconds':shared['shared_seconds']+elapsed,
                        'within_route_budget':shared['shared_seconds']+elapsed<=budget.route_wall_seconds}
            pair[arm]=bound_receipt(rp,rb,decide_arm)
            print(json.dumps({'request':fixture['id'],'arm':arm,'decision':pair[arm]['result']['decision'],
                              'reason':pair[arm]['result'].get('reason'),**monitor.counters()}),flush=True)
        # Actual paired wall includes loading (if any), I/O, guards and both arms.
        bound_receipt(OUTPUT/f'requests/{i:04d}.json',binding,lambda:{'order':order,
             'actual_paired_request_wall_seconds':time.perf_counter()-request_start,
             'accounting':'Shared query retrieval measured once; charged to each arm. Stored source vectors cached from fixed control. Arm costs measured with replay; first request includes setup in actual paired wall.'})
        responses.append(pair)
    check()
    response_hashes={str(p.relative_to(OUTPUT)):sha(p) for p in sorted((OUTPUT/'responses').rglob('*.json'))}
    publish(OUTPUT/'decisions-seal.json',{'candidate_sha256':candidate_sha,'responses_sha256':response_hashes})
    # Independent source suites enter only after every public decision is sealed.
    from . import validate
    source_tests=load(CONTROL/'source-tests.json');scored=[]
    for i,(fixture,pair) in enumerate(zip(fixtures,responses)):
        binding={'candidate_sha256':candidate_sha,'decisions_seal_sha256':sha(OUTPUT/'decisions-seal.json'),
                 'fixture_sha256':digest(fixture),'test_authority_sha256':sha(CONTROL/'source-tests.json')}
        def score_arm(arm):
            result=pair[arm]['result'];accepted=result['decision']=='answered';key=fixture['expected_key'];verdict=None;elapsed=0.
            if accepted and key in source_tests:
                q=Problem.from_dict(fixture['query']);q.entry=result['answer_interface']
                start=time.perf_counter();verdict=validate.judge_problem(q,result['code'],source_tests[key]['tests']).to_dict();elapsed=time.perf_counter()-start
            identity=key is not None and result.get('match',{}).get('key')==key
            unknown=bool(accepted and (not verdict or verdict['reason'] in ('sandbox_error','checker_error','no_tests')))
            approval=(result.get('source') or {}).get('qualification',{}).get('approved',False)
            infrastructure=infra(result) or bool(verdict and verdict['reason'] in ('sandbox_error','checker_error'))
            return {'accepted':accepted,'correct':bool(accepted and identity and verdict and verdict['passed'] and approval),
                'wrong':bool(accepted and (not identity or (verdict and not unknown and not verdict['passed']))),
                'unqualified':bool(accepted and (unknown or not approval)),'identity_correct':identity,
                'infrastructure_error':infrastructure,'infrastructure_reason':'sandbox_error' if infrastructure else None,
                'independent':verdict,'independent_scoring_seconds':elapsed,'reason':result.get('reason'),
                'first_choice':((result.get('match') or {}).get('candidates') or [{}])[0].get('key'),
                'charged_route_seconds':pair[arm]['charged_route_seconds'], 'cached_arm_seconds':pair[arm]['cached_arm_seconds'],
                'within_route_budget':pair[arm]['within_route_budget']}

        arms=score_pair_receipts(OUTPUT/'scores',i,binding,score_arm)
        scored.append({'id':fixture['id'],'kind':fixture['kind'],**arms})
    check();check_control(candidate['control_snapshot'])
    report=summarize(scored)
    historical=[]
    for i,row in enumerate(scored):
        old=load(CONTROL/f'scores/{i:04d}.json')['value'];new=row['control']
        if (old['accepted'],old['accepted_and_correct'],old['reason'])!=(new['accepted'],new['correct'],new['reason']):historical.append(row['id'])
    if historical:report['retain_as_development_candidate']=False
    child=resource.getrusage(resource.RUSAGE_CHILDREN)
    report.update(schema='algsolve.requirements-paired-development-report.v1',name=NAME,candidate_sha256=candidate_sha,
        control_candidate_sha256=CONTROL_SHA,control_drift_from_original=historical,rows=scored,
        resource_counters=monitor.counters(),child_cpu_seconds=child.ru_utime+child.ru_stime,
        encoder_setup_this_invocation=setup,questions=0,protected_opened=False,training=False,
        source_vectors='66 cached vectors from original control, not remeasured',query_retrieval='one fresh embedding/retrieval per eligible query shared by both arms',
        limitations=candidate['contract']['limitations'])
    report['artifacts_sha256']={str(p.relative_to(OUTPUT)):sha(p) for p in sorted(OUTPUT.rglob('*'))
        if p.is_file() and p.name!='lock' and 'failures' not in p.parts and not p.name.startswith('.')}
    publish(OUTPUT/'summary.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','artifacts_sha256')},indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['freeze','run'])
    args=parser.parse_args();OUTPUT.mkdir(parents=True,exist_ok=True)
    lock=(OUTPUT/'lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    os.environ['ALGSOLVE_EMBEDDING_DIR']=str(ASSET/'encoder')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    if args.action=='freeze':freeze();return
    monitor=Monitor([ASSET,CONTROL,OUTPUT]);monitor.start()
    print(f'[run-contract] run_name={NAME} pairs_input_spec=frozen-66-entry-24-request-control resume_from=hash-bound-receipts resume_stage=existing decode=none eval_dataset_paths=consumed-development-only device=cpu schedule=paired-alternating runtime_mode=reviewed-linux-sandbox sweep_mode=live',flush=True)
    try:run(monitor)
    except BaseException as error:
        failures=OUTPUT/'failures';failures.mkdir(exist_ok=True)
        failure={'error_type':type(error).__name__,'detail':str(error),'resources':monitor.counters()}
        publish(failures/f'{time.time_ns()}.json',failure);print(json.dumps(failure),flush=True);raise
    finally:monitor.stop.set()

if __name__=='__main__':main()
