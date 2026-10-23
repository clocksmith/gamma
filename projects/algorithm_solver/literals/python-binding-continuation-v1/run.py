"""Matched Python scope/global naming; all fit arms seal before validation load."""
import argparse
import concurrent.futures
from contextlib import contextmanager
import copy
import json
import multiprocessing
import os
from pathlib import Path
import resource
import signal
import sys
import time
import graph
from backend import HERE,LIT,analyze,tail,names,body,banned,polish,parent_qualified_sources,write_atomic
from qualification import qualify_one

ARMS=('control','global','global_joint','scope','scope_joint')


@contextmanager
def guarded_pool(n,ctx):
    pool=concurrent.futures.ProcessPoolExecutor(n,mp_context=ctx)
    try:
        yield pool
    except BaseException:
        for child in multiprocessing.active_children():child.terminate()
        raise
    finally:
        pool.shutdown(wait=True,cancel_futures=True)

def contract():return json.loads((HERE/'contract.json').read_text())

def sources(c,ids):
    permitted=set(c['partition']['dev_fit']+c['partition']['dev_val'])
    assert set(ids)<=permitted and len(permitted)==36
    rows={r['id']:r for r in c['sources']};assert set(rows)==permitted
    out={}
    for pid in ids:
        row=rows[pid];raw=Path(row['file']).read_bytes()
        assert analyze.sha(raw)==row['sha256'];out[pid]=raw.decode('utf-8')
    return out

def setup_worker(core):
    c=contract();os.sched_setaffinity(0,{core})
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)

def checked_names(texts,vocab,mode,c):
    output,stats={},{}
    for pid,text in sorted(texts.items()):
        record=graph.record(text)
        candidate,info=names.optimize(text,record,vocab,mode=mode,sweeps=c['rewrite']['sweeps'],max_trials=c['rewrite']['trials'])
        graph.validate_rewrite(text,candidate,record)
        # Parse and body-extract every generated variant before retaining it.
        entry=next(r['entry'] for r in c['sources'] if r['id']==pid)
        body.forbidden(candidate,entry)
        output[pid]=candidate;stats[str(pid)]=info
    return output,stats

def slim(stats):
    out=copy.deepcopy(stats)
    for v in out.values():v.pop('_trace',None)
    return out

def fit_width(job):
    width,out,core=job;setup_worker(core);c=contract();folder=Path(out)/f'w{width}';folder.mkdir()
    fit=sources(c,c['partition']['dev_fit']);entries={r['id']:r['entry'] for r in c['sources']}
    seed_row=c['baseline_dictionaries'][str(width)];raw=Path(seed_row['file']).read_bytes()
    assert analyze.sha(raw)==seed_row['sha256'];seed=json.loads(raw)
    write_atomic(folder/'baseline-dictionary.json',seed);summaries={}
    for name in ARMS:
        vocab=seed;variants={pid:{'original':text} for pid,text in fit.items()};chosen=fit;history=[]
        for round_no in range(2):
            stats={}
            if name!='control':
                new,stats=checked_names(chosen,vocab,'global' if name.startswith('global') else 'scope',c)
                for pid,text in new.items():variants[pid][f'round{round_no}']=text
            state,info=polish(variants,vocab,width,entries,c,name=='control' or name.endswith('_joint'))
            vocab=state['vocab'];chosen={pid:variants[pid][v] for pid,v in state['chosen'].items()}
            info['rewrite']=stats;history.append(info)
            print(json.dumps({'phase':'fit','width':width,'arm':name,'round':round_no,'selections':state['selections'],'stop':info['stop']}),flush=True)
        arm=folder/name;arm.mkdir();write_atomic(arm/'dictionary.json',vocab)
        write_atomic(arm/'fit-sources.json',chosen);write_atomic(arm/'fit-variants.json',variants);write_atomic(arm/'fit-trace.json',history)
        summaries[name]=[{**{k:v for k,v in h.items() if k not in ('trace','rewrite')},'rewrite':slim(h['rewrite'])} for h in history]
    seal={name:{file:analyze.sha((folder/name/file).read_bytes()) for file in ('dictionary.json','fit-sources.json','fit-variants.json')} for name in ARMS}
    write_atomic(folder/'fit-seal.json',{'validation_loaded':False,'arms':seal})
    return {'width':width,'seal_sha256':analyze.sha((folder/'fit-seal.json').read_bytes()),'rounds':summaries}

