"""Item46 execution: three fixed parents, shared ban barriers, then strict cases."""
import argparse
import concurrent.futures as futures
import multiprocessing
import math
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time
import common as c
import engine as e
import qualification


def limit(config,cores,seconds):
    assert config.get('active') is True and config.get('source_bound') is True,'Inactive/unbound contract'
    if seconds<=0:raise c.HardDeadline('Absolute worker deadline exhausted before input')
    os.sched_setaffinity(0,set(cores))
    size=config['limits']['address_space_bytes'];resource.setrlimit(resource.RLIMIT_AS,(size,size))
    def expired(*_):raise c.HardDeadline('Whole worker deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,seconds)


def seal(folder,name,files,**extra):
    value={'files':{rel:c.hashfile(folder/rel) for rel in files},**extra};c.write(folder/name,value);return value


def verify_seal(folder,name):
    value=c.read(folder/name)
    for rel,digest in value['files'].items():assert c.hashfile(folder/rel)==digest
    return value


def failure(folder,phase,error):
    c.write(folder/'failure.json',{'complete':False,'phase':phase,'error_type':type(error).__name__,'promotion_allowed':False})


def worker(args):
    anchor,phase,out,config,*tail=args;out=Path(out);folder=out/'fit'/anchor;started=time.monotonic()
    remaining=config['limits']['worker_seconds'];core=config['arm_cores'][anchor]
    if phase=='validation':
        assert len(tail)==1 and type(tail[0]) in (int,float) and math.isfinite(tail[0])
        assert tail[0]<=started+remaining
        remaining=min(remaining,tail[0]-time.monotonic())
    else:assert not tail
    limit(config,core,remaining)
    try:
        folder.mkdir(parents=True,exist_ok=True)
        dictionaries={a:c.dictionary(config['work'],a,config) for a in c.ANCHORS};vocab=dictionaries[anchor]
        if phase=='fit':
            texts=c.checked_read(config['work'],config['sources']['fit']);c.check_sources(texts,config['partition']['dev_fit'],config)
            selected_menu=e.menu(texts,vocab)
            c.write(folder/'menu.json',selected_menu)
            result=e.apply(texts,vocab,selected_menu,checkpoint=lambda r:c.write(folder/'fit-partial.json',r),
                           proposal_cap=config['proposal_cap'],phase='fit',dictionaries=dictionaries)
            result['menu']=selected_menu;result['anchor']=anchor
            result['anchor_deadline']=started+config['limits']['worker_seconds']
            result['started_monotonic']=started;result['finished_monotonic']=time.monotonic()
            result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            result['worker_seconds']=result['finished_monotonic']-started
            c.write(folder/'fit.json',result)
            seal(folder,'fit-seal.json',['fit.json','menu.json'],validation_loaded=False)
            return {'anchor':anchor,'seconds':result['worker_seconds'],'anchor_deadline':result['anchor_deadline'],'proposals':result['proposals'],
                    'accepted':result['accepted'],'fit_seal_sha256':c.hashfile(folder/'fit-seal.json')}
        assert phase=='validation' and (out/'all-fit-sealed.json').exists()
        verify_seal(folder,'fit-seal.json');fit=c.read(folder/'fit.json')
        assert tail[0]==fit['anchor_deadline']
        # One absolute per-anchor ceiling spans fit, barrier wait and validation;
        # no finalization or restart gap replenishes the budget.
        limit(config,core,fit['anchor_deadline']-time.monotonic())
        original=c.checked_read(config['work'],config['sources']['all'])
        expected=config['partition']['dev_fit']+config['partition']['dev_val'];c.check_sources(original,expected,config)
        texts={str(pid):original[str(pid)] for pid in config['partition']['dev_val']}
        result=e.apply(texts,vocab,fit['menu'],fit['ledger'],lambda r:c.write(folder/'validation-partial.json',r),
                       config['proposal_cap']-fit['proposals'],'validation',dictionaries)
        result['anchor']=anchor
        # Both views are constructed under the remaining per-anchor worker cap;
        # global legality is resolved by the coordinator before any qualification.
        sources={**fit['selected'],**result['selected']};assert set(sources)==set(original)
        arms=[]
        for suffix,source in (('U',original),('S',sources)):
            arms+=c.prior('run').measure(anchor+'-'+suffix,source,vocab,result['ledger']['banned'],out,config,original)
        result['started_monotonic']=started;result['finished_monotonic']=time.monotonic()
        result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['worker_seconds']=result['finished_monotonic']-started;result['cumulative_worker_seconds']=fit['worker_seconds']+result['worker_seconds']
        assert result['cumulative_worker_seconds']<=config['limits']['worker_seconds']
        c.write(folder/'validation.json',result);c.write(folder/'unqualified-arms.json',arms)
        seal(folder,'validation-seal.json',['validation.json','unqualified-arms.json'],qualification_started=False)
        return {'anchor':anchor,'seconds':result['worker_seconds'],'proposals':result['proposals'],'accepted':result['accepted'],
                'validation_seal_sha256':c.hashfile(folder/'validation-seal.json')}
    except BaseException as error:
        failure(folder,phase,error);raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)


