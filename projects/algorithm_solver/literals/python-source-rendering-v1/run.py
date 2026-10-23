"""Eight sealed U/S/D/J arms; finite qualification only after every choice seal."""
import argparse
import concurrent.futures
import json
import multiprocessing
import os
from pathlib import Path
import resource
import signal
import time
from common import (HERE,engine,render,analyze,write,sha,contract,verify,checked,texts_checked,authority,
                    identity,variants_for,evaluate,save_packets,seal_files,check_files)
import qualification

FIT_FILES=('dictionary.json','fit-sources.json','fit-variants.json','fit-menus.json','fit-record.json')
CHOICE_FILES=('dictionary.json','sources.json','validation-variants.json','validation-menus.json','validation-choices.json','unqualified-results.json')

def setup(core,c,seconds):
    os.sched_setaffinity(0,{core});resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)
    def timeout(signum,frame):raise TimeoutError('frozen worker deadline')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(seconds)

def fit(job):
    width,name,out,core=job;c=contract();setup(core,c,c['limits']['fit_seconds']);started=time.monotonic()
    folder=Path(out)/identity(width,name);folder.mkdir(parents=True)
    texts=texts_checked(c,width,fit_only=True);entries={pid:c['entries'][pid] for pid in texts}
    seed=checked(c['inputs'][str(width)]['seed_dictionary'])
    record=engine.fit_arm_supplied(texts,seed,width,entries,c,name)
    write(folder/'dictionary.json',record['dictionary']);write(folder/'fit-sources.json',record['fit_sources'])
    write(folder/'fit-variants.json',record['variants']);write(folder/'fit-menus.json',record['menus'])
    write(folder/'fit-record.json',{key:value for key,value in record.items() if key not in ('dictionary','fit_sources','variants','menus','all_menu_bans')})
    seal={'width':width,'arm':name,'validation_loaded':False,'case_data_loaded':False,'files':seal_files(folder,FIT_FILES)}
    write(folder/'fit-seal.json',seal)
    result={'width':width,'arm':name,'fit_seal_sha256':sha((folder/'fit-seal.json').read_bytes()),'elapsed':time.monotonic()-started}
    print(json.dumps({'phase':'fit_complete',**result}),flush=True);return result

def check_all_fit(out):
    sealed=json.loads((out/'all-fit-seal.json').read_text())
    assert sealed['validation_loaded'] is False and sealed['case_data_loaded'] is False
    keys={identity(w,n) for w in (7,8) for n in engine.ARMS}
    assert len(sealed['arms'])==8 and set(sealed['arms'])==keys
    for key,summary in sealed['arms'].items():
        assert key==identity(summary['width'],summary['arm'])
        folder=out/key;assert sha((folder/'fit-seal.json').read_bytes())==summary['fit_seal_sha256']
        seal=json.loads((folder/'fit-seal.json').read_text());assert set(seal['files'])==set(FIT_FILES)
        assert seal['width']==summary['width'] and seal['arm']==summary['arm']
        assert seal['validation_loaded'] is False and seal['case_data_loaded'] is False
        check_files(folder,seal['files'])
    return sealed

def validation(job):
    width,name,out,core=job;c=contract();setup(core,c,c['limits']['validation_seconds']);out=Path(out)
    check_all_fit(out);folder=out/identity(width,name)
    parent=texts_checked(c,width);val={str(pid):parent[str(pid)] for pid in c['partition']['dev_val']}
    assert {pid:parent[pid] for pid in map(str,c['partition']['dev_fit'])}==texts_checked(c,width,fit_only=True)
    vocab=json.loads((folder/'dictionary.json').read_text())
    groups,menus=engine.source_menus(val);variants=variants_for(name,val,groups)
    selected,trace=engine.choose(val,variants,vocab,width)
    fit_sources=json.loads((folder/'fit-sources.json').read_text());sources={**fit_sources,**selected}
    fit_menus=json.loads((folder/'fit-menus.json').read_text());allmenus={**fit_menus,**menus}
    write(folder/'sources.json',sources);write(folder/'validation-variants.json',variants)
    write(folder/'validation-menus.json',menus);write(folder/'validation-choices.json',trace)
    result=evaluate(sources,vocab,width,c,allmenus);result.update(arm=name,source_choice_count=sum(sources[p]!=parent[p] for p in sources))
    save_packets(folder,sources,vocab,width);write(folder/'unqualified-results.json',result)
    write(folder/'choices-seal.json',{'case_data_loaded':False,'files':seal_files(folder,CHOICE_FILES)})
    return {'width':width,'arm':name,'choices_seal_sha256':sha((folder/'choices-seal.json').read_bytes())}

def reference(width,out,c):
    folder=out/f'w{width}'/'R';folder.mkdir()
    texts=texts_checked(c,width,original=True);vocab=checked(c['inputs'][str(width)]['baseline_dictionary'])
    menus={pid:{'candidates':{'original':text}} for pid,text in texts.items()}
    result=evaluate(texts,vocab,width,c,menus);result.update(arm='R',source_choice_count=0)
    write(folder/'sources.json',texts);write(folder/'dictionary.json',vocab);save_packets(folder,texts,vocab,width)
    write(folder/'unqualified-results.json',result)
    return seal_files(folder,('sources.json','dictionary.json','unqualified-results.json'))

