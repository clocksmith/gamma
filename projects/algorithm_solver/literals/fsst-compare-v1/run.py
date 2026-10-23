"""Pinned author FSST, native optimal paths, and explicit Gamma dictionary adapters."""
import argparse
from collections import Counter
import concurrent.futures
import importlib.util
import json
import multiprocessing
from pathlib import Path
import sys
import time
import native
import packet
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

tail=module('fsst_tail',LIT/'tail-search-v1/search.py')
v3=module('fsst_v3',LIT/'matched80-v3/run.py')
_original_prune=v3.prune

def capped_prune(sources,state,width,budget):
    return (state,[]) if budget.expired() else _original_prune(sources,state,width,budget)

v3.prune=capped_prune


def pool_and_adapter(table,payloads,fit,banned):
    counts=Counter()
    for payload in payloads:
        for i,n in enumerate(native.counts(table,payload)['symbol_uses']):counts[i]+=n
    pool=[]
    for i,word in enumerate(table):
        if len(word)<2:continue
        text=word.decode('ascii')
        if text in banned or sum(text in source for source in fit.values())<2:continue
        pool.append((-(len(word)-1)*counts[i],len(word),text))
    ranked=[text for _,_,text in sorted(pool)]
    return ranked,v3.joint.order(list(v3.FALLBACK)+ranked[:160])


def records(texts,header,table,native_payloads,vocab,kind):
    rows={};sequences={}
    for pid,text in sorted(texts.items()):
        if kind.startswith('native'):
            payload=native_payloads[pid] if kind=='native_author' else native.optimal(table,text.encode())
            framed=packet.pack(header,payload);assert packet.unpack(header,framed)==text.encode()
            counters=native.counts(table,payload);n=counters['selections'];chars=counters['single_character_channel_codes']
            sequences[pid]=list(payload);escapes=counters['escapes']
        else:
            seq=analyze.shortest_encode(text,vocab);framed=analyze.encode(vocab,seq,8)
            assert analyze.decode(analyze.dictionary_bytes(vocab),framed)==text
            n=len(seq);chars=sum(len(vocab[i])==1 for i in seq);sequences[pid]=seq;escapes=0
        rows[pid]={'encodable':True,'source_sha256':analyze.sha(text.encode()),'source_bytes':len(text.encode()),
            'selections':n,'actions':n+1,'single_characters':chars,'escapes':escapes,'packet_bytes':len(framed),
            'packet_sha256':analyze.sha(framed),'qualification_reused':True}
    return rows,sequences