def parallel(jobs):
    pool=futures.ProcessPoolExecutor(max_workers=3,mp_context=multiprocessing.get_context('spawn'))
    try:return list(pool.map(worker,jobs))
    except BaseException:
        pool.terminate_workers();raise
    finally:pool.shutdown(wait=True,cancel_futures=True)


def merge(out,phase,dictionaries):
    ledgers=[]
    for anchor in c.ANCHORS:
        folder=out/'fit'/anchor;verify_seal(folder,phase+'-seal.json')
        data=c.read(folder/(phase+'.json'));assert data['complete'] is True
        ledgers.append((anchor,data['ledger']))
    union=c.global_ledger(ledgers,dictionaries)
    target='global-fit-ledger.json' if phase=='fit' else 'global-ledger.json';c.write(out/target,union)
    if not union['legal']:raise c.LegalityFailure('Shared population ban collision')
    return target


def main(out):
    started=time.monotonic();phase='preflight';out=Path(out);writable=False
    # Fixed guard precedes config/input and is independently backed by supervisor.
    def expired(*_):raise c.HardDeadline('Whole production deadline')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,3600)
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2);os.sched_setaffinity(0,{0,1,2,3})
    try:
        config=c.read(c.HERE/'contract.json');c.verify_public(config)
        assert config['limits']['overall_seconds']==3600 and config['limits']['address_space_bytes']==8*1024**3
        assert config['all_cores']==[0,1,2,3] and config['arm_cores']=={'24':[0],'43N':[1],'43W':[2]}
        assert Path(sys.executable).absolute()==Path(config['python_bin']).absolute() and platform.python_version()==config['python_version']
        assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
        out.mkdir(parents=True,exist_ok=False);writable=True
        c.write(out/'status.json',{'phase':phase,'complete':False})
        dictionaries={anchor:c.dictionary(config['work'],anchor,config) for anchor in c.ANCHORS}
        for anchor,binding in config['dictionaries'].items():
            if binding.get('parent_seal'):
                parent=c.read(Path(config['work'])/binding['parent_seal'])
                assert parent['dictionary_sha256']==binding['sha256'] and parent['validation_loaded'] is False
        phase='fit';c.write(out/'status.json',{'phase':phase,'complete':False})
        fit_summaries=parallel([(anchor,'fit',str(out),config) for anchor in c.ANCHORS])
        globalfit=merge(out,'fit',dictionaries)
        c.write(out/'all-fit-sealed.json',{'validation_loaded':False,'arms':fit_summaries,'global_ledger_sha256':c.hashfile(out/globalfit)})
        # Metadata containing consumed validation is deferred behind this barrier.
        for binding in config.get('deferred_parent_artifacts',[]):c.checked_read(config['work'],binding)
        phase='validation';c.write(out/'status.json',{'phase':phase,'complete':False})
        deadlines={row['anchor']:row['anchor_deadline'] for row in fit_summaries}
        val_summaries=parallel([(anchor,'validation',str(out),config,deadlines[anchor]) for anchor in c.ANCHORS])
        globalval=merge(out,'validation',dictionaries)
        c.write(out/'all-validation-sealed.json',{'qualification_started':False,'arms':val_summaries,'global_ledger_sha256':c.hashfile(out/globalval)})
        arms=[arm for anchor in c.ANCHORS for arm in c.read(out/'fit'/anchor/'unqualified-arms.json')]
        assert len(arms)==12
        phase='qualification';c.write(out/'status.json',{'phase':phase,'complete':False})
        fresh=qualification.qualify(out,config,arms)
        result={'complete':True,'arms':arms,'fit_summaries':fit_summaries,'validation_summaries':val_summaries,
            'fresh_qualification_summary':fresh,'seconds':time.monotonic()-started,'contract_sha256':c.hashfile(c.HERE/'contract.json'),
            'decoded_packets':sum(a['fit']['covered']+a['validation']['covered'] for a in arms),
            'global_ledger_sha256':c.hashfile(out/globalval),'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        c.write(out/'results.json',result);c.write(out/'status.json',{'phase':'complete','complete':True})
        return result
    except BaseException as error:
        if writable:
            try:failure(out,phase,error)
            finally:(out/'results.json').unlink(missing_ok=True)
        raise
    finally:signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.output.resolve())