def qworker(jobs,c,core):
    setup(core,c,c['limits']['qualification_seconds']);completed={}
    for key,job in jobs:
        completed[key]=qualification.qualify_one(job,c)
        print(json.dumps({'phase':'qualified','key':key,'passed':completed[key]['passed']}),flush=True)
    return completed

def pool_map(function,jobs,count):
    pool=concurrent.futures.ProcessPoolExecutor(count,mp_context=multiprocessing.get_context('spawn'))
    try:return list(pool.map(function,jobs))
    except BaseException:
        for child in multiprocessing.active_children():child.terminate()
        raise
    finally:pool.shutdown(wait=True,cancel_futures=True)

def qgroup(job):return qworker(*job)

def run(output,c):
    resource.setrlimit(resource.RLIMIT_AS,(c['limits']['address_space_bytes'],)*2)
    output.mkdir(parents=True,exist_ok=False);started=time.monotonic();phase='preflight'
    def status(value):
        nonlocal phase
        phase=value;write(output/'status.json',{'phase':phase,'complete':False,'elapsed':time.monotonic()-started})
    def deadline(signum,frame):raise TimeoutError('frozen overall deadline')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(c['overall_seconds'])
    try:
        verify(c);write(output/'run-binding.json',{'contract_sha256':sha((HERE/'contract.json').read_bytes())})
        jobs=[(w,n,str(output.resolve()),c['cores'][i]) for i,(w,n) in enumerate((w,n) for w in (7,8) for n in engine.ARMS)]
        status('fit');fit_summaries=pool_map(fit,jobs,8)
        write(output/'all-fit-seal.json',{'validation_loaded':False,'case_data_loaded':False,
              'arms':{identity(s['width'],s['arm']):s for s in fit_summaries}})
        status('validation');summaries=pool_map(validation,jobs,8)
        refs={str(w):reference(w,output,c) for w in (7,8)}
        write(output/'all-choices-seal.json',{'case_data_loaded':False,'all_fit_seal_sha256':sha((output/'all-fit-seal.json').read_bytes()),
              'arms':{identity(s['width'],s['arm']):s for s in summaries},'references':refs})
        specs={str(row['id']):row for row in c['sources']};qjobs={}
        for width,name,_,_ in jobs:
            folder=output/identity(width,name);texts=json.loads((folder/'sources.json').read_text());old=texts_checked(c,width)
            for pid,text in texts.items():
                if text!=old[pid]:
                    key=f'{pid}-{sha(text.encode())}'
                    qjobs[key]={'spec':specs[pid],'source':text,'folder':str(output/'qualification'/key)}
        write(output/'qualification-plan.json',{'all_choices_seal_sha256':sha((output/'all-choices-seal.json').read_bytes()),
              'keys':sorted(qjobs),'new_sources':len(qjobs),'cases':sum(j['spec']['cases'] for j in qjobs.values())})
        status('qualification')
        groups=[[] for _ in c['qualification_cores']]
        for i,item in enumerate(sorted(qjobs.items())):groups[i%len(groups)].append(item)
        allq=pool_map(qgroup,[(group,c,core) for group,core in zip(groups,c['qualification_cores'])],4)
        receipts={key:value for group in allq for key,value in group.items()};assert set(receipts)==set(qjobs)
        write(output/'qualification-private.json',receipts)
        arms=[]
        for width in (7,8):
            for name in (*engine.ARMS,'R'):
                folder=output/f'w{width}'/name;a=json.loads((folder/'unqualified-results.json').read_text())
                parent=texts_checked(c,width,original=name=='R');a['qualification']={}
                for pid,row in a['per_problem'].items():
                    key=f'{pid}-{row["source_sha256"]}'
                    if row['source_sha256']==sha(parent[pid].encode()):
                        q={'passed':True,'reused':True,'receipt_sha256':c['qualification']['sha256']}
                    else:
                        r=receipts[key];q={'passed':r['passed'],'reused':False,'checks_passed':r['checks_passed'],'cases':r['cases'],
                            'receipt_sha256':sha((output/'qualification'/key/'receipt.json').read_bytes())}
                    a['qualification'][pid]=q
                a['qualified']=sum(q['passed'] for q in a['qualification'].values());arms.append(a)
        write(output/'results.json',{'contract_sha256':sha((HERE/'contract.json').read_bytes()),'arms':arms,'elapsed':time.monotonic()-started,
              'fresh_sources':len(receipts),'fresh_cases':sum(q['cases'] for q in receipts.values())})
        write(output/'status.json',{'phase':'complete','complete':True,'elapsed':time.monotonic()-started})
    except BaseException as error:
        write(output/'failure.json',{'phase':phase,'error_type':type(error).__name__,'complete':False,'promotion_allowed':False})
        for child in multiprocessing.active_children():child.terminate()
        raise
    finally:signal.alarm(0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);ap.add_argument('--verify-only',action='store_true');args=ap.parse_args()
    c=contract()
    if args.verify_only:verify(c);print(json.dumps({'verified':True,'private_content_read':False}));return
    assert args.output is not None;run(args.output,c)
if __name__=='__main__':main()
