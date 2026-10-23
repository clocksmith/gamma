"""Frozen execution only: public preflight, fit seals, validation seals, strict parity."""
import argparse
import concurrent.futures as futures
import multiprocessing
import os
from pathlib import Path
import platform
import resource
import signal
import sys
import time
import core as c
import engine as e
import metrics as m
import qualification

HERE,LIT=c.HERE,c.LIT

def status(out,phase,complete=False):c.write(out/'status.json',{'phase':phase,'complete':complete})
def hashfile(path):return c.sha(Path(path).read_bytes())
def verify_seal(folder,name):
    seal=c.read(folder/name)
    for rel,digest in seal['files'].items():assert hashfile(folder/rel)==digest,(folder,rel)
    return seal

def seal(folder,name,files,**extra):
    value={'files':{rel:hashfile(folder/rel) for rel in files},**extra};c.write(folder/name,value);return value

def limit(config,cores):
    assert config.get('active') is True,'Inactive execution contract'
    os.sched_setaffinity(0,set(cores))
    size=config['limits']['address_space_bytes'];resource.setrlimit(resource.RLIMIT_AS,(size,size))
    def expired(signum,frame):raise c.HardDeadline('Hard worker deadline includes input loading and finalization')
    signal.signal(signal.SIGALRM,expired);signal.alarm(config['limits']['worker_seconds'])

def check_sources(texts,ids,config):
    assert set(texts)==set(map(str,ids))
    for pid,text in texts.items():assert c.sha(text.encode())==config['source_qualification'][pid]['source_sha256']

def fit_job(job):
    arm,output,config,cores=job;out=Path(output);folder=out/'fit'/arm
    limit(config,cores);folder.mkdir(parents=True)
    try:
        source=Path(config['source_run'])
        texts=c.read(source/'fit/D11/fit-sources.json');check_sources(texts,config['partition']['dev_fit'],config)
        vocab=c.read(source/config['initial_dictionary']['path'])
        assert c.order(vocab)==vocab and len(vocab)==config['initial_dictionary']['entries']
        assert sum(len(w)==1 for w in vocab)==config['initial_dictionary']['character_entries']
        names=c.names(vocab,c.rewrite.records(texts))
        result=e.optimize(texts,vocab,names,arm,config['search'],lambda r:c.write(folder/'partial.json',r))
        c.write(folder/'fit.json',result)
        seal(folder,'fit-seal.json',['fit.json'],validation_loaded=False)
        return {'arm':arm,**{k:result[k] for k in ('trials','rounds','stop','seconds','overrun_seconds','trial_composition','coverage_failures')},
                'fit_seal_sha256':hashfile(folder/'fit-seal.json')}
    except BaseException as error:
        c.write(folder/'failure.json',{'complete':False,'phase':'fit','error_type':type(error).__name__,'error':str(error),'promotion_allowed':False});raise
    finally:signal.alarm(0)

def val_job(job):
    arm,output,config,cores=job;out=Path(output);folder=out/'fit'/arm
    limit(config,cores)
    try:
        verify_seal(folder,'fit-seal.json');fit=c.read(folder/'fit.json')
        allsources=c.read(Path(config['source_run'])/'artifacts/D11/sources.json')
        texts={str(pid):allsources[str(pid)] for pid in config['partition']['dev_val']};check_sources(texts,config['partition']['dev_val'],config)
        result=e.validation(texts,fit['state']['vocab'],fit['names'],fit['final_contexts'],fit['ledger'],arm,
                            lambda r:c.write(folder/'validation-partial.json',r))
        c.write(folder/'validation.json',result)
        seal(folder,'validation-seal.json',['validation.json'],qualification_started=False)
        return {'arm':arm,'validation_seal_sha256':hashfile(folder/'validation-seal.json')}
    except BaseException as error:
        c.write(folder/'failure.json',{'complete':False,'phase':'validation','error_type':type(error).__name__,'error':str(error),'promotion_allowed':False});raise
    finally:signal.alarm(0)

def parallel(function,jobs):
    pool=futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn'))
    try:
        return list(pool.map(function,jobs))
    except BaseException:
        pool.terminate_workers();raise
    finally:pool.shutdown(wait=True,cancel_futures=True)

