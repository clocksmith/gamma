"""Frozen scope-naming alternatives with exact source selection and final qualification."""
import argparse
import concurrent.futures
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'tail-search-v1'));import search as tail
analyze=tail.analyze
sys.path.insert(0,str(LIT/'name-search-v1'))
names=tail.module('compiler_qualification_helpers',LIT/'name-search-v1/run.py')


def compile_sources(texts):
    result=subprocess.run(['node',str(HERE/'compile.cjs')],input=json.dumps(texts),text=True,capture_output=True,check=True,timeout=120)
    records=json.loads(result.stdout)
    return {pid:records[str(pid)]['candidates'] for pid in texts},{pid:{'skip':r['skip'],'errors':r['errors'],
        'candidate_count':len(r['candidates']),'binding_stats':r['binding_stats'],'candidate_bytes':{k:len(v.encode()) for k,v in r['candidates'].items()}} for pid,r in records.items()}


def restrict(variants,arm):
    allowed={'original','layout'} if arm=='control' else {'original','layout','default'} if arm=='default' else None
    return {pid:{k:v for k,v in vs.items() if allowed is None or k in allowed} for pid,vs in variants.items()}


def forbidden(variants):
    flat={f'{pid}:{name}':text for pid,vs in variants.items() for name,text in vs.items()}
    records=tail.source_structure(flat)
    return set(flat.values())|{b for r in records.values() for b in r['bodies']}


def arm(job):
    name,width,work,out=job['arm'],job['width'],Path(job['work']),Path(job['output'])
    c=json.loads((HERE/'contract.json').read_text());parent=json.loads((LIT/'cost-decomposition-v1/contract.json').read_text())
    fit_ids,val_ids=parent['partition']['dev_fit'],parent['partition']['dev_val'];started=time.monotonic()
    fit=names.source_subset(work,parent,fit_ids)
    fit_variants,fit_compile=compile_sources(fit)
    banned=forbidden(fit_variants);sources=restrict(fit_variants,name)
    raw=(work/parent['dictionaries'][str(width)]['relative_path']).read_bytes();assert analyze.sha(raw)==parent['dictionaries'][str(width)]['sha256']
    vocab=json.loads(raw);m=tail.module('compiler_choice_style',LIT/'style150-v2/measure.py');v3=m.v3
    budget=v3.Budget(c['search']);state=v3.evaluate(sources,vocab,width,None,budget);trace=[];stop='fixed_dictionary'
    initial_selections=state['selections']
    if name in ('control','joint'):
        base=m.hybrid_chosen([],sources)
        def safe(s,st,limit,fraction):return [x for x in base(s,st,limit,fraction) if x not in banned]
        state,_=v3.refill(sources,state,width,safe,c['neighborhood'],24,budget)
        state,stop=v3.local_search(sources,state,width,safe,c['neighborhood'],budget,trace)
    info={'trials':budget.trials,'seconds':budget.elapsed(),'stop':stop,'rounds':len(trace),'initial_selections':initial_selections}
    vocab=state['vocab'];chosen={pid:sources[pid][v] for pid,v in state['chosen'].items()}
    folder=out/f'{name}-{2**width}';folder.mkdir()
    analyze.write(folder/'dictionary.json',vocab);analyze.write(folder/'fit-sources.json',chosen)
    analyze.write(folder/'fit-variants.json',fit_variants);analyze.write(folder/'trace.json',trace)
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),
        'fit_sources_sha256':analyze.sha((folder/'fit-sources.json').read_bytes()),'fit_variants_sha256':analyze.sha((folder/'fit-variants.json').read_bytes())})
    print(json.dumps({'arm':name,'width':width,'fit_selections':state['selections'],'trials':info['trials'],'stop':stop}),flush=True)
    val=names.source_subset(work,parent,val_ids)
    val_variants,val_compile=compile_sources(val)
    val_sources=restrict(val_variants,name);val_budget=v3.Budget({'trials':1,'seconds':120})
    val_state=v3.evaluate(val_sources,vocab,width,None,val_budget)
    chosen.update({pid:val_sources[pid][v] for pid,v in val_state['chosen'].items()})
    banned|=forbidden(val_variants);structure=tail.source_structure(chosen)
    rows,illegal=tail.evaluate_output(chosen,vocab,width,banned,{pid:r['labels'] for pid,r in structure.items()})
    original={str(r['id']):r['sha256'] for r in parent['sources']};all_choices={**state['chosen'],**val_state['chosen']}
    for pid,row in rows.items():row.update(original_sha256=original[pid],chosen_profile=all_choices[int(pid)])
    analyze.write(folder/'sources.json',chosen);analyze.write(folder/'validation-variants.json',val_variants)
    db=len(analyze.dictionary_bytes(vocab));result={'arm':name,'width':width,'entries':len(vocab),'dictionary_bytes':db,
        'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),'per_problem':rows,'illegal_entry_sha256':illegal,
        'fit':tail.aggregate(rows,fit_ids,db),'validation':tail.aggregate(rows,val_ids,db),'search':info,
        'fit_compiler':fit_compile,'validation_compiler':val_compile,'seconds':time.monotonic()-started}
    analyze.write(folder/'results.json',result);return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    for row in c['qualification']:
        for path,h in row['files'].items():assert analyze.sha((a.work/path).read_bytes())==h,path
    assert analyze.sha((a.work/'population500/manifest.json').read_bytes())==c['manifest_sha256']
    a.output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    jobs=[{'arm':n,'width':w,'work':str(a.work.resolve()),'output':str(a.output.resolve())} for w in (7,8) for n in ('control','default','select','joint')]
    with concurrent.futures.ProcessPoolExecutor(4,mp_context=multiprocessing.get_context('spawn')) as pool:results=list(pool.map(arm,jobs))
    analyze.write(a.output/'unqualified-results.json',results)
    print('[qualification] final changed sources, four sandbox workers, no retries',flush=True)
    names.qualify(a.work,a.output,c,results)
    analyze.write(a.output/'results.json',{'arms':results,'seconds':time.monotonic()-started,'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})
    print(json.dumps({'complete':True,'qualified':{f'{r["arm"]}-{2**r["width"]}':r['qualified'] for r in results}}),flush=True)


if __name__=='__main__':main()
