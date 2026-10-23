"""Sealed fit-only searches, common validation views, then strict final qualification."""
import argparse
import concurrent.futures
import json
import multiprocessing
import os
from pathlib import Path
import sys
import time
import engine as e

HERE=e.HERE;LIT=e.LIT;analyze=e.analyze
sys.path.insert(0,str(LIT/'tail-search-v1'))
tail=e.module('lns_names_tail',LIT/'tail-search-v1/search.py')
sys.path.insert(0,str(LIT/'coupled-names-v1'))
qualification=e.module('lns_names_qualification',LIT/'coupled-names-v1/run.py')


def subset(work,parent,ids):
    return analyze.load_sources(work,{**parent,'sources':[r for r in parent['sources'] if r['id'] in set(ids)]})


def fit_arm(name,work,out,c):
    parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text())
    original=subset(work,parent,parent['partition']['dev_fit'])
    seedroot=work/c['seed']['relative_path']/'scope_joint-256'
    seed={int(k):v for k,v in json.loads((seedroot/'fit-sources.json').read_text()).items()}
    assert set(seed)==set(original)
    vocab=json.loads((seedroot/'dictionary.json').read_text())
    variants={pid:({'seed':seed[pid]} if name in ('seed','lns_fixed') else {'original':text,'seed':seed[pid]}) for pid,text in original.items()}
    state=e.choose(variants,vocab);initial=state['selections'];history=[];start=time.monotonic()
    folder=out/'fit'/name;folder.mkdir(parents=True)
    if name!='seed':
        for round_no in range(c['rounds']):
            before=state['selections'];stats={}
            if name in ('ordinary','lns_joint'):
                rewritten,stats=e.naming(e.selected(variants,state),state['vocab'],c['rewrite'])
                for pid,text in rewritten.items():variants[pid][f'rename{round_no}']=text
                state=e.choose(variants,state['vocab'])
            named=state['selections'];banned=e.forbidden(variants)
            assert not set(state['vocab'])&banned
            repair=None
            if name.startswith('lns_'):
                state,repair=e.repairs(variants,state,banned,c['repair'],folder/f'round-{round_no}',round_no)
            after_repair=state['selections']
            state,polish=e.polish(variants,state,banned,c['search'],c['neighborhood'])
            assert state['selections']<=named<=before
            history.append({'round':round_no,'before':before,'after_naming':named,'after_repair':after_repair,
                            'after_polish':state['selections'],'rewrite':stats,'repair':repair,'polish':polish})
            print(json.dumps({'arm':name,'round':round_no,'fit_selections':state['selections']}),flush=True)
    final=e.selected(variants,state)
    analyze.write(folder/'dictionary.json',state['vocab']);analyze.write(folder/'fit-sources.json',final)
    analyze.write(folder/'fit-variants.json',variants);analyze.write(folder/'trace.json',history)
    seal={'validation_loaded':False,'files':{p.name:analyze.sha(p.read_bytes()) for p in folder.iterdir() if p.is_file()},
          'fit_selections':state['selections'],'initial_fit_selections':initial}
    analyze.write(folder/'fit-seal.json',seal)
    # Private names and proposals stay in trace.json; sanitized statistics travel separately.
    for h in history:
        for stats in h['rewrite'].values():stats.pop('_trace',None)
        h['polish'].pop('trace',None)
    result={'arm':name,'initial_fit_selections':initial,'fit_selections':state['selections'],
            'rounds':history,'seconds':time.monotonic()-start,'fit_seal_sha256':analyze.sha((folder/'fit-seal.json').read_bytes())}
    analyze.write(folder/'summary.json',result);return result


def batch(job):
    names,cores,work,out,c=job;os.sched_setaffinity(0,set(cores))
    return [fit_arm(n,Path(work),Path(out),c) for n in names]