def measure(arm,sources,vocab,forbidden,out,config,original):
    folder=out/'artifacts'/arm;folder.mkdir(parents=True)
    c.write(folder/'sources.json',sources);c.write(folder/'dictionary.json',vocab)
    db=c.analyze.dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(db)
    metadata=m.spelling(sources);results=[]
    for policy in m.POLICIES:
        packets=folder/policy;packets.mkdir();rows={}
        for pid,text in sorted(sources.items()):
            row={'source_sha256':c.sha(text.encode()),'source_bytes':len(text.encode()),
                 'source_byte_delta':len(text.encode())-len(original[pid].encode())}
            try:seq=c.segment.encode(text,vocab,policy)
            except ValueError:row['encodable']=False
            else:
                packet=c.analyze.encode(vocab,seq,8);assert c.analyze.decode(db,packet)==text
                if policy=='canonical':assert seq==c.analyze.shortest_encode(text,vocab)
                (packets/f'{pid}.bin').write_bytes(packet)
                row.update(encodable=True,selections=len(seq),actions=len(seq)+1,single_characters=sum(len(vocab[i])==1 for i in seq),
                           packet_bytes=len(packet),packet_sha256=c.sha(packet),one_program_package_bytes=len(db)+len(packet),
                           one_program_package_with_decoder_dependencies=len(db)+len(packet)+config['decoder_dependency_bytes'])
            rows[pid]=row
        results.append({'arm':arm,'policy':policy,'width':8,'entries':len(vocab),'character_entries':sum(len(w)==1 for w in vocab),
                        'dictionary_bytes':len(db),'dictionary_sha256':hashfile(folder/'dictionary.json'),'dictionary_binary_sha256':c.sha(db),
                        'illegal_entry_sha256':sorted(c.sha(w.encode()) for w in set(vocab)&set(forbidden)),
                        'spelling':metadata,'per_problem':rows})
    return results

def parity_job(job):
    work,pid,text,spec,config,cores,rawfolder=job;limit(config,cores)
    try:
        return qualification.execute(work,pid,text,spec,rawfolder)
    finally:signal.alarm(0)

def qualify(work,out,config,arms):
    # This is the first access to test contents or baseline observations, after
    # every final source choice has been sealed. No all-population source loader.
    assert config.get('active') is True,'Inactive execution contract'
    assert (out/'all-validation-sealed.json').exists()
    assert hashfile(work/'population500/manifest.json')==config['manifest_sha256']
    for q in config['qualification']:
        for rel,digest in q['files'].items():assert hashfile(work/rel)==digest,rel
    allowed={int(q['id']) for q in config['qualification']}
    manifest=c.read(work/'population500/manifest.json')
    specs={int(row['id']):row for row in manifest['rows'] if int(row['id']) in allowed}
    assert set(specs)==allowed
    known=config['known_receipts'];jobs={}
    for arm in arms:
        texts=c.read(out/'artifacts'/arm['arm']/'sources.json')
        for pid,row in arm['per_problem'].items():
            key=f'{pid}:{row["source_sha256"]}'
            if key not in known:jobs[key]=(int(pid),texts[pid])
    receipt={'expected_keys':sorted(jobs),'receipts':{},'failures':{},'complete':False}
    c.write(out/'qualification-private.json',receipt)
    pool=futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn'))
    try:
        pending={pool.submit(parity_job,(str(work),pid,text,specs[pid],config,config['cores'][i%4],str(out/'raw-qualification'/key.replace(':','-')))):key
                 for i,(key,(pid,text)) in enumerate(jobs.items())}
        for future in futures.as_completed(pending):
            key=pending[future]
            try:passed,ok,total,bad,rawhash=future.result()
            except BaseException as error:
                receipt['failures'][key]={'error_type':type(error).__name__,'error':str(error)};c.write(out/'qualification-private.json',receipt);raise
            receipt['receipts'][key]={'passed':bool(passed),'checks_passed':ok,'cases':total,'reused':False,
                                        'raw_receipt':str(Path('raw-qualification')/key.replace(':','-')/'receipt.json'),'raw_receipt_sha256':rawhash}
            if bad or not passed:receipt['failures'][key]=bad or {'passed':False}
            c.write(out/'qualification-private.json',receipt)
    except BaseException:
        pool.terminate_workers();raise
    finally:pool.shutdown(wait=True,cancel_futures=True)
    receipt['complete']=True;c.write(out/'qualification-private.json',receipt)
    for arm in arms:
        arm['qualification']={}
        for pid,row in arm['per_problem'].items():
            key=f'{pid}:{row["source_sha256"]}';q=known.get(key,receipt['receipts'].get(key));assert q is not None
            arm['qualification'][pid]=q;row['qualified_source']=q['passed']
        for name,key in (('fit','dev_fit'),('validation','dev_val')):
            arm[name]=m.aggregate(arm['per_problem'],config['partition'][key],arm['dictionary_bytes'],config['decoder_dependency_bytes'])
    return {'distinct_new_sources':len(jobs),'passed':sum(r['passed'] for r in receipt['receipts'].values()),
            'checks':sum(r['cases'] for r in receipt['receipts'].values()),'checks_passed':sum(r['checks_passed'] for r in receipt['receipts'].values()),
            'failed_sources':len(receipt['failures'])}

