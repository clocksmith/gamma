"""Frozen continuation with and without coupled dictionary-guided name changes."""
import argparse
import concurrent.futures
import json
import multiprocessing
from pathlib import Path
import sys
import time
import shutil
import rewrite

HERE=rewrite.HERE; LIT=HERE.parent; analyze=rewrite.analyze
sys.path.insert(0,str(LIT/'tail-search-v1'))
import search as tail


def source_subset(work,parent,ids):
    return analyze.load_sources(work,{**parent,'sources':[r for r in parent['sources'] if r['id'] in set(ids)]})


def rewrite_all(texts,vocab,mode,limits):
    records=rewrite.records(texts)
    output,stats={},{}
    for pid,text in sorted(texts.items()):
        output[pid],stats[str(pid)]=rewrite.optimize(text,records[str(pid)],vocab,mode=mode,sweeps=limits['sweeps'],max_trials=limits['trials'],rounds=limits['rounds'],proposal_limit=limits['proposal_limit'],state_limit=limits['state_limit'])
    return output,stats


def forbidden(texts):
    records=tail.source_structure(texts)
    return set(texts.values()) | {b for r in records.values() for b in r['bodies']}


def arm(job):
    name,width,work,out=job['arm'],job['width'],Path(job['work']),Path(job['output'])
    c=json.loads((HERE/'contract.json').read_text())
    parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text())
    fit_ids,val_ids=parent['partition']['dev_fit'],parent['partition']['dev_val']
    fit=source_subset(work,parent,fit_ids)
    seedroot=work/c['seed']['relative_path']
    if name in ('control','seed'):
        source=seedroot/('control-256' if name=='control' else 'scope_joint-256')
        shutil.copytree(source,out/f'{name}-256')
        result=json.loads((source/'results.json').read_text());result['arm']=name
        result['historical_replay']=True
        return result
    vocab=json.loads((seedroot/'scope_joint-256/dictionary.json').read_text())
    seedfit={int(k):v for k,v in json.loads((seedroot/'scope_joint-256/fit-sources.json').read_text()).items()}
    assert set(seedfit)==set(fit)
    m=tail.module('coupled_style',LIT/'style150-v2/measure.py');v3=m.v3
    variants={pid:{'original':text,'seed':seedfit[pid]} for pid,text in fit.items()}
    selected=seedfit;history=[];started=time.monotonic()
    mode='coupled' if name.startswith('coupled') else 'ordinary'
    for round_no in range(2):
        rewrite_stats={}
        if True:
            candidates,rewrite_stats=rewrite_all(selected,vocab,mode,c['rewrite'])
            for pid,text in candidates.items():variants[pid][f'rename{round_no}']=text
        banned=set()
        for variant in next(iter(variants.values())):
            banned |= forbidden({pid:v[variant] for pid,v in variants.items()})
        budget=v3.Budget(c['search'])
        state=v3.evaluate(variants,vocab,width,None,budget)
        log=[];stop='fixed_dictionary'
        if name.endswith('_joint'):
            proposer=m.hybrid_chosen([],variants)
            def safe(s,st,limit,fraction):return [x for x in proposer(s,st,limit,fraction) if x not in banned]
            state,_=v3.refill(variants,state,width,safe,c['neighborhood'],24,budget)
            state,stop=v3.local_search(variants,state,width,safe,c['neighborhood'],budget,log)
        vocab=state['vocab']
        selected={pid:variants[pid][v] for pid,v in state['chosen'].items()}
        history.append({'round':round_no,'trials':budget.trials,'stop':stop,'seconds':budget.elapsed(),
                        'selections':state['selections'],'rewrite':rewrite_stats,'trace':log})
        print(json.dumps({'arm':name,'width':width,'round':round_no,'fit_selections':state['selections'],'stop':stop}),flush=True)
    folder=out/f'{name}-{2**width}';folder.mkdir()
    analyze.write(folder/'dictionary.json',vocab)
    analyze.write(folder/'fit-sources.json',selected)
    analyze.write(folder/'fit-variants.json',variants)
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),
                   'fit_sources_sha256':analyze.sha((folder/'fit-sources.json').read_bytes())})
    validation=source_subset(work,parent,val_ids)
    seeds=json.loads((seedroot/'scope_joint-256/sources.json').read_text())
    # Consume only validation IDs after the fit seal. Original and seed remain available.
    seedval={pid:seeds[str(pid)] for pid in val_ids}
    tree=rewrite.codec.trie(vocab)
    key=lambda t:(len(rewrite.codec.encode_text(t,tree)),len(t.encode()),t)
    validation_variants={'original':validation,'seed':seedval}
    validation={pid:min((validation[pid],seedval[pid]),key=key) for pid in val_ids}
    validation, val_stats1=rewrite_all(validation,vocab,mode,c['rewrite'])
    validation_variants['pass1']=validation
    validation, val_stats2=rewrite_all(validation,vocab,mode,c['rewrite'])
    validation_variants['pass2']=validation
    all_sources={**selected,**validation}
    structure=tail.source_structure(all_sources)
    banned=set(all_sources.values())|{b for r in structure.values() for b in r['bodies']}
    for variant in variants.values():
        banned.update(variant.values())
    for group in validation_variants.values():banned |= forbidden(group)
    for variant in next(iter(variants.values())):banned |= forbidden({pid:v[variant] for pid,v in variants.items()})
    rows,illegal=tail.evaluate_output(all_sources,vocab,width,banned,{pid:r['labels'] for pid,r in structure.items()})
    for pid,row in rows.items():row['original_sha256']=next(r['sha256'] for r in parent['sources'] if str(r['id'])==pid)
    analyze.write(folder/'sources.json',all_sources)
    analyze.write(folder/'trace.json',history)
    analyze.write(folder/'validation-trace.json',[val_stats1,val_stats2])
    analyze.write(folder/'validation-variants.json',validation_variants)
    # Names, mappings and rejected-candidate traces stay in the private artifacts.
    for h in history:
        for stats in h['rewrite'].values():stats.pop('_trace',None)
    for group in (val_stats1,val_stats2):
        for stats in group.values():stats.pop('_trace',None)
    db=len(analyze.dictionary_bytes(vocab))
    result={'arm':name,'width':width,'entries':len(vocab),'dictionary_bytes':db,'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),
            'per_problem':rows,'illegal_entry_sha256':illegal,'fit':tail.aggregate(rows,fit_ids,db),'validation':tail.aggregate(rows,val_ids,db),
            'rounds':[{k:v for k,v in h.items() if k!='trace'} for h in history],
            'validation_rewrite':[val_stats1,val_stats2],'seconds':time.monotonic()-started,'historical_replay':False}
    analyze.write(folder/'results.json',result)
    return result