def validation_width(job):
    width,out,core=job;setup_worker(core);c=contract();out=Path(out);folder=out/f'w{width}'
    allseal=json.loads((out/'all-fit-seal.json').read_text());assert allseal['validation_loaded'] is False
    for w,h in allseal['widths'].items():assert analyze.sha((out/f'w{w}'/'fit-seal.json').read_bytes())==h
    val=sources(c,c['partition']['dev_val']);entries={r['id']:r['entry'] for r in c['sources']};arms=[]
    seal=json.loads((folder/'fit-seal.json').read_text())
    for name in ARMS:
        arm=folder/name
        for file,h in seal['arms'][name].items():assert analyze.sha((arm/file).read_bytes())==h
        vocab=json.loads((arm/'dictionary.json').read_text());fit={int(k):v for k,v in json.loads((arm/'fit-sources.json').read_text()).items()}
        variants={int(k):v for k,v in json.loads((arm/'fit-variants.json').read_text()).items()}
        selected=val;validation_variants={pid:{'original':t} for pid,t in val.items()};stats=[]
        if name!='control':
            for index in range(2):
                selected,info=checked_names(selected,vocab,'global' if name.startswith('global') else 'scope',c);stats.append(info)
                for pid,text in selected.items():validation_variants[pid][f'pass{index}']=text
        write_atomic(arm/'validation-trace.json',stats);write_atomic(arm/'validation-variants.json',validation_variants)
        all_sources={**fit,**selected};write_atomic(arm/'sources.json',all_sources)
        ban=banned({**variants,**validation_variants},entries)
        rows,illegal=tail.evaluate_output(all_sources,vocab,width,ban)
        # Preserve actual private independent packets, not just decode assertions.
        packets=arm/'packets';packets.mkdir();db=analyze.dictionary_bytes(vocab)
        for pid,text in all_sources.items():
            row=rows[str(pid)]
            if row['encodable']:
                sequence=analyze.shortest_encode(text,vocab)
                packet=analyze.encode(vocab,sequence,width)
                assert analyze.decode(db,packet)==text
                (packets/f'{pid}.ltv').write_bytes(packet)
            row['original_sha256']=next(r['sha256'] for r in c['sources'] if r['id']==pid)
        history=json.loads((arm/'fit-trace.json').read_text())
        result={'width':width,'arm':name,'entries':len(vocab),'dictionary_bytes':len(db),
                'dictionary_sha256':seal['arms'][name]['dictionary.json'],'per_problem':rows,'illegal_entry_sha256':illegal,
                'fit':tail.aggregate(rows,c['partition']['dev_fit'],len(db)),
                'validation':tail.aggregate(rows,c['partition']['dev_val'],len(db)),
                'rounds':[{**{k:v for k,v in h.items() if k not in ('trace','rewrite')},'rewrite':slim(h['rewrite'])} for h in history],
                'validation_rewrite':[slim(s) for s in stats]}
        write_atomic(arm/'unqualified-results.json',result);arms.append(result)
    return arms

def qualify_job(job):
    setup_worker(job.pop('core'));return qualify_one(job)

