"""Frozen cached development comparison only; no encoder, source or confirmation."""
import argparse,hashlib,importlib.util,json,os,resource,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(spec):
    path=Path(spec['path']);raw=path.read_bytes()
    if len(raw)>32*1024**2 or hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('bounded pinned artifact mismatch')
    return json.loads(raw)
def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)
def module(name,spec):
    if sha(spec['path'])!=spec['sha256']:raise ValueError('module drift')
    loader=importlib.util.spec_from_file_location(name,spec['path']);m=importlib.util.module_from_spec(loader);sys.modules[name]=m;loader.loader.exec_module(m);return m

def binding(identity,rows):return hashlib.sha256(json.dumps({'identity':identity,'query':True,'rows':rows},sort_keys=True).encode()).hexdigest()

def restore_queries(f,queries,cache,np):
    """Complete fixed52 rows, exact metadata+array bindings, no hidden cache reuse."""
    if len(queries)!=52 or len({q['query_id'] for q in queries})!=52:raise ValueError('exact52 unique query IDs')
    if [c['start'] for c in f['query_chunks']]!=list(range(0,52,4)):raise ValueError('complete query cache chunks')
    arrays=[];truncated=[]
    for c in f['query_chunks']:
        start=c['start'];rows=[{'problem_id':q['query_id'],'text':q['text']} for q in queries[start:start+4]]
        info=read(c['receipt']);cache.check_pin(c['array'])
        expected=binding(f['index']['encoder_cache_identity'],rows)
        if (info['binding_sha256']!=expected or c['binding_sha256']!=expected or info['array_sha256']!=c['array']['sha256'] or
            info['ids']!=[r['problem_id'] for r in rows]):raise ValueError('query cache binding mismatch')
        request=info['request'];flags=request['truncated']
        if request['query'] is not True or request['rows']!=len(rows) or len(flags)!=len(rows) or any(type(x)is not bool for x in flags):raise ValueError('query truncation metadata mismatch')
        array=np.load(c['array']['path'],allow_pickle=False);cache.validate_array(array,len(rows),np)
        arrays.append(array);truncated.extend(flags)
    return np.concatenate(arrays),truncated

def decision_projection(d):
    # Scores can differ by last-bit BLAS rounding; identity/status/exact receipt
    # selection cannot. Any baseline classification/selection drift blocks claims.
    return {k:d.get(k) for k in ('status','reason','problem_id','implementations')}

def compact(d,query_id):
    guard=d.get('guard',{});parsed=d.get('query_analysis',{})
    return {'query_id':query_id,'status':d['status'],'reason':d.get('reason'),'problem_id':d.get('problem_id'),
            'semantic_proof':False,'clarification_questions':[],
            'guard_overall':guard.get('overall'),'contradictions':guard.get('contradictions',[]),
            'grammar_complete':parsed.get('grammar_complete'),
            'known_query_facets':sorted(parsed.get('facts',{})),
            'unsupported_span_count':len(parsed.get('unsupported_spans',[]))}

def compare_policies(queries,rankings,policies,service,guard,ids,contracts,flags,historical):
    from projects.algorithm_solver.catalogue.empirical_recognition import decide,score_decisions,select_policy
    if len(policies)!=20 or len({p['id'] for p in policies})!=20:raise ValueError('original20 policy identities required')
    if len(queries)!=len(rankings) or len(flags)!=len(queries):raise ValueError('aligned queries/rankings/truncation required')
    results=[]
    for policy in policies:
        old=[decide(r,policy,service,truncated=flags[i]) for i,r in enumerate(rankings)]
        prior=historical[policy['id']]
        if prior['policy']!=policy or len(prior['decisions'])!=len(old):raise ValueError('historical policy mismatch')
        if [decision_projection(d) for d in old]!=[decision_projection(d) for d in prior['decisions']]:raise ValueError('historical baseline decision drift')
        current=[guard.guarded_decide(q['text'],r,policy,service,ids,contracts,truncated=flags[i]) for i,(q,r) in enumerate(zip(queries,rankings))]
        baseline=score_decisions(queries,old);metrics=score_decisions(queries,current)
        for key,value in baseline.items():
            if prior['metrics'].get(key)!=value:raise ValueError('historical baseline metrics drift')
        # A veto cannot create an acceptance, change identity or substitute source.
        for before,after in zip(old,current):
            if after['status']=='accepted' and (before['status']!='accepted' or before['problem_id']!=after['problem_id'] or before['implementations']!=after['implementations']):raise ValueError('guard is not veto-only')
        results.append({'policy':policy,'baseline_metrics':baseline,'metrics':metrics,
            'metric_deltas':{k:metrics[k]-baseline[k] for k in metrics},
            'decisions':[compact(d,q['query_id']) for d,q in zip(current,queries)],
            'grammar_complete_queries':sum(d.get('query_analysis',{}).get('grammar_complete',False) for d in current),
            'queries_with_facts':sum(bool(d.get('query_analysis',{}).get('facts',{})) for d in current)})
    return results,select_policy(results)

