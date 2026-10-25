"""Frozen48-document CPU delta; matchedv16 arms and explicitv8 service control."""
import argparse,hashlib,importlib.util,json,os,resource,signal,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent

def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pinned(spec):
    path=Path(spec['path'])
    if not path.is_absolute()or path.stat().st_size>32*1024**2:raise ValueError('bounded absolute descriptor required')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=spec['sha256']:raise ValueError('pinned metadata mismatch')
    return json.loads(raw)
def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)
def module(name,spec):
    if file_sha(spec['path'])!=spec['sha256']:raise ValueError('module drift')
    loader=importlib.util.spec_from_file_location(name,spec['path']);m=importlib.util.module_from_spec(loader);sys.modules[name]=m;loader.loader.exec_module(m);return m

def load_document_pair(f):
    from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open
    oldplan=pinned(f['old_document_plan']);newplan=pinned(f['new_document_plan'])
    if oldplan['boundary_gate']!=newplan['boundary_gate']:raise ValueError('same boundary required')
    gate=pinned(oldplan['boundary_gate']);bundles=[]
    for plan,spec,count,plan_spec in ((oldplan,f['old_documents'],54,f['old_document_plan']),(newplan,f['new_documents'],102,f['new_document_plan'])):
        ids=[a['problem_id']for a in plan['authorities']]
        if len(ids)!=count or len(set(ids))!=count:raise ValueError('exact authorized semantic population')
        for pid in ids:authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],language='javascript',payload_kind='statement')
        bundle=pinned(spec)
        if bundle['plan_sha256']!=plan_spec['sha256']or bundle['enriched']!=count or bundle['population']!=4081 or set(bundle['changed_problem_ids'])!=set(ids):raise ValueError('document authority/population binding')
        bundles.append(bundle)
    return bundles

def alignment(old,new):
    if old['stable_ids']!=new['stable_ids']or len(old['stable_ids'])!=4081 or len(set(old['stable_ids']))!=4081:raise ValueError('all4081identity/order required')
    if len(old['documents'])!=4081 or len(new['documents'])!=4081:raise ValueError('complete document rows')
    changed=[]
    for i,(a,b)in enumerate(zip(old['documents'],new['documents'])):
        if a['problem_id']!=b['problem_id']or a['problem_id']!=old['stable_ids'][i]:raise ValueError('document order binding')
        for row in (a,b):
            if hashlib.sha256(row['text'].encode()).hexdigest()!=row['document_sha256']:raise ValueError('document text SHA')
        if a['text']!=b['text']:
            if a['authority']['knowledge_class']!='title-only'or b['authority']['knowledge_class']=='title-only':raise ValueError('only newly authoritative text changes')
            changed.append(i)
    if len(changed)!=48:raise ValueError('exact48 newdocuments')
    return changed

def batch_binding(identity,new_artifact_sha,rows):
    return digest({'schema':'gamma.enriched102-delta-binding.v1','encoder_cache_identity':identity,'new_documents_sha256':new_artifact_sha,
        'rows':[{'problem_id':r['problem_id'],'document_sha256':r['document_sha256']}for r in rows]})

