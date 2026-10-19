"""Bounded, separately identified LCD recognition development reconstruction.

No protected scoring, generated answers, threshold fitting or composer training.
Raw data, source code and per-query responses stay in ignored local directories.
"""
from pathlib import Path
import argparse
from collections import Counter
import copy
import fcntl
import hashlib
import io
import json
import os
import signal
import threading
import time

from .records import LANE_ROOT, Problem
from .rebuild_download import FILES, verify

NAME = 'recognition-rebuild-dev-suby-v1'
GIB = 1024**3


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4*1024*1024), b''): h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def publish(path, value):
    from .synth.typed_scoring import write_json_once
    if path.exists():
        if json.loads(path.read_text()) != value: raise ValueError('Frozen artifact differs: '+path.name)
    else: write_json_once(path,value)


def boundary(catalog, reservation):
    from .splits import sibling_base
    blocked = {k for k,v in catalog['excluded'].items() if v=='protected_composition_alias'}
    pool = reservation['reservation']['pool']
    blocked.update(r['key'] for r in pool)
    families = {r['family'] for r in pool} | {sibling_base(k.removeprefix('lc:')) for k in blocked}
    uids = {u for r in pool for u in r['members']}
    uids.update(r['judge_uid'] for r in pool if r.get('judge_uid'))
    return {'keys':sorted(blocked),'families':sorted(families),'uids':sorted(uids)}


def exclusion(row, limits):
    from .splits import sibling_base
    key = 'lc:'+row['task_id']; uid = 'lcd:'+str(row['question_id'])
    if key in limits['keys'] or uid in limits['uids'] or sibling_base(row['task_id']) in limits['families']:
        return 'protected_identity_family_or_recorded_alias'
    return None


def disk_size(roots):
    total=0
    for root in roots:
        for p in root.rglob('*'):
            try:
                if p.is_file(): total+=p.stat().st_size
            except FileNotFoundError: pass  # Atomic publication removes temporary names.
    return total


def bound_receipt(path, binding, make):
    if path.exists(): row=json.loads(path.read_text())
    else:
        body={'binding':binding,'value':make()}
        row={**body,'receipt_sha256':digest(body)}
        publish(path,row)
    body={k:v for k,v in row.items() if k!='receipt_sha256'}
    if body.get('binding')!=binding or digest(body)!=row.get('receipt_sha256'):
        raise ValueError('Receipt binding or contents differ: '+path.name)
    return body['value']


class EnvelopeExceeded(RuntimeError): pass


class Monitor:
    """Conservative aggregate RSS watchdog and per-process CPU affinity cap."""
    def __init__(self, roots, seconds=900):
        self.roots=roots; self.started=time.monotonic(); self.seconds=seconds
        self.peak_rss=0; self.disk_bytes=0; self.reason=None; self.stop=threading.Event()
        self.cpu_started=time.process_time()

    def start(self):
        os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:4])
        signal.signal(signal.SIGUSR1,lambda *args: self.exceeded())
        self.thread=threading.Thread(target=self.watch,daemon=True); self.thread.start()

    def exceeded(self): raise EnvelopeExceeded(self.reason or 'Resource envelope exceeded')

    def watch(self):
        pid=os.getpid(); tick=0
        while not self.stop.wait(.1):
            parents={}; rss={}
            for p in Path('/proc').iterdir():
                if not p.name.isdigit(): continue
                try:
                    fields=dict(line.split(':',1) for line in (p/'status').read_text().splitlines() if ':' in line)
                    parents[int(p.name)]=int(fields['PPid'])
                    rss[int(p.name)]=int(fields.get('VmRSS','0 kB').split()[0])*1024
                except (OSError,KeyError,ValueError): continue
            owned={pid}
            while True:
                more={p for p,parent in parents.items() if parent in owned}
                if more<=owned: break
                owned.update(more)
            self.peak_rss=max(self.peak_rss,sum(rss.get(p,0) for p in owned))
            tick+=1
            if tick%20==0:
                self.disk_bytes=disk_size(self.roots)
            if self.peak_rss>8*GIB: self.reason='Aggregate process-tree RSS exceeds 8 GiB'
            if self.disk_bytes>5*GIB: self.reason='Run assets exceed 5 GiB'
            if time.monotonic()-self.started>self.seconds: self.reason='First pilot exceeds 900-second wall budget'
            if self.reason:
                os.kill(pid,signal.SIGUSR1); return

    def counters(self):
        return {'wall_seconds':time.monotonic()-self.started,'process_cpu_seconds':time.process_time()-self.cpu_started,
                'peak_aggregate_rss_bytes':self.peak_rss,'disk_bytes':disk_size(self.roots),
                'cpu_affinity':sorted(os.sched_getaffinity(0)),'threads':4,
                'rss_sampling_seconds':.1,'disk_sampling_seconds':2.,'limit_reason':self.reason}


