"""Fit fixed-source dictionaries with frozen character penalties; seal then evaluate."""
import argparse
import concurrent.futures
import importlib.util
import json
import multiprocessing
from pathlib import Path
import time
import search
HERE=search.HERE;LIT=search.LIT;analyze=search.analyze

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

tail=module('char_tail',LIT/'tail-search-v1/search.py')
seg=module('char_secondary',LIT/'segmentation-audit-v1/segment.py')


def measure(texts,vocab,policy,weight):
    db=analyze.dictionary_bytes(vocab);rows={};seqs={}
    for pid,text in sorted(texts.items()):
        seq=search.encode(text,vocab,weight) if policy=='weighted' else seg.encode(text,vocab,policy)
        packet=analyze.encode(vocab,seq,8);assert analyze.decode(db,packet)==text
        if policy=='canonical':assert seq==analyze.shortest_encode(text,vocab)
        rows[str(pid)]={'encodable':True,'source_sha256':analyze.sha(text.encode()),'source_bytes':len(text.encode()),
            'selections':len(seq),'actions':len(seq)+1,'single_characters':sum(len(vocab[i])==1 for i in seq),
            'packet_bytes':len(packet),'packet_sha256':analyze.sha(packet),'qualification_reused':True}
        seqs[str(pid)]=seq
    return rows,seqs


def arm(job):
    name,weight,work,out=job['name'],job['weight'],Path(job['work']),Path(job['output'])
    c=json.loads((HERE/'contract.json').read_text());seed=work/c['seed_path']
    fit=json.loads((seed/'fit-sources.json').read_text());vocab=json.loads((seed/'dictionary.json').read_text())
    assert set(fit)=={str(i) for i in c['partition']['dev_fit']}
    structure=tail.source_structure(fit);banned=set(fit.values())|{body for r in structure.values() for body in r['bodies']}
    assert not set(vocab)&banned
    budget=search.Budget(c['search']);state=search.evaluate(fit,vocab,8,weight,None,budget);initial=search.brief(state)
    trace=[];stop='fixed_seed'
    if name!='seed':
        state,_=search.prune(fit,state,8,weight,budget)
        state,_=search.refill(fit,state,8,weight,banned,c['neighborhood'],24,budget)
        state,stop=search.local_search(fit,state,8,weight,banned,c['neighborhood'],budget,trace)
    search_seconds=budget.elapsed()
    vocab=state['vocab'];folder=out/name;folder.mkdir()
    analyze.write(folder/'dictionary.json',vocab)
    analyze.write(folder/'fit-seal.json',{'validation_loaded':False,'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),
                 'fit_sources_sha256':analyze.sha((seed/'fit-sources.json').read_bytes()),'objective':state['objective']})
    # No source adaptation under these dictionaries. Read only the frozen seed's validation IDs now.
    old=json.loads((seed/'sources.json').read_text());val={str(i):old[str(i)] for i in c['partition']['dev_val']};texts={**fit,**val}
    validation_structure=tail.source_structure(val);banned|=set(val.values())|{body for r in validation_structure.values() for body in r['bodies']}
    illegal=sorted(analyze.sha(s.encode()) for s in set(vocab)&banned)
    analyze.write(folder/'trace.json',trace);analyze.write(folder/'sources.json',texts)
    hist=json.loads((LIT/'binding-descent-v1/evidence/results.json').read_text());prior=next(a for a in hist['arms'] if a['width']==8 and a['arm']=='scope_joint')
    for pid,text in texts.items():
        assert prior['qualification'][pid]['passed'] and analyze.sha(text.encode())==prior['per_problem'][pid]['source_sha256']
    outputs=[]
    for policy in ('canonical','shortest_min_char','weighted'):
        rows,seqs=measure(texts,vocab,policy,weight)
        a={'arm':name,'weight':weight,'policy':policy,'width':8,'entries':len(vocab),'dictionary_bytes':len(analyze.dictionary_bytes(vocab)),
           'dictionary_sha256':analyze.sha((folder/'dictionary.json').read_bytes()),'per_problem':rows,'illegal_entry_sha256':illegal,
           'initial_fit_objective':initial,'final_fit_objective':search.brief(state),'search_trials':budget.trials,'search_seconds':search_seconds,
           'search_stop':stop,'accepted_dictionary_moves':len(trace),'reused_qualification_receipt':c['historical_evidence_sha256']}
        for split,key in [('fit','dev_fit'),('validation','dev_val')]:
            ids=c['partition'][key];d=tail.aggregate(rows,ids,a['dictionary_bytes']);d['single_character_codes']=sum(rows[str(i)]['single_characters'] for i in ids)
            d['package_with_decoder_dependencies']=d['package_bytes']+c['decoder_dependency_bytes'];d['qualified']=len(ids)
            d['source_bytes']=sum(rows[str(i)]['source_bytes'] for i in ids);d['framing_bytes']=41*len(ids);d['payload_bits']=8*d['selections']['total'];d['padding_bits']=0
            a[split]=d
        if policy=='weighted':assert 4*a['fit']['selections']['total']+weight*a['fit']['single_character_codes']==state['objective']
        analyze.write(folder/f'{policy}-sequences.json',seqs);outputs.append(a)
    print(json.dumps({'arm':name,'fit':search.brief(state),'trials':budget.trials,'stop':stop}),flush=True)
    analyze.write(folder/'results.json',outputs);return outputs


def main(work,out):
    c=json.loads((HERE/'contract.json').read_text())
    for rel,h in c['code_hashes'].items():assert analyze.sha((LIT/rel).read_bytes())==h,rel
    for path,h in c['runtime_files'].items():assert analyze.sha(Path(path).read_bytes())==h,path
    for rel,h in c['private_files'].items():assert analyze.sha((work/rel).read_bytes())==h,rel
    out.mkdir(parents=True,exist_ok=False);started=time.monotonic()
    jobs=[{'name':n,'weight':w,'work':str(work),'output':str(out)} for n,w in [('seed',0),('w0',0),('w1',1),('w4',4),('w16',16)]]
    with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:results=[a for group in pool.map(arm,jobs) for a in group]
    analyze.write(out/'results.json',{'schema':'gamma.character-objective.results.v1','arms':results,'seconds':time.monotonic()-started,
        'contract_sha256':analyze.sha((HERE/'contract.json').read_bytes())})
    print(json.dumps({'complete':True,'decodes':sum(len(a['per_problem']) for a in results),'seconds':time.monotonic()-started}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--work',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();main(a.work.resolve(),a.output.resolve())
