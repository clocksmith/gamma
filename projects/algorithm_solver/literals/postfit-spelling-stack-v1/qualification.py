"""Item41 strict execution authority, exact-hash reuse and complete raw receipts."""
import concurrent.futures as futures
import multiprocessing
from pathlib import Path
import signal
import common as c

execute=c.prior('qualification').execute


def job(args):
    work,pid,text,spec,config,core,folder=args
    from run import limit
    limit(config,[core],config['limits']['qualification_seconds'])
    try:return execute(work,pid,text,spec,folder)
    finally:signal.setitimer(signal.ITIMER_REAL,0)


def qualify(out,config,arms):
    assert config.get('active') is True and config.get('source_bound') is True
    assert (out/'all-validation-sealed.json').exists()
    assert c.read(out/'global-ledger.json')['legal'] is True
    work=Path(config['work'])
    assert c.hashfile(work/'population500/manifest.json')==config['manifest_sha256']
    for row in config['qualification']:
        for rel,digest in row['files'].items():assert c.hashfile(work/rel)==digest
    allowed={int(q['id']) for q in config['qualification']}
    specs={int(row['id']):row for row in c.read(work/'population500/manifest.json')['rows'] if int(row['id']) in allowed}
    assert set(specs)==allowed
    known=config['known_receipts'];jobs={}
    for arm in arms:
        texts=c.read(out/'artifacts'/arm['arm']/'sources.json')
        for pid,row in arm['per_problem'].items():
            key=f'{pid}:{row["source_sha256"]}'
            if key not in known:jobs[key]=(int(pid),texts[pid])
    receipt={'expected_keys':sorted(jobs),'receipts':{},'failures':{},'complete':False}
    c.write(out/'qualification-private.json',receipt)
    # One persistent worker queue per core prevents different live workers from
    # accidentally sharing a core merely because completion order differs.
    pools=[];pending={}
    try:
        for core in config['all_cores']:
            pools.append(futures.ProcessPoolExecutor(max_workers=1,mp_context=multiprocessing.get_context('spawn')))
        for i,(key,(pid,text)) in enumerate(sorted(jobs.items())):
            core=config['all_cores'][i%len(pools)]
            args=(str(work),pid,text,specs[pid],config,core,str(out/'raw-qualification'/key.replace(':','-')))
            pending[pools[i%len(pools)].submit(job,args)]=key
        for future in futures.as_completed(pending):
            key=pending[future]
            try:passed,ok,total,bad,rawhash=future.result()
            except BaseException as error:
                receipt['failures'][key]={'error_type':type(error).__name__}
                c.write(out/'qualification-private.json',receipt);raise
            receipt['receipts'][key]={'passed':bool(passed),'checks_passed':ok,'cases':total,'reused':False,
                'raw_receipt':str(Path('raw-qualification')/key.replace(':','-')/'receipt.json'),'raw_receipt_sha256':rawhash}
            if bad or not passed:receipt['failures'][key]=bad or {'passed':False}
            c.write(out/'qualification-private.json',receipt)
    except BaseException:
        for pool in pools:pool.terminate_workers()
        raise
    finally:
        for pool in pools:pool.shutdown(wait=True,cancel_futures=True)
    receipt['complete']=True;c.write(out/'qualification-private.json',receipt)
    for arm in arms:
        arm['qualification']={}
        for pid,row in arm['per_problem'].items():
            key=f'{pid}:{row["source_sha256"]}';q=known.get(key,receipt['receipts'].get(key));assert q is not None
            arm['qualification'][pid]=q;row['qualified_source']=q['passed']
        for name,key in (('fit','dev_fit'),('validation','dev_val')):
            arm[name]=c.prior('metrics').aggregate(arm['per_problem'],config['partition'][key],arm['dictionary_bytes'],config['decoder_dependency_bytes'])
    return {'distinct_new_sources':len(jobs),'passed':sum(r['passed'] for r in receipt['receipts'].values()),
        'checks':sum(r['cases'] for r in receipt['receipts'].values()),'checks_passed':sum(r['checks_passed'] for r in receipt['receipts'].values()),
        'failed_sources':len(receipt['failures'])}
