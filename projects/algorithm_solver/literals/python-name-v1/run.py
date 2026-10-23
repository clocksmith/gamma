"""Python-only transfer of vocabulary-aware naming on an allowlisted panel."""
import argparse
import concurrent.futures
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import time
import bindings

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'name-search-v1'))
import rewrite
analyze=rewrite.analyze
sys.path.insert(0,str(LIT/'tail-search-v1'))
import search as tail
sys.path.insert(0,str(LIT.parent))
from algsolve.judge import sandbox
from algsolve.judge.judge import FunctionalTest,_matches


def sources(c,ids):
    out={}
    for row in c['sources']:
        if row['id'] in ids:
            raw=Path(row['file']).read_bytes();assert analyze.sha(raw)==row['sha256']
            out[row['id']]=raw.decode('utf-8')
    assert set(out)==set(ids)
    return out


def banned(sources,entries):
    return {s for pid,vs in sources.items() for text in vs.values() for s in bindings.forbidden(text,entries[pid])}


def optimize_names(texts,vocab):
    output,stats={},{}
    for pid,text in sorted(texts.items()):
        output[pid],stats[str(pid)]=rewrite.optimize(text,bindings.record(text),vocab,sweeps=2)
    return output,stats


def polish(variants,vocab,width,entries,m,c,enabled):
    ban=banned(variants,entries);budget=m.v3.Budget(c['search'])
    state=m.v3.evaluate(variants,vocab,width,None,budget);log=[];stop='fixed_dictionary'
    if enabled:
        proposer=m.hybrid_chosen([],variants)
        def safe(s,st,limit,fraction):return [p for p in proposer(s,st,limit,fraction) if p not in ban]
        state,_=m.v3.refill(variants,state,width,safe,c['neighborhood'],24,budget)
        state,stop=m.v3.local_search(variants,state,width,safe,c['neighborhood'],budget,log)
    return state,{'trials':budget.trials,'stop':stop,'seconds':budget.elapsed(),'selections':state['selections'],'trace':log}


def width_job(job):
    width,out=job['width'],Path(job['output']);c=json.loads((HERE/'contract.json').read_text())
    fit_ids,val_ids=c['partition']['dev_fit'],c['partition']['dev_val'];entries={r['id']:r['entry'] for r in c['sources']}
    fit=sources(c,fit_ids);m=tail.module('python_name_style',LIT/'style150-v2/measure.py')
    variants={pid:{'original':t} for pid,t in fit.items()}
    started=time.monotonic()
    seed,seed_info=polish(variants,list(m.joint.base.ALPHABET),width,entries,m,c,True)
    folder=out/f'w{width}';folder.mkdir()
    analyze.write(folder/'baseline-dictionary.json',seed['vocab']);analyze.write(folder/'baseline-trace.json',seed_info)
    print(json.dumps({'width':width,'phase':'baseline_fit','selections':seed['selections'],'stop':seed_info['stop']}),flush=True)
    fitted={}
    for name in ('control','rename','joint'):
        variants={pid:{'original':t} for pid,t in fit.items()};chosen=fit;vocab=seed['vocab'];history=[]
        for i in range(2):
            stats={}
            if name!='control':
                renamed,stats=optimize_names(chosen,vocab)
                for pid,text in renamed.items():variants[pid][f'rename{i}']=text
            state,info=polish(variants,vocab,width,entries,m,c,name!='rename')
            info['rewrite']=stats;history.append(info);vocab=state['vocab']
            chosen={pid:variants[pid][variant] for pid,variant in state['chosen'].items()}
        arm=folder/name;arm.mkdir()
        analyze.write(arm/'dictionary.json',vocab);analyze.write(arm/'fit-sources.json',chosen)
        analyze.write(arm/'fit-variants.json',variants);analyze.write(arm/'trace.json',history)
        for h in history:
            h.pop('trace',None)
            for stat in h['rewrite'].values():stat.pop('_trace',None)
        fitted[name]=(vocab,chosen,history)
    seal={name:{f:analyze.sha((folder/name/f).read_bytes()) for f in ('dictionary.json','fit-sources.json')} for name in fitted}
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'arms':seal})
    # No validation text is opened until every fit decision of this width is sealed.
    val=sources(c,val_ids);results=[]
    for name,(vocab,chosen,history) in fitted.items():
        validation=val;vstats=[];vvariants={'original':val}
        if name!='control':
            for i in range(2):
                validation,stats=optimize_names(validation,vocab);vstats.append(stats);vvariants[f'pass{i}']=validation
        arm=folder/name;all_sources={**chosen,**validation}
        analyze.write(arm/'validation-trace.json',vstats);analyze.write(arm/'validation-variants.json',vvariants)
        for group in vstats:
            for stats in group.values():stats.pop('_trace',None)
        rows,illegal=tail.evaluate_output(all_sources,vocab,width,banned({pid:{'selected':t} for pid,t in all_sources.items()},entries))
        for pid,row in rows.items():row['original_sha256']=next(x['sha256'] for x in c['sources'] if str(x['id'])==pid)
        analyze.write(arm/'sources.json',all_sources)
        db=len(analyze.dictionary_bytes(vocab));result={'width':width,'arm':name,'entries':len(vocab),'dictionary_bytes':db,
            'dictionary_sha256':seal[name]['dictionary.json'],'per_problem':rows,'illegal_entry_sha256':illegal,
            'fit':tail.aggregate(rows,fit_ids,db),'validation':tail.aggregate(rows,val_ids,db),'rounds':history,'validation_rewrite':vstats}
        analyze.write(arm/'results.json',result);results.append(result)
    return {'width':width,'baseline':{k:v for k,v in seed_info.items() if k!='trace'},'arms':results,'seconds':time.monotonic()-started}