def prepare(asset, output, wanted, targets, limits, universe):
    from . import importers, values
    from .splits import IndexEntry
    receipt=output/'inputs.json'
    if receipt.exists():
        info=json.loads(receipt.read_text())
        for name,h in info['files_sha256'].items():
            if sha(output/name)!=h: raise ValueError('Prepared input changed')
        return info
    entries=[]; problems={}; tests={}; dropped=Counter(); excluded=[]
    with (asset/'LeetCodeDataset-train.jsonl').open() as stream:
        for line in stream:
            row=json.loads(line)
            # Metadata boundary before signature parsing, indexing or test/code qualification.
            reason=exclusion(row,limits); key='lc:'+row['task_id']; uid='lcd:'+str(row['question_id'])
            if reason:
                dropped[reason]+=1; excluded.append({'uid':uid,'key':key,'reason':reason}); continue
            if key not in universe: dropped['outside_historical_key_universe']+=1; continue
            if key not in wanted: dropped['outside_frozen_development_shortlist']+=1; continue
            method=row['entry_point'].split('.',1)[1]
            try:
                params=values.signature(row['starter_code'],method)
                public,public_dropped=importers.statement_examples(row['problem_description'],params,
                    values.return_annotation(row['starter_code'],method))
            except values.Unsupported:
                dropped['unsupported_signature_or_public_data']+=1; continue
            if public_dropped: public=[]
            p=Problem(uid,'lcd',str(row['question_id']),row['task_id'].replace('-',' '),row['task_id'],
                row['problem_description'].strip(),'functional',starter_code=row['starter_code'],
                entry={'class':'Solution','method':method},params=[list(p) for p in params],
                tags=list(row.get('tags') or []),difficulty=row.get('difficulty',''),
                public_tests=public,license=importers.LCD_LICENSE,
                attribution='https://leetcode.com/problems/'+row['task_id']+'/ via newfacade/LeetCodeDataset')
            entry=IndexEntry(key,p.slug,p.title,p.statement,p.starter_code,p.entry,p.params,p.tags,p.difficulty,[uid],
                references=[{'uid':uid,'source':'lcd','code':row['completion'],'validated':False}],
                license=[p.license],attribution=[p.attribution])
            entries.append(entry.__dict__)
            if key in targets:
                hidden,n=importers.lcd_hidden_tests(row['test'],params)
                problems[key]=json.loads(p.to_json()); tests[key]={'tests':hidden,'dropped':n,'public_dropped':public_dropped}
    entries.sort(key=lambda e:e['key'])
    if len({e['key'] for e in entries})!=len(entries): raise ValueError('Duplicate source identities')
    for name,value in [('entries.json',entries),('problems.json',problems),('source-tests.json',tests),('exclusions.json',excluded)]:
        publish(output/name,value)
    info={'indexed_entries':len(entries),'target_keys':sorted(targets),'missing_targets':sorted(targets-set(problems)),
          'source_rows_excluded':dict(dropped),'index_selection':'Union of the existing 24-query development receipt shortlists and 16 targets, before this run; not the historical 3353-entry service',
          'files_sha256':{n:sha(output/n) for n in ('entries.json','problems.json','source-tests.json','exclusions.json')}}
    publish(receipt,info); return info