def arm(job):
    work,out=Path(job['work']),Path(job['output']);cohort=job['cohort'];c=json.loads((HERE/'contract.json').read_text())
    seed=work/cohort['relative_path'];fit=json.loads((seed/'fit-sources.json').read_text())
    assert set(fit)=={str(i) for i in c['partition']['dev_fit']}
    structure=tail.source_structure(fit);banned=set(fit.values())|{b for r in structure.values() for b in r['bodies']}
    baseline=json.loads((seed/'dictionary.json').read_text());folder=out/cohort['name'];folder.mkdir();start=time.monotonic()
    fit_order=sorted(fit,key=int)
    with native.Encoder(c['library_path'],[fit[pid].encode() for pid in fit_order]) as enc:
        native_seconds=time.monotonic()-start
        fit_payloads=enc.compress([fit[pid].encode() for pid in fit_order])
        pool,adapted=pool_and_adapter(enc.table,fit_payloads,fit,banned)
        variants={pid:{'fixed':text} for pid,text in fit.items()};budget=v3.Budget(c['search'])
        state=v3.evaluate(variants,adapted,8,None,budget);initial=state['selections'];trace=[]
        def propose(sources,state,limit,fraction):return [p for p in pool if p not in state['vocab']][:limit]
        state,_=v3.refill(variants,state,8,propose,c['neighborhood'],24,budget)
        state,stop=v3.local_search(variants,state,8,propose,c['neighborhood'],budget,trace)
        polished=state['vocab'];search_seconds=budget.elapsed()
        (folder/'native-header.bin').write_bytes(enc.header)
        for name,vocab in [('gamma_seed',baseline),('gamma_adapter',adapted),('gamma_polish',polished)]:analyze.write(folder/f'{name}-dictionary.json',vocab)
        seal={'validation_loaded':False,'native_header_sha256':analyze.sha(enc.header),'fit_sources_sha256':analyze.sha((seed/'fit-sources.json').read_bytes()),
              'dictionary_sha256':{name:analyze.sha((folder/f'{name}-dictionary.json').read_bytes()) for name in ('gamma_seed','gamma_adapter','gamma_polish')}}
        analyze.write(folder/'fit-seal.json',seal);analyze.write(folder/'trace.json',trace)
        previous=json.loads((seed/'sources.json').read_text());val={str(i):previous[str(i)] for i in c['partition']['dev_val']}
        val_order=sorted(val,key=int);val_payloads=enc.compress([val[pid].encode() for pid in val_order])
        payloads={**dict(zip(fit_order,fit_payloads)),**dict(zip(val_order,val_payloads))};texts={**fit,**val}
        structure=tail.source_structure(val);banned|=set(val.values())|{b for r in structure.values() for b in r['bodies']}
        hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());prior=next(a for a in hist['arms'] if a['width']==8 and a['arm']==cohort['arm'])
        for pid,text in texts.items():assert prior['qualification'][pid]['passed'] and prior['per_problem'][pid]['source_sha256']==analyze.sha(text.encode())
        analyze.write(folder/'sources.json',texts)
        outputs=[]
        for kind,vocab in [('gamma_seed',baseline),('native_author',None),('native_optimal',None),('gamma_adapter',adapted),('gamma_polish',polished)]:
            rows,seqs=records(texts,enc.header,enc.table,payloads,vocab,kind)
            native_view=kind.startswith('native');words=[s.decode('ascii') for s in enc.table] if native_view else vocab
            illegal=sorted(analyze.sha(s.encode()) for s in set(words)&banned)
            db=len(enc.header) if native_view else len(analyze.dictionary_bytes(vocab))
            if kind=='gamma_seed':assert all(rows[pid]['selections']==prior['per_problem'][pid]['selections'] and rows[pid]['single_characters']==prior['per_problem'][pid]['single_characters'] for pid in rows)
            if native_view:
                for pid,text in texts.items():enc.verify_official(bytes(seqs[pid]),text.encode())
            a={'cohort':cohort['name'],'arm':kind,'width':8,'entries':len(words),'native_format':native_view,'dictionary_bytes':db,
               'dictionary_sha256':analyze.sha(enc.header) if native_view else seal['dictionary_sha256'][kind],
               'per_problem':rows,'illegal_entry_sha256':illegal,'native_table_build_seconds':native_seconds,
               'pool_entries':len(pool),'adapter_entries':len(adapted),'polish_initial_fit_selections':initial,'polish_final_fit_selections':state['selections'],
               'polish_trials':budget.trials,'polish_stop':stop,'polish_seconds':search_seconds,
               'source_qualification_receipt':c['historical_evidence_sha256'],'decoder_source_bytes':c['native_decoder_bytes'] if native_view else c['gamma_decoder_bytes']}
            for split,key in [('fit','dev_fit'),('validation','dev_val')]:
                ids=c['partition'][key];d=tail.aggregate(rows,ids,db);d['single_character_codes']=sum(rows[str(i)]['single_characters'] for i in ids)
                d['escaped_raw_bytes']=sum(rows[str(i)]['escapes'] for i in ids);d['qualified']=len(ids)
                d['package_with_decoder_source']=d['package_bytes']+a['decoder_source_bytes'];d['source_bytes']=sum(rows[str(i)]['source_bytes'] for i in ids)
                d['framing_bytes']=41*len(ids);d['payload_bits']=8*d['selections']['total'];d['padding_bits']=0;a[split]=d
            analyze.write(folder/f'{kind}-sequences.json',seqs);outputs.append(a)
        for pid in texts:assert outputs[2]['per_problem'][pid]['selections']<=outputs[1]['per_problem'][pid]['selections']
    print(json.dumps({'cohort':cohort['name'],'native_table_bytes':len(enc.header),'native_symbols':len(enc.table),'pool_entries':len(pool),
                      'polish_trials':budget.trials,'polish_stop':stop}),flush=True)
    analyze.write(folder/'results.json',outputs);return outputs


def main(work,out):
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['external_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    out.mkdir(parents=True,exist_ok=False);start=time.monotonic()
    jobs=[{'work':str(work),'output':str(out),'cohort':x} for x in c['cohorts']]
    with concurrent.futures.ProcessPoolExecutor(max_workers=2,mp_context=multiprocessing.get_context('spawn')) as pool:results=[a for group in pool.map(arm,jobs) for a in group]
    analyze.write(out/'results.json',{'schema':'gamma.fsst-compare.results.v1','arms':results,'seconds':time.monotonic()-start,
        'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})
    print(json.dumps({'complete':True,'decodes':sum(len(a['per_problem']) for a in results),'seconds':time.monotonic()-start}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work.resolve(),a.output.resolve())