def verify_public(config):
    assert config.get('active') is True,'Inactive execution contract'
    for rel,digest in config['code_hashes'].items():assert hashfile(LIT/rel)==digest,rel
    for path,digest in config['runtime_files'].items():assert hashfile(path)==digest,path

def main(source_run,out):
    config=c.read(HERE/'contract.json');assert config.get('active') is True,'Inactive execution contract'
    assert str(source_run)==config['source_run']
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic();status(out,'preflight')
    assert Path(sys.executable).absolute()==Path(config['python_bin']).absolute() and platform.python_version()==config['python_version']
    assert os.environ.get('OMP_NUM_THREADS')==os.environ.get('OPENBLAS_NUM_THREADS')=='1'
    size=config['limits']['address_space_bytes'];resource.setrlimit(resource.RLIMIT_AS,(size,size))
    verify_public(config)
    deferred='artifacts/D11/sources.json'
    for rel,digest in config['source_carrier']['private_files'].items():
        if rel!=deferred:assert hashfile(source_run/rel)==digest,rel
    assert hashfile(source_run/config['initial_dictionary']['path'])==config['initial_dictionary']['sha256']
    initial=c.read(source_run/config['initial_dictionary']['path'])
    assert c.sha(c.analyze.dictionary_bytes(initial))==config['initial_dictionary']['binary_sha256']
    jobs=[(arm,str(out),config,cores) for arm,cores in zip(e.ARMS,config['cores'])]
    status(out,'fit');summaries=parallel(fit_job,jobs)
    for arm in e.ARMS:verify_seal(out/'fit'/arm,'fit-seal.json')
    name_lists=[c.read(out/'fit'/arm/'fit.json')['names'] for arm in e.ARMS];assert all(x==name_lists[0] for x in name_lists)
    c.write(out/'all-fit-sealed.json',{'validation_loaded':False,'arms':summaries})
    status(out,'validation')
    assert hashfile(source_run/deferred)==config['source_carrier']['private_files'][deferred]
    vals=parallel(val_job,jobs)
    for arm in e.ARMS:verify_seal(out/'fit'/arm,'validation-seal.json')
    c.write(out/'all-validation-sealed.json',{'qualification_started':False,'arms':vals})
    original=c.read(source_run/deferred);expected=[i for ids in config['partition'].values() for i in ids];check_sources(original,expected,config)
    status(out,'measure');arms=measure('D10',original,initial,c.banned(original),out,config,original)
    for arm in e.ARMS:
        folder=out/'fit'/arm;fit=c.read(folder/'fit.json');val=c.read(folder/'validation.json')
        texts={**fit['state']['sources'],**val['selected']};assert set(texts)==set(original)
        arms+=measure(arm,texts,fit['state']['vocab'],val['ledger']['banned'],out,config,original)
    c.write(out/'unqualified-results.json',arms)
    status(out,'qualification');fresh=qualify(Path(config['work']),out,config,arms)
    result={'arms':arms,'fit_summaries':summaries,'fresh_qualification_summary':fresh,'seconds':time.monotonic()-start,
            'contract_sha256':hashfile(HERE/'contract.json'),'decoded_packets':sum(a['fit']['covered']+a['validation']['covered'] for a in arms)}
    c.write(out/'results.json',result);status(out,'complete',True)
    print(c.canonical({'complete':True,'decoded_packets':result['decoded_packets'],'qualification':fresh}),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-run',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():parser.error('Refuse existing output directory; retained runs are immutable')
    try:main(args.source_run.resolve(),args.output.resolve())
    except BaseException as error:
        if args.output.exists():c.write(args.output/'failure.json',{'complete':False,'promotion_allowed':False,'phase':c.read(args.output/'status.json')['phase'],
                'error_type':type(error).__name__,'error':str(error)})
        raise