def run(asset, output, monitor):
    import importlib.metadata
    from dataclasses import asdict
    import numpy as np
    import torch
    from . import approved_library, embed, validate
    from .answer import answer
    from .lookup import LookupIndex
    from .routes import Budget, Context
    from .splits import IndexEntry
    torch.set_num_threads(4); torch.set_num_interop_threads(1)
    if not torch.equal(torch.ones(2,2)@torch.ones(2,2),torch.full((2,2),2.)): raise RuntimeError('CPU probe failed')
    fixed_paths=['contracts/natural_description_dev_v1.json','findings/natural-description-dev-v1/recognition.jsonl',
                 'findings/known-lookup-release-v2/approved-library.json','contracts/typed_confirmation_v1.json',
                 'contracts/lookup_thresholds.json','contracts/statement_lookup_thresholds.json','contracts/run_contract.json']
    frozen={p:sha(LANE_ROOT/p) for p in fixed_paths}
    frozen.update({str(p.relative_to(LANE_ROOT)):sha(p) for p in (LANE_ROOT/'algsolve').rglob('*.py')})
    cases=json.loads((LANE_ROOT/fixed_paths[0]).read_text())['cases']
    catalog=json.loads((LANE_ROOT/fixed_paths[2]).read_text())
    limits=boundary(catalog,json.loads((LANE_ROOT/fixed_paths[3]).read_text()))
    targets={k for case in cases for k in case['expected']['keys']}
    prior=[json.loads(s) for s in (LANE_ROOT/fixed_paths[1]).read_text().splitlines()]
    wanted=targets|{c['key'] for row in prior for c in row['prediction'].get('candidates',[])}
    universe=set(catalog['approved'])|set(catalog['excluded'])
    payloads={name:verify(asset/name,spec) for name,spec in FILES.items()}
    plan={'schema':'algsolve.recognition-rebuild-plan.v1','name':NAME,'scope':'development only; no historical reproduction or fresh confirmation',
          'fixed_files_sha256':frozen,'payloads':payloads,'selected_keys':sorted(wanted),'target_keys':sorted(targets),
          'exclusions':limits,'cpu_threads':4,'max_rss_bytes':8*GIB,'max_disk_bytes':5*GIB,'wall_budget_seconds':900,
          'dependencies':{n:importlib.metadata.version(n) for n in ('torch','transformers','numpy')},
          'thresholds_changed':False,'generation':False,'protected_opened':False,'questions':0,
          'fixture_policy':'Original authored description text plus target-source public examples for specified requests; no starter, params, target key or oracle signature is passed to answer(). Ambiguous/out-of-domain requests get no invented examples.'}
    publish(output/'plan.json',plan)
    if (output/'summary.json').exists():
        saved=json.loads((output/'summary.json').read_text())
        if any(sha(output/p)!=h for p,h in saved['artifacts_sha256'].items()):
            raise ValueError('Completed run artifact drift')
        print(json.dumps(saved,indent=2),flush=True); return
    def check():
        if any(sha(LANE_ROOT/p)!=h for p,h in frozen.items()): raise ValueError('Candidate source/contract changed')
    check(); info=prepare(asset,output,wanted,targets,limits,universe)
    entries=[IndexEntry(**e) for e in json.loads((output/'entries.json').read_text())]
    problems=json.loads((output/'problems.json').read_text()); source_tests=json.loads((output/'source-tests.json').read_text())
    budget=Budget.from_contract(json.loads((LANE_ROOT/'contracts/run_contract.json').read_text()))
    thresholds=json.loads((LANE_ROOT/'contracts/lookup_thresholds.json').read_text())
    statement_thresholds=json.loads((LANE_ROOT/'contracts/statement_lookup_thresholds.json').read_text())
    class ExactOnly:
        def encode(self,*args,**kw): raise AssertionError('Exact source qualification must not encode')
    exact=Context(generator=None,embedder=ExactOnly(),lookup=LookupIndex(entries,np.zeros((len(entries),1))),thresholds=thresholds,classifier=None,entries=entries,budget=budget)
    qual=output/'qualification'; qual.mkdir(exist_ok=True)
    by_key={e.key:e for e in entries}; qualifications={}
    for key in sorted(targets):
        path=qual/(key.removeprefix('lc:')+'.json')
        binding={'plan_sha256':sha(output/'plan.json'),'key':key,
                 'problem_sha256':digest(problems.get(key)),'test_authority_sha256':digest(source_tests.get(key))}
        if path.exists(): result=bound_receipt(path,binding,lambda:None)
        else:
            result={'key':key,'status':'missing_source','independent':None,'public':None,'exact':None}
            if key in problems:
                p=Problem.from_dict(problems[key]); source=by_key[key].references[0]['code']; spec=source_tests[key]
                result.update(independent_tests=len(spec['tests']),dropped_independent=spec['dropped'],public_tests=len(p.public_tests))
                if not p.public_tests: result['status']='missing_complete_public_examples'
                elif not spec['tests'] or spec['dropped']: result['status']='missing_or_incomplete_independent_tests'
                else:
                    result['public']=validate.judge_problem(p,source,p.public_tests).to_dict()
                    result['independent']=validate.judge_problem(p,source,spec['tests']).to_dict()
                    result['exact']=answer(exact,p)
                    ok=(result['public']['passed'] and result['independent']['passed'] and
                        result['exact']['decision']=='answered' and result['exact']['code']==source and
                        result['exact'].get('match',{}).get('key')==key)
                    result['status']='passed' if ok else 'qualification_failed'
            check(); bound_receipt(path,binding,lambda:result)
        qualifications[key]=result
        if result['status']=='passed': by_key[key].references[0]['validated']=True
        print(json.dumps({'qualified_target':key,'status':result['status'],**monitor.counters()}),flush=True)
    inventory=[]; rows=[]
    for e in entries:
        ref=e.references[0]; q=qualifications.get(e.key); passed=q and q['status']=='passed'
        code_hash=approved_library.code_hash(ref['code'])
        inventory.append({'key':e.key,'identity_valid':True,'provenance_present':True,'interface_compatible':True,
                          'references':[{'code_sha256':code_hash}],
                          'independent_test_sets':[{'sha256':digest(source_tests[e.key]['tests']),'tests':len(source_tests[e.key]['tests'])}] if passed else []})
        rows.append({'key':e.key,'accepted_and_correct':bool(passed),'result':{'code_sha256':code_hash if passed else None},
                     'stored_solution':{'status':'passed' if passed else (q['status'] if q else 'not_qualified_in_this_pilot'),
                                        'verdicts':[q['independent']] if passed else []}})
    publish(output/'qualified-entries.json',[asdict(e) for e in entries])
    approval=approved_library.build(entries,inventory,rows,evidence={'development_reconstruction':True,'plan_sha256':sha(output/'plan.json')},runtime_files=frozen)
    publish(output/'approved-library.json',approval)
    fixture_rows=[]
    for case in cases:
        key=next(iter(case['expected']['keys']),None)
        p=problems.get(key); public=copy.deepcopy(p['public_tests']) if p else []
        query=Problem('development:'+case['id'],'user',case['id'],'','',case['query'],'functional',public_tests=public)
        fixture_rows.append({'id':case['id'],'kind':case['kind'],'expected_key':key,'source_available':p is not None,
                             'input_origin':'existing authored development description; newly supplied indexed public examples, no oracle interface',
                             'query':json.loads(query.to_json())})
    publish(output/'fixtures.json',fixture_rows)
    vectors_dir=output/'embeddings'; vectors_dir.mkdir(exist_ok=True)
    vector_paths=[vectors_dir/f'{i:04d}.npy' for i in range(len(entries))]
    encoder=None; setup=[]
    def get_encoder():
        nonlocal encoder
        if encoder is None:
            started=time.perf_counter(); encoder=embed.Embedder(device='cpu')
            setup.append({'encoder_load_and_hash_verification_seconds':time.perf_counter()-started})
        return encoder
    from .synth.typed_scoring import write_bytes_once
    for i,(entry,path) in enumerate(zip(entries,vector_paths)):
        if not path.exists():
            started=time.perf_counter(); vector=get_encoder().encode([entry.query_text()],batch_size=1)[0]
            elapsed=time.perf_counter()-started
            data=io.BytesIO(); np.save(data,vector); write_bytes_once(path,data.getvalue())
            publish(vectors_dir/f'{i:04d}.json',{'key':entry.key,'seconds_including_first_load_if_needed':elapsed,'vector_sha256':sha(path)})
        metadata=json.loads((vectors_dir/f'{i:04d}.json').read_text())
        if metadata['key']!=entry.key or metadata['vector_sha256']!=sha(path):
            raise ValueError('Cached embedding identity differs')
        vector=np.load(path,allow_pickle=False)
        if vector.shape!=(1024,) or not np.isfinite(vector).all(): raise ValueError('Invalid embedding')
        if i%10==0: print(json.dumps({'embedded':i+1,'total':len(entries),**monitor.counters()}),flush=True)
    matrix=np.stack([np.load(p,allow_pickle=False) for p in vector_paths])
    context=Context(generator=None,embedder=get_encoder(),lookup=LookupIndex(entries,matrix),thresholds=thresholds,classifier=None,entries=entries,budget=budget)
    context.statement_thresholds=statement_thresholds
    approved=approved_library.ApprovedLibrary(approval); approved.verify_runtime(LANE_ROOT)
    candidate={'schema':'algsolve.recognition-rebuild-candidate.v1','plan_sha256':sha(output/'plan.json'),
               'approval_sha256':sha(output/'approved-library.json'),'fixtures_sha256':sha(output/'fixtures.json'),
               'entries_sha256':sha(output/'qualified-entries.json'),'embedding_sha256':[sha(p) for p in vector_paths]}
    publish(output/'candidate.json',candidate)
    response_dir=output/'responses'; response_dir.mkdir(exist_ok=True)
    responses=[]
    for i,fixture in enumerate(fixture_rows):
        path=response_dir/f'{i:04d}.json'
        binding={'candidate_sha256':sha(output/'candidate.json'),'fixture_sha256':digest(fixture),'id':fixture['id']}
        def decide():
            check()
            return {'id':fixture['id'],'result':answer(context,Problem.from_dict(fixture['query']),approved_library=approved)}
        row=bound_receipt(path,binding,decide)
        responses.append(row)
        print(json.dumps({'decided':fixture['id'],'decision':row['result']['decision'],'reason':row['result'].get('reason'),**monitor.counters()}),flush=True)
    publish(output/'decisions-seal.json',{'candidate_sha256':sha(output/'candidate.json'),
        'response_files_sha256':{p.name:sha(p) for p in sorted(response_dir.glob('*.json'))}})
    score_dir=output/'scores'; score_dir.mkdir(exist_ok=True); scored=[]
    for i,(fixture,response) in enumerate(zip(fixture_rows,responses)):
        path=score_dir/f'{i:04d}.json'
        binding={'decisions_seal_sha256':sha(output/'decisions-seal.json'),
                 'response_sha256':digest(response),'test_authority_sha256':digest(source_tests.get(fixture['expected_key']))}
        def score_response():
            result=response['result']; accepted=result['decision']=='answered'; key=fixture['expected_key']
            matched=result.get('match',{}).get('key'); verdict=None
            if accepted and key in source_tests:
                p=Problem.from_dict(fixture['query']); p.entry=result['answer_interface']
                verdict=validate.judge_problem(p,result['code'],source_tests[key]['tests']).to_dict()
            unknown=accepted and (not verdict or verdict['reason'] in ('sandbox_error','checker_error','no_tests'))
            identity=key is not None and matched==key
            row={'id':fixture['id'],'kind':fixture['kind'],'source_available':fixture['source_available'],
                 'accepted':accepted,'identity_correct':identity,'accepted_and_correct':bool(accepted and identity and not unknown and verdict['passed']),
                 'wrong_acceptance':bool(accepted and (not identity or (not unknown and not verdict['passed']))),
                 'accepted_unqualified':bool(unknown),'independent':verdict,'questions':0,
                 'decision_seconds':result['seconds'],'reason':result.get('reason')}
            check(); return row
        row=bound_receipt(path,binding,score_response)
        scored.append(row)
    known=[r for r in scored if r['kind'] in ('informal','changed_signature')]
    def metrics(rs):
        times=[r['decision_seconds'] for r in rs]
        return {'requests':len(rs),'returned':sum(r['accepted'] for r in rs),'accepted_correct':sum(r['accepted_and_correct'] for r in rs),
                'wrong_acceptances':sum(r['wrong_acceptance'] for r in rs),'accepted_unqualified':sum(r['accepted_unqualified'] for r in rs),
                'abstentions':sum(not r['accepted'] for r in rs),'missing_sources':sum(not r['source_available'] for r in rs if r['kind'] in ('informal','changed_signature')),
                'p50_seconds':float(np.percentile(times,50)),'p95_seconds':float(np.percentile(times,95)),'maximum_seconds':max(times)}
    check()
    summary={'schema':'algsolve.recognition-rebuild-development-report.v1','name':NAME,'candidate_sha256':sha(output/'candidate.json'),
             'index_entries':len(entries),'requested_shortlist_keys':len(wanted),'target_references':len(targets),
             'qualification_counts':dict(Counter(q['status'] for q in qualifications.values())),
             'overall':metrics(scored),'specified':metrics(known),'by_kind':{kind:metrics([r for r in scored if r['kind']==kind]) for kind in sorted({r['kind'] for r in scored})},
             'resource_counters':monitor.counters(),'cold_setups_this_invocation':setup,'questions':0,'protected_opened':False,
             'thresholds_changed':False,'composer_trained':False,'fresh_confirmation':False,'historical_reproduction':False,
             'limitations':['LCD-only development shortlist index, not the historical 3353-entry universe; all 24 requests retained.',
                'Specified fixtures add indexed public examples to old authored descriptions; this changes initial information and is not matched to the old description-only baseline.',
                'Imported source test suites qualify stored references and score requirement-equivalent development requests; not independently authored fresh query tests.',
                'Ambiguous requests abstain; four out-of-domain controls do not establish genuine absent-algorithm rejection.',
                'No tuning after this candidate is sealed; failures remain visible; no 1a/1b release or learned composition claim.']}
    summary['artifacts_sha256']={str(p.relative_to(output)):sha(p) for p in sorted(output.rglob('*'))
        if p.is_file() and p.name!='lock' and 'failures' not in p.parts and not p.name.startswith('.')}
    publish(output/'summary.json',summary)
    print(json.dumps(summary,indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--name',choices=[NAME],required=True)
    args=parser.parse_args(); output=LANE_ROOT/'runs'/args.name; output.mkdir(parents=True,exist_ok=True)
    asset=LANE_ROOT/'data/reconstruction'/args.name
    os.environ['ALGSOLVE_EMBEDDING_DIR']=str(asset/'encoder')
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    lock=(output/'lock').open('a')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    monitor=Monitor([asset,output]); monitor.start()
    print(f'[run-contract] run_name={NAME} pairs_input_spec=pinned-LCD-training+authored-description-development resume_from=immutable-stage-receipts resume_stage=existing decode=none eval_dataset_paths=development-only device=cpu schedule=serial runtime_mode=reviewed-linux-sandbox sweep_mode=live',flush=True)
    try: run(asset,output,monitor)
    except BaseException as error:
        failure={'error_type':type(error).__name__,'detail':str(error),'resources':monitor.counters()}
        failures=output/'failures'; failures.mkdir(exist_ok=True)
        publish(failures/f'{time.time_ns()}.json',failure)
        print(json.dumps(failure),flush=True); raise
    finally: monitor.stop.set()


if __name__=='__main__': main()