def encode_delta(encoder,rows,f,output,np,cache):
    """Only these48 rows reach encoder.encode, query=False. No resume ambiguity."""
    if len(rows)!=48:raise ValueError('exact48 documents required')
    output.mkdir(exist_ok=False);arrays=[];receipts=[]
    for start in range(0,48,4):
        batch=rows[start:start+4];expected=f['delta_batches'][start//4]
        bind=batch_binding(f['encoder_cache_identity'],f['new_documents']['sha256'],batch)
        if expected!={'start':start,'ids':[r['problem_id']for r in batch],'binding_sha256':bind}:raise ValueError('frozen delta batch drift')
        array=encoder.encode([r['text']for r in batch],query=False);cache.validate_array(array,len(batch),np)
        info=encoder.last_request_info
        if (not isinstance(info,dict)or info.get('query')is not False or info.get('rows')!=len(batch)or
            len(info.get('truncated',[]))!=len(batch)or any(x is not False for x in info['truncated'])):raise ValueError('missing or truncated delta document')
        path=output/f'{start:04d}.npy'
        with path.open('xb')as stream:np.save(stream,array,allow_pickle=False);stream.flush();os.fsync(stream.fileno())
        receipt={'start':start,'ids':expected['ids'],'binding_sha256':bind,'array_sha256':file_sha(path),'request':info}
        save(output/f'{start:04d}.json',receipt);receipts.append(receipt);arrays.append(array)
        save(output.parent/'progress.json',{'phase':'new_document_encoding','completed_documents':start+len(batch),'total_documents':48,'completed_batches':len(receipts)})
    return np.concatenate(arrays),receipts

def install_delta(old,positions,delta,np):
    if len(positions)!=48 or len(set(positions))!=48 or delta.shape!=(48,1024):raise ValueError('delta identity/shape')
    new=old.copy();new[positions]=delta
    retained=np.ones(4081,dtype=bool);retained[positions]=False
    if not np.array_equal(old[retained],new[retained]):raise ValueError('old54/remaining3979 vectors changed')
    return new

def projection(d):return {k:d.get(k)for k in ('status','reason','problem_id','implementations')}
def compact(d,qid):return {'query_id':qid,'status':d['status'],'reason':d.get('reason'),'problem_id':d.get('problem_id')}
def compare(queries,rank54,rank102,policies,v8,v16,flags,historical):
    from projects.algorithm_solver.catalogue.empirical_recognition import decide,score_decisions,select_policy
    if len(policies)!=20 or len({p['id']for p in policies})!=20:raise ValueError('same20policies required')
    if len(queries)!=len(rank54)or len(queries)!=len(rank102)or len(flags)!=len(queries):raise ValueError('aligned arm/query/truncation rows')
    results=[]
    for p in policies:
        old=[decide(r,p,v8,truncated=flags[i])for i,r in enumerate(rank54)]
        baseline=[decide(r,p,v16,truncated=flags[i])for i,r in enumerate(rank54)]
        expanded=[decide(r,p,v16,truncated=flags[i])for i,r in enumerate(rank102)]
        prior=historical[p['id']]
        if prior['policy']!=p or [projection(d)for d in old]!=[projection(d)for d in prior['decisions']]:raise ValueError('historical54/v8 decision reproduction failed')
        metrics=[score_decisions(queries,ds)for ds in (old,baseline,expanded)]
        for k,v in metrics[0].items():
            if prior['metrics'].get(k)!=v:raise ValueError('historical metrics drift')
        results.append({'policy':p,'historical54_v8':metrics[0],'baseline54_v16':metrics[1],'expanded102_v16':metrics[2],
            'service_only_delta_v16_minus_v8':{k:metrics[1][k]-metrics[0][k]for k in metrics[0]},
            'document_only_delta_102_minus_54_at_v16':{k:metrics[2][k]-metrics[1][k]for k in metrics[0]},
            'baseline54_v16_decisions':[compact(d,q['query_id'])for d,q in zip(baseline,queries)],
            'expanded102_v16_decisions':[compact(d,q['query_id'])for d,q in zip(expanded,queries)]})
    selected={arm:select_policy([{'policy':r['policy'],'metrics':r[arm]}for r in results])for arm in ('historical54_v8','baseline54_v16','expanded102_v16')}
    return results,selected

def verify(f):
    for name,pin in f['code_sha256'].items():
        if file_sha(HERE/name)!=pin:raise ValueError('local code drift')
    for name,pin in f['dependency_code_sha256'].items():
        if file_sha(BASE/name)!=pin:raise ValueError('dependency code drift')

def run(args):
    output=Path(args.output);output.mkdir(exist_ok=False);start=time.perf_counter();cpu0=time.process_time();phase='preflight'
    save(output/'progress.json',{'phase':phase,'completed_documents':0})
    try:
        f=pinned({'path':str(Path(args.freeze).resolve()),'sha256':args.freeze_sha256});verify(f)
        if f['schema']!='gamma.enriched102-cpu-freeze.v1' or f['new_encode_documents']!=48 or f['query_encode_documents']!=0:raise ValueError('frozen scope')
        resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);resource.setrlimit(resource.RLIMIT_CPU,(300,305))
        def terminate(*_):raise TimeoutError('native resource budget')
        for signum in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM):signal.signal(signum,terminate)
        signal.alarm(240)
        available=int(next(l.split()[1]for l in Path('/proc/meminfo').read_text().splitlines()if l.startswith('MemAvailable:')))*1024
        limit=Path('/sys/fs/cgroup/memory.max');current=Path('/sys/fs/cgroup/memory.current')
        if limit.exists()and current.exists()and limit.read_text().strip()!='max':available=min(available,int(limit.read_text())-int(current.read_text()))
        if available<5*1024**3:raise RuntimeError('less than5GiB effective headroom')
        if Path(sys.executable)!=Path(f['python'])or file_sha(Path(sys.executable).resolve())!=f['encoder_cache_identity']['native_python_sha256']:raise ValueError('native pinned private runtime')
        os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        import numpy as np
        cache=module('frozen102_index_cache',f['cache_module']);qcache=module('frozen102_query_cache',f['query_cache_module'])
        phase='gated_documents';old,new=load_document_pair(f);positions=alignment(old,new)
        if positions!=f['replacement_positions']:raise ValueError('new48 position drift')
        cacheplan=pinned(f['cache_plan'])
        if cacheplan['index']['stable_ids']!=old['stable_ids']or cacheplan['index']['encoder_cache_identity']!=f['encoder_cache_identity']:raise ValueError('index cache identity')
        phase='restore_frozen_vectors';index=cache.restore_index(cacheplan['index'],np)
        queries=pinned(f['development'])['queries'];qvectors,flags=qcache.restore_queries(cacheplan,queries,cache,np)
        if any(flags):raise ValueError('truncated cached query prevents complete comparison')
        phase='model_load'
        from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
        identity=f['encoder_cache_identity']
        encoder=PinnedCPUEncoder(f['model_root'],encoder_manifest=f['encoder_manifest']['path'],encoder_manifest_sha256=f['encoder_manifest']['sha256'],cpu_manifest=f['cpu_manifest']['path'],cpu_manifest_sha256=f['cpu_manifest']['sha256'],native_python_sha256=identity['native_python_sha256'],threads=2,batch_size=4)
        encoder._load();phase='encode_only48_newdocuments'
        delta,receipts=encode_delta(encoder,[new['documents'][i]for i in positions],f,output/'documents-cache',np,cache)
        expanded=install_delta(index.array,positions,delta,np)
        from projects.algorithm_solver.catalogue.empirical_recognition import rank
        from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
        phase='full4081ranking';ids=old['stable_ids'];rank54=[rank(s,ids)for s in qvectors@index.array.T];rank102=[rank(s,ids)for s in qvectors@expanded.T]
        phase='matched_service_comparison';v8=KnownSpecService.from_config(f['historical_service']['path'],f['historical_service']['sha256']);v16=KnownSpecService.from_config(f['matched_service']['path'],f['matched_service']['sha256'])
        policies=pinned(f['policy'])['policy_family'];history=pinned(f['historical_result'])
        results,selected=compare(queries,rank54,rank102,policies,v8,v16,flags,{r['policy']['id']:r for r in history['results']})
        verify(f)
        report={'schema':'gamma.enriched102-cpu-result.v1','status':'completed','freeze_sha256':args.freeze_sha256,'population':4081,'policy_count':20,'query_count':52,
            'document_vector_count':48,'new_encode_document_count':48,'query_encode_document_count':0,'reused_vectors':{'existing_authoritative':54,'remaining_title_only':3979,'queries':52},
            'encoder_identity':encoder.identity(),'delta_receipts':receipts,'results':results,'selected_policies':selected,'historical_baseline_reproduced':True,
            'matched_service_sha256':f['matched_service']['sha256'],'historical_service_sha256':f['historical_service']['sha256'],
            'wall_seconds':time.perf_counter()-start,'cpu_seconds':time.process_time()-cpu0,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'source_availability_ranking_filter':False,'candidate_source_reads':0,'candidate_executions':0,'confirmation_read':False,'recognition_qualified':False,
            'scope':'Development-only representation comparison: document effect102vs54 at identicalv16service; service availability effect54/v16vs54/v8 separately. Authored non-IID data, not independent confirmation.'}
        save(output/'report.json',report);save(output/'progress.json',{'phase':'completed','completed_documents':48})
    except BaseException as error:
        save(output/'failure.json',{'status':'failed','phase':phase,'error_type':type(error).__name__,'freeze_sha256':args.freeze_sha256,'recognition_qualified':False,'candidate_executions':0,'confirmation_read':False})
        raise
    finally:signal.alarm(0)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('freeze','freeze-sha256','output'):p.add_argument('--'+name,required=True)
    run(p.parse_args())