def strict(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise ValueError('duplicate key')
        out[k]=v
    return out


def parse(data,n):
    rows=[json.loads(line,object_pairs_hook=strict,parse_constant=lambda x:(_ for _ in ()).throw(ValueError(x))) for line in data.splitlines()]
    assert len(rows)==n+1 and rows[-1]=={'done':n}
    assert all(type(r.get('i')) is int and r['i']==i for i,r in enumerate(rows[:-1]))
    return [{k:v for k,v in r.items() if k!='i'} for r in rows[:-1]]


def qualify_one(job):
    spec,text,folder=job['spec'],job['source'],Path(job['folder']);folder.mkdir(parents=True)
    tests=json.loads(Path(spec['tests_file']).read_text());base=[]
    for call in spec['baseline_calls']:
        raw=Path(call['file']).read_bytes();assert analyze.sha(raw)==call['sha256']
        base.extend(parse(raw,call['cases']))
    assert len(base)==len(tests)==spec['cases'];passed=0;failures=[]
    for off in range(0,len(tests),32):
        batch=tests[off:off+32]
        res=sandbox.run(['/usr/bin/python3','harness.py'],files={'harness.py':(HERE/'harness.py').read_bytes(),'candidate.py':text,
            'inputs.json':json.dumps({'entry':spec['entry'],'calls':[{'args':t['args']} for t in batch]})},
            limits=sandbox.Limits(cpu_seconds=3,wall_seconds=8,memory_bytes=512*1024**2,max_output_bytes=4*1024**2))
        (folder/f'{off}.stdout').write_bytes(res.stdout);(folder/f'{off}.stderr').write_bytes(res.stderr)
        try:
            assert res.ok,f'sandbox exit={res.exit_code}, timeout={res.timed_out}'
            observations=parse(res.stdout,len(batch))
            for j,(test,o) in enumerate(zip(batch,observations)):
                valid=not o['error'] and _matches(FunctionalTest(args=test['args'],expected=test['expected'],compare=test.get('compare','return')),
                                               {'result':o['result'],'args':o['args_after']})
                same=json.dumps(o,sort_keys=True)==json.dumps(base[off+j],sort_keys=True)
                passed+=bool(valid and same)
                if not valid or not same:failures.append({'case':off+j,'oracle':bool(valid),'parity':same})
        except Exception as e:failures.append({'offset':off,'reason':str(e)})
    return {'passed':passed==len(tests) and not failures,'checks_passed':passed,'cases':len(tests),'failures':failures}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    for row in c['sources']:
        assert analyze.sha(Path(row['tests_file']).read_bytes())==row['tests_sha256']
        for call in row['baseline_calls']:assert analyze.sha(Path(call['file']).read_bytes())==call['sha256']
    args.output.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(2,mp_context=multiprocessing.get_context('spawn')) as pool:
        widths=list(pool.map(width_job,[{'width':w,'output':str(args.output.resolve())} for w in (7,8)]))
    arms=[a for width in widths for a in width['arms']];analyze.write(args.output/'unqualified-results.json',widths)
    jobs={};specs={str(r['id']):r for r in c['sources']}
    for a in arms:
        chosen=json.loads((args.output/f'w{a["width"]}'/a['arm']/'sources.json').read_text())
        for pid,row in a['per_problem'].items():
            if row['source_sha256']!=row['original_sha256']:
                key=f'{pid}-{row["source_sha256"]}'
                jobs[key]={'spec':specs[pid],'source':chosen[pid],'folder':str(args.output/'qualification'/key)}
    print(json.dumps({'phase':'qualification','distinct_changed':len(jobs),'sandbox_workers':4}),flush=True)
    receipts={};analyze.write(args.output/'qualification-private.json',receipts)
    with concurrent.futures.ProcessPoolExecutor(4,mp_context=multiprocessing.get_context('spawn')) as pool:
        futures={pool.submit(qualify_one,job):key for key,job in jobs.items()}
        for f in concurrent.futures.as_completed(futures):
            receipts[futures[f]]=f.result();analyze.write(args.output/'qualification-private.json',receipts)
    for a in arms:
        a['qualification']={}
        for pid,row in a['per_problem'].items():
            if row['source_sha256']==row['original_sha256']:q={'passed':True,'reused':True}
            else:q={**{k:v for k,v in receipts[f'{pid}-{row["source_sha256"]}'].items() if k!='failures'},'reused':False}
            a['qualification'][pid]=q
        a['qualified']=sum(q['passed'] for q in a['qualification'].values())
    analyze.write(args.output/'results.json',{'widths':widths,'arms':arms,'seconds':time.monotonic()-started,
                                           'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})
    print(json.dumps({'complete':True,'qualified':{f'{a["arm"]}-{2**a["width"]}':a['qualified'] for a in arms}}),flush=True)


if __name__=='__main__':main()