def verify(f):
    for name,digest in f['code_sha256'].items():
        if sha(HERE/name)!=digest:raise ValueError('evaluator code drift')
    guard_freeze=read(f['guard_freeze'])
    guardroot=Path(f['guard_freeze']['path']).parent
    for name,digest in guard_freeze['files'].items():
        if sha(guardroot/name)!=digest:raise ValueError('frozen guard drift')
    for name,digest in guard_freeze['dependency_code_sha256'].items():
        if sha(BASE/name)!=digest:raise ValueError('guard dependency drift')
    for name,digest in f['dependency_code_sha256'].items():
        if sha(BASE/name)!=digest:raise ValueError('evaluator dependency drift')

def run(args):
    output=Path(args.output);output.mkdir(exist_ok=False);started=time.perf_counter();cpu0=time.process_time();phase='freeze'
    try:
        resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,)*2);resource.setrlimit(resource.RLIMIT_CPU,(59,60))
        def terminate(*_):raise TimeoutError('host resource budget')
        for signum in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM):signal.signal(signum,terminate)
        signal.alarm(60)
        f=read({'path':args.freeze,'sha256':args.freeze_sha256});verify(f)
        if f['schema']!='gamma.cached-guard-development-freeze.v2' or f['confirmation_read']is not False or f['encoder_invocations']!=0:raise ValueError('scope drift')
        os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
        import numpy as np
        cache=module('frozen_cached_artifacts',f['cache_module']);guard=module('frozen_guard_v2',f['guard_module'])
        queries=read(f['development'])['queries'];policies=read(f['policy'])['policy_family'];historical=read(f['historical_result'])
        phase='gated_contract_facts';ids,contracts=guard.load_documents(f['document_plan'],f['documents'])
        if ids!=f['index']['stable_ids']:raise ValueError('complete universe/order drift')
        phase='cached_vectors';index=cache.restore_index(f['index'],np);vectors,flags=restore_queries(f,queries,cache,np)
        from projects.algorithm_solver.catalogue.empirical_recognition import rank
        rankings=[rank(scores,ids) for scores in vectors@index.array.T]
        from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
        service=KnownSpecService.from_config(f['service']['path'],f['service']['sha256'])
        phase='unchanged20_policy_comparison';results,selected=compare_policies(queries,rankings,policies,service,guard,ids,contracts,flags,{r['policy']['id']:r for r in historical['results']})
        verify(f)
        report={'schema':'gamma.cached-guard-development-result.v2','freeze_sha256':args.freeze_sha256,'status':'completed',
            'results':results,'selected_policy':selected,'historical_baseline_reproduced':True,'population':4081,'queries':52,'policy_count':20,
            'encoder_invocations':0,'candidate_executions':0,'candidate_source_reads':0,'confirmation_read':False,
            'recognition_qualified':False,'semantic_proof':False,'source_availability_ranking_filter':False,
            'wall_seconds':time.perf_counter()-started,'cpu_seconds':time.process_time()-cpu0,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'evidence_scope':'Authored non-IID development comparison with fixed versioned guard; not independent confirmation or recognition qualification. Cached data processing, not fresh serving latency.'}
        save(output/'report.json',report)
    except BaseException as error:
        save(output/'failure.json',{'status':'failed','phase':phase,'error_type':type(error).__name__,'recognition_qualified':False,'encoder_invocations':0,'confirmation_read':False})
        raise
    finally:signal.alarm(0)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('freeze','freeze-sha256','output'):p.add_argument('--'+name,required=True)
    run(p.parse_args())