def qualify(work,out,c,results):
    """Test final changed programs only; no candidate repairs or feedback into search."""
    minify=tail.module('name_minify',LIT/'minify-control-v1/minify.py')
    manifest=json.loads((work/'population500/manifest.json').read_text())
    allowed={str(r['id']):r for r in c['qualification']}
    specs={r['id']:r for r in manifest['rows'] if str(r['id']) in allowed}
    jobs={}
    for a in results:
        sources=json.loads((out/f'{a["arm"]}-{2**a["width"]}'/'sources.json').read_text())
        for pid,row in a['per_problem'].items():
            if row['source_sha256']!=row['original_sha256']:
                jobs[int(pid),row['source_sha256']]=sources[pid]
    receipts={}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(minify.style.parity,minify.shim(work),pid,text,'solve',specs[pid],None):(pid,digest)
                 for (pid,digest),text in jobs.items()}
        for f in concurrent.futures.as_completed(futures):
            key=futures[f]; passed,ok,n,bad=f.result()
            # Detailed failures stay private; no case values enter sanitized results.
            receipts[f'{key[0]}:{key[1]}']={'passed':passed,'checks_passed':ok,'cases':n,'failures':bad}
            analyze.write(out/'qualification-private.json',receipts)
    for a in results:
        a['qualification']={}
        for pid,row in a['per_problem'].items():
            changed=row['source_sha256']!=row['original_sha256']
            q=receipts[f'{pid}:{row["source_sha256"]}'] if changed else None
            a['qualification'][pid]=({'passed':q['passed'],'checks_passed':q['checks_passed'],'cases':q['cases'],'reused':False}
                                    if changed else {'passed':True,'reused':True})
        a['qualified']=sum(q['passed'] for q in a['qualification'].values())


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();c=json.loads((HERE/'contract.json').read_text())
    for rel,digest in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==digest,rel
    for path,digest in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==digest,path
    for r in c['qualification']:
        for rel,digest in r['files'].items():assert analyze.sha((a.work/rel).read_bytes())==digest,rel
    for rel,digest in c['seed']['files'].items():assert analyze.sha((a.work/c['seed']['relative_path']/rel).read_bytes())==digest,rel
    assert analyze.sha((a.work/'population500/manifest.json').read_bytes())==c['manifest_sha256']
    a.output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    jobs=[{'arm':n,'width':w,'work':str(a.work.resolve()),'output':str(a.output.resolve())} for w in (8,) for n in ('control','seed','ordinary','coupled','ordinary_joint','coupled_joint')]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
        results=list(pool.map(arm,jobs))
    analyze.write(a.output/'unqualified-results.json',results)
    print('[qualification] final changed sources, four sandbox workers, no retries',flush=True)
    qualify(a.work,a.output,c,results)
    analyze.write(a.output/'results.json',{'arms':results,'seconds':time.monotonic()-started,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})
    print(json.dumps({'complete':True,'qualified':{f'{a["arm"]}-{2**a["width"]}':a['qualified'] for a in results}}),flush=True)


if __name__=='__main__':main()