def validation_views(job):
    name,work,out,c,fit_summary=job;work=Path(work);out=Path(out)
    os.sched_setaffinity(0,set(c['validation_cores']))
    parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text());fit_ids=parent['partition']['dev_fit'];val_ids=parent['partition']['dev_val']
    root=out/'fit'/name;seal=json.loads((root/'fit-seal.json').read_text())
    assert not seal['validation_loaded']
    for file,digest in seal['files'].items():assert analyze.sha((root/file).read_bytes())==digest
    vocab=json.loads((root/'dictionary.json').read_text());fit={int(k):v for k,v in json.loads((root/'fit-sources.json').read_text()).items()}
    fitvariants={int(k):v for k,v in json.loads((root/'fit-variants.json').read_text()).items()}
    original=subset(work,parent,val_ids)
    seedall=json.loads((work/c['seed']['relative_path']/'scope_joint-256/sources.json').read_text())
    seed={pid:seedall[str(pid)] for pid in val_ids}
    variants={pid:{'original':original[pid],'seed':seed[pid]} for pid in val_ids}
    state=e.choose(variants,vocab);stats=[]
    for no in range(c['validation_naming_calls']):
        renamed,trace=e.naming(e.selected(variants,state),vocab,c['rewrite'])
        for pid,text in renamed.items():variants[pid][f'pass{no}']=text
        state=e.choose(variants,vocab);stats.append(trace)
    adaptive=e.selected(variants,state)
    # Both choices sealed before any case execution. No test outcome can alter them.
    analyze.write(root/'validation-variants.json',variants);analyze.write(root/'validation-trace.json',stats)
    analyze.write(root/'validation-seal.json',{'dictionary_sha256':analyze.sha((root/'dictionary.json').read_bytes()),
        'files':{f:analyze.sha((root/f).read_bytes()) for f in ('validation-variants.json','validation-trace.json')},
        'fixed_seed_source_sha256':e.digest_texts(seed),'adaptive_source_sha256':e.digest_texts(adaptive),'qualification_started':False})
    banned=e.forbidden(fitvariants)|e.forbidden(variants)
    for group in stats:
        for st in group.values():st.pop('_trace',None)
    results=[]
    for view,validation in (('fixed_seed',seed),('adaptive',adaptive)):
        label=f'{name}_{view}';folder=out/f'{label}-256';folder.mkdir()
        sources={**fit,**validation};structure=tail.source_structure(sources)
        rows,illegal=tail.evaluate_output(sources,vocab,8,banned,{pid:r['labels'] for pid,r in structure.items()})
        for pid,row in rows.items():row['original_sha256']=next(r['sha256'] for r in parent['sources'] if str(r['id'])==pid)
        analyze.write(folder/'dictionary.json',vocab);analyze.write(folder/'sources.json',sources)
        # Store canonical independently decodable packets, not only aggregate costs.
        (folder/'packets').mkdir();db=analyze.dictionary_bytes(vocab);(folder/'dictionary.bin').write_bytes(db)
        for pid,text in sources.items():
            packet=analyze.encode(vocab,analyze.shortest_encode(text,vocab),8)
            assert analyze.decode(db,packet)==text
            (folder/'packets'/f'{pid}.bin').write_bytes(packet)
        result={'arm':label,'dictionary_arm':name,'view':view,'width':8,'entries':len(vocab),'dictionary_bytes':len(db),
                'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),'dictionary_binary_sha256':analyze.sha(db),
                'per_problem':rows,'illegal_entry_sha256':illegal,'fit':tail.aggregate(rows,fit_ids,len(db)),
                'validation':tail.aggregate(rows,val_ids,len(db)),'fit_search':fit_summary,
                'validation_rewrite':stats if view=='adaptive' else [],
                'validation_seal_sha256':analyze.sha((root/'validation-seal.json').read_bytes())}
        analyze.write(folder/'results.json',result);results.append(result)
    return results


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    c=json.loads((HERE/'contract.json').read_text())
    assert Path(sys.executable).absolute()==Path(c['python_bin']).absolute()
    import platform, numpy, scipy
    assert c['versions']=={'python':platform.python_version(),'numpy':numpy.__version__,'scipy':scipy.__version__}
    assert os.environ.get('OMP_NUM_THREADS')==os.environ.get('OPENBLAS_NUM_THREADS')=='2'
    for rel,digest in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==digest,rel
    for path,digest in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==digest,path
    for r in c['qualification']:
        for rel,digest in r['files'].items():assert analyze.sha((a.work/rel).read_bytes())==digest,rel
    for rel,digest in c['seed']['files'].items():assert analyze.sha((a.work/c['seed']['relative_path']/rel).read_bytes())==digest,rel
    assert analyze.sha((a.work/'population500/manifest.json').read_bytes())==c['manifest_sha256']
    a.output.mkdir(parents=True,exist_ok=False);start=time.monotonic();work=str(a.work.resolve());out=str(a.output.resolve())
    summaries=[fit_arm('seed',a.work,a.output,c)]
    ctx=multiprocessing.get_context('spawn')
    jobs=[(names,cores,work,out,c) for names,cores in ((['ordinary','lns_joint'],c['search_cores'][0]),(['lns_fixed'],c['search_cores'][1]))]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=ctx) as pool:
        for group in pool.map(batch,jobs):summaries.extend(group)
    analyze.write(a.output/'all-fit-sealed.json',{'validation_loaded':False,'arms':summaries})
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=ctx) as pool:
        groups=list(pool.map(validation_views,[(s['arm'],work,out,c,s) for s in summaries]))
    results=[a for group in groups for a in group];analyze.write(a.output/'unqualified-results.json',results)
    print('[qualification] all choices sealed; final sources, four sandbox workers, no retries',flush=True)
    qualification.qualify(a.work,a.output,c,results)
    analyze.write(a.output/'results.json',{'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes()),'arms':results,'seconds':time.monotonic()-start})
    print(json.dumps({'complete':True,'qualified':{a['arm']:a['qualified'] for a in results}}),flush=True)

if __name__=='__main__':main()