def verify(c):
    assert str(Path(sys.executable).resolve())==c['python_bin']
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    assert c['partition']==json.loads((LIT/'python-name-v1/contract.json').read_text())['partition']
    for row in c['baseline_dictionaries'].values():assert analyze.sha(Path(row['file']).read_bytes())==row['sha256']
    passed=parent_qualified_sources(c)
    assert all((str(row['id']),row['sha256']) in passed for row in c['sources'])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    c=contract()
    if args.verify_only:
        verify(c);print(json.dumps({'verified':True,'corpus_loaded':False}));return
    assert args.output is not None
    args.output.mkdir(parents=True,exist_ok=False);started=time.monotonic();phase='preflight'
    def status(value):
        nonlocal phase
        phase=value;write_atomic(args.output/'status.json',{'phase':phase,'elapsed':time.monotonic()-started,'complete':False})
    def failed(error):
        write_atomic(args.output/'failure.json',{'phase':phase,'elapsed':time.monotonic()-started,'type':type(error).__name__,'error':str(error),'complete':False,'promotion_allowed':False})
    def deadline(signum,frame):
        failed(TimeoutError('overall frozen run deadline'))
        for child in multiprocessing.active_children():child.terminate()
        raise TimeoutError('overall frozen run deadline')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(c['limits']['overall_seconds'])
    try:
        status('preflight');verify(c)
        ctx=multiprocessing.get_context('spawn');jobs=[(w,str(args.output.resolve()),c['search_cores'][i]) for i,w in enumerate((7,8))]
        status('fit')
        with guarded_pool(2,ctx) as pool:fits=list(pool.map(fit_width,jobs))
        write_atomic(args.output/'all-fit-seal.json',{'validation_loaded':False,'widths':{str(x['width']):x['seal_sha256'] for x in fits}})
        status('validation')
        with guarded_pool(2,ctx) as pool:arms=[a for group in pool.map(validation_width,jobs) for a in group]
        write_atomic(args.output/'choices-seal.json',{f'{a["width"]}/{a["arm"]}':analyze.sha((args.output/f'w{a["width"]}'/a['arm']/'sources.json').read_bytes()) for a in arms})
        write_atomic(args.output/'unqualified-results.json',arms)
        specs={str(r['id']):r for r in c['sources']};qjobs={}
        for a in arms:
            texts=json.loads((args.output/f'w{a["width"]}'/a['arm']/'sources.json').read_text())
            for pid,row in a['per_problem'].items():
                if row['source_sha256']!=row['original_sha256']:
                    key=f'{pid}-{row["source_sha256"]}'
                    qjobs[key]={'spec':specs[pid],'source':texts[pid],'folder':str(args.output/'qualification'/key)}
        status('qualification')
        receipts={};write_atomic(args.output/'qualification-private.json',receipts)
        print(json.dumps({'phase':'qualification','distinct_changed':len(qjobs)}),flush=True)
        with guarded_pool(4,ctx) as pool:
            futures={pool.submit(qualify_job,{**job,'core':c['sandbox_cores'][i%4]}):key for i,(key,job) in enumerate(qjobs.items())}
            for f in concurrent.futures.as_completed(futures):
                receipts[futures[f]]=f.result();write_atomic(args.output/'qualification-private.json',receipts)
        passed=parent_qualified_sources(c)
        for a in arms:
            a['qualification']={}
            for pid,row in a['per_problem'].items():
                if row['source_sha256']==row['original_sha256']:
                    assert (pid,row['source_sha256']) in passed
                    q={'passed':True,'reused':True,'receipt_sha256':c['parent_results_sha256']}
                else:q={**{k:v for k,v in receipts[f'{pid}-{row["source_sha256"]}'].items() if k!='failures'},'reused':False}
                a['qualification'][pid]=q
            a['qualified']=sum(q['passed'] for q in a['qualification'].values())
        write_atomic(args.output/'results.json',{'arms':arms,'seconds':time.monotonic()-started,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})
        write_atomic(args.output/'status.json',{'phase':'complete','elapsed':time.monotonic()-started,'complete':True})
        signal.alarm(0);print(json.dumps({'complete':True,'qualified':{f'{a["arm"]}-{2**a["width"]}':a['qualified'] for a in arms}}),flush=True)
    except BaseException as error:
        failed(error)
        for child in multiprocessing.active_children():child.terminate()
        raise
    finally:
        signal.alarm(0)

if __name__=='__main__':main()
