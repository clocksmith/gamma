"""Native-only persistent CPU recognition/artifact diagnostic; no execution mode."""
import argparse,json,os,resource,signal,sys,time
from pathlib import Path
from artifacts import pinned,sha,check_pin,first_queries,query_identity,restore_index
from pipeline import POLICY,request

HERE=Path(__file__).resolve().parent;BASE=HERE.parent
PROCESS_START=time.perf_counter()

def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n');os.replace(tmp,path)

def memory_available():
    available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))*1024
    maximum=Path('/sys/fs/cgroup/memory.max');current=Path('/sys/fs/cgroup/memory.current')
    if maximum.exists() and current.exists():
        limit=maximum.read_text().strip()
        if limit!='max':available=min(available,int(limit)-int(current.read_text()))
    return available

def verify_code(f):
    for root,key in ((HERE,'code_sha256'),(BASE,'dependency_code_sha256')):
        for name,digest in f[key].items():
            if sha(root/name)!=digest:raise ValueError('code drift')

def run(args):
    output=Path(args.output);output.mkdir(exist_ok=False)
    rows=[];init={};started=time.perf_counter();phase='freeze_validation';active_request=None;cpu0=time.process_time()
    save(output/'progress.json',{'status':'starting','phase':phase,'completed_requests':0})
    try:
        f=pinned({'path':args.freeze,'sha256':args.freeze_sha256})
        if (f['schema']!='gamma.persistent-recognition-timing-freeze.v1' or f['policy']!=POLICY or
            f['passes']!=2 or f['description_requests']!=8 or f['exact_id_requests']!=6 or
            f['exact_ids']!=['leetcode:802','leetcode:875','leetcode:2406'] or f['candidate_executions']!=0):raise ValueError('frozen diagnostic scope')
        budget=f['resources']
        if budget!={'address_space_bytes':8589934592,'batch_size':4,'cpu_hard_seconds':305,'cpu_seconds':300,'minimum_available_memory_bytes':5368709120,'threads':2,'wall_seconds':240}:raise ValueError('resource scope drift')
        resource.setrlimit(resource.RLIMIT_AS,(budget['address_space_bytes'],)*2)
        resource.setrlimit(resource.RLIMIT_CPU,(300,305))
        def terminate(signum,frame):raise TimeoutError('resource or termination signal')
        for signum in (signal.SIGALRM,signal.SIGXCPU,signal.SIGTERM):signal.signal(signum,terminate)
        signal.alarm(240)
        if memory_available()<5*1024**3:raise RuntimeError('insufficient effective memory headroom')
        verify_code(f)
        identity=f['encoder_cache_identity']
        if sha(Path(sys.executable).resolve())!=identity['native_python_sha256'] or Path(sys.executable)!=Path(f['python']):raise ValueError('native private interpreter required')
        check_pin(f['upstream']);check_pin(f['completed_development_result'])
        queries=first_queries(f['development'])
        if query_identity(queries)!=f['query_selection']:raise ValueError('query projection drift')
        init['freeze_and_preflight']=time.perf_counter()-started
        phase='index_initialization';t=time.perf_counter()
        os.environ.update(OPENBLAS_NUM_THREADS='2',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        import numpy as np
        index=restore_index(f,np);init['index_restore_and_import']=time.perf_counter()-t
        phase='service_initialization';t=time.perf_counter()
        from projects.algorithm_solver.catalogue.known_spec_service import KnownSpecService
        service=KnownSpecService.from_config(f['service']['path'],f['service']['sha256'])
        if set(service._universe['eligible_problem_ids'])!=set(f['stable_ids']):raise ValueError('service/index universe mismatch')
        init['service_initialization']=time.perf_counter()-t
        phase='model_initialization';t=time.perf_counter()
        from projects.algorithm_solver.catalogue.cpu_encoder import PinnedCPUEncoder
        encoder=PinnedCPUEncoder(f['model_root'],encoder_manifest=f['encoder_manifest']['path'],encoder_manifest_sha256=f['encoder_manifest']['sha256'],cpu_manifest=f['cpu_manifest']['path'],cpu_manifest_sha256=f['cpu_manifest']['sha256'],native_python_sha256=identity['native_python_sha256'],threads=2,batch_size=4)
        encoder._load()  # Explicit initialization, outside request intervals; no warmup encode.
        init['model_hash_runtime_load']=time.perf_counter()-t
        init['all_initialization']=time.perf_counter()-started
        def record(row):
            rows.append(row)
            with (output/'requests.jsonl').open('a') as stream:
                stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
            save(output/'progress.json',{'status':'running','phase':phase,'completed_requests':len(rows),'total_requests':14,'initialization_seconds':init})
        phase='description_requests'
        for pass_index in range(2):
            for q in queries:
                active_request={'mode':'description','pass_index':pass_index,'query_position':q['position'],'query_id':q['query_id']}
                row=request(service,mode='description',ids=f['stable_ids'],encoder=encoder,index=index,text=q['text'])
                record(dict(row,pass_index=pass_index,query_id=q['query_id'],query_position=q['position'],cold_process_first_query=(pass_index==0 and q['position']==0)))
        phase='exact_id_artifact_controls'
        for pass_index in range(2):
            for pid in f['exact_ids']:
                active_request={'mode':'exact-id-artifact','pass_index':pass_index,'control_id':pid}
                record(dict(request(service,mode='exact-id-artifact',ids=f['stable_ids'],problem_id=pid),pass_index=pass_index,control_id=pid))
        phase='final_code_check';verify_code(f)
        report={'schema':'gamma.persistent-recognition-timing-result.v1','freeze_sha256':args.freeze_sha256,'status':'completed',
            'initialization_seconds':init,'requests':rows,'description_requests':8,'exact_id_requests':6,'candidate_executions':0,
            'first_query_plus_initialization_seconds':init['all_initialization']+rows[0]['timing_seconds']['end_to_end'],
            'second_pass_description_seconds':[r['timing_seconds']['end_to_end'] for r in rows if r['mode']=='description' and r['pass_index']==1],
            'status_counts':{s:sum(r['status']==s for r in rows) for s in ('artifact_returned','abstain','error')},
            'encoder_identity':encoder.identity(),'cpu_seconds':time.process_time()-cpu0,'wall_seconds':time.perf_counter()-started,
            'module_start_to_report_seconds':time.perf_counter()-PROCESS_START,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'cache_state':f['cache_state'],'query_vector_cache':False,'confirmation_read':False,
            'source_availability_ranking_filter':False,'source_bytes_published':False,'recognition_qualified':False,'goal_1c_qualified':False,
            'scope':'Cold process initialization plus first description; persistent subsequent fresh encodes and full4081ranking; dual-language exact artifact bytes materialized and serialized in memory. No candidate execution, network delivery, adaptation or query-public verification.',
            'timing_exclusions':'Interpreter startup before module timer; report IO excluded from request intervals but included in run wall. OS/page cache uncontrolled. No generalized latency estimate from four authored queries.'}
        save(output/'report.json',report);save(output/'progress.json',{'status':'completed','completed_requests':len(rows),'status_counts':report['status_counts']})
    except BaseException as error:
        save(output/'failure.json',{'status':'failed','phase':phase,'error_type':type(error).__name__,
            'completed_requests':len(rows),'active_request':active_request,'initialization_seconds':init,'rows':rows,'recognition_qualified':False,
            'wall_seconds':time.perf_counter()-started,'candidate_executions':0,'source_bytes_published':False})
        raise
    finally:signal.alarm(0)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('freeze','freeze-sha256','output'):p.add_argument('--'+name,required=True)
    run(p.parse_args())
