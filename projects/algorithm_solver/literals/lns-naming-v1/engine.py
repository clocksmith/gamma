"""Fit-only naming and exact selected-source dictionary repairs; no data loading."""
from collections import Counter
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

HERE=Path(__file__).resolve().parent;LIT=HERE.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

rewrite=module('lns_names_rewrite',LIT/'coupled-names-v1/rewrite.py')
analyze=rewrite.analyze
m=module('lns_names_style',LIT/'style150-v2/measure.py');v3=m.v3
lns=module('lns_names_repair',LIT/'mip-lns-v1/lns.py')
sel=module('lns_names_selection',LIT/'lagrange-select-v2/selection.py')
_original_prune=v3.prune

def capped_prune(sources,state,width,budget):
    return (state,[]) if budget.expired() else _original_prune(sources,state,width,budget)
v3.prune=capped_prune


def choose(variants,vocab):
    return v3.joint.evaluate(variants,vocab,8)


def selected(variants,state):
    return {pid:variants[pid][name] for pid,name in state['chosen'].items()}


def digest_texts(texts):
    return analyze.sha(json.dumps(texts,sort_keys=True,separators=(',',':')).encode())


def forbidden(variants):
    banned=set()
    for name in sorted({n for vs in variants.values() for n in vs}):
        banned |= sel.forbidden_strings({pid:vs[name] for pid,vs in variants.items() if name in vs})
    return banned


def naming(texts,vocab,cfg):
    records=rewrite.records(texts);output={};stats={}
    for pid,text in sorted(texts.items()):
        output[pid],stats[str(pid)]=rewrite.ordinary(text,records[str(pid)],vocab,sweeps=cfg['sweeps'],max_trials=cfg['trials'])
    return output,stats


def ranked_pool(texts,banned,max_length):
    pool=sel.build_pool(texts,banned,max_length);lookup=set(pool);counts=Counter()
    for text in texts.values():
        for i in range(len(text)):
            for length in range(2,min(max_length,len(text)-i)+1):
                fragment=text[i:i+length]
                if fragment in lookup:counts[fragment]+=1
    return pool,sorted(pool,key=lambda s:(-counts[s]*(len(s)-1),s))


def proposal(incumbent,pool,ranked,rng,cfg):
    learned=sorted(set(incumbent)-set(sel.ALPHABET));removed=rng.sample(learned,min(cfg['free'],len(learned)))
    removed_set=set(removed);fixed=[s for s in incumbent if s not in removed_set];fixset=set(fixed)
    top=[s for s in ranked if s not in fixset][:cfg['top']];present=fixset|set(top)
    extra=[s for s in rng.sample(pool,min(len(pool),cfg['random']*3)) if s not in present][:cfg['random']]
    cand=list(dict.fromkeys(removed+top+extra))
    return fixed,cand,256-len(fixed)


def check_solver(texts,trial,solver):
    if not solver['feasible']:return None
    exact=sel.exact_fit(texts,trial)
    assert solver['objective'] is not None and exact<=solver['objective']+1e-6,'exact selected-source cost exceeds solver objective'
    if solver['status']==0:assert abs(exact-solver['objective'])<=1e-6,'optimal solver objective mismatch'
    return exact


def repairs(variants,state,banned,cfg,folder,round_no,repair_fn=None):
    """MILP is conditioned on selected sources. Reselection is a separate exact step."""
    repair_fn=repair_fn or lns.repair;folder.mkdir(parents=True,exist_ok=True)
    start=time.monotonic();snapshot=selected(variants,state)
    pool,ranked=ranked_pool(snapshot,banned,cfg['max_length'])
    analyze.write(folder/'pool.json',pool)
    pool_hash=analyze.sha((folder/'pool.json').read_bytes());rng=random.Random(cfg['seed']+round_no)
    moves=[];stop='move_limit'
    for no in range(cfg['moves']):
        remaining=cfg['seconds']-(time.monotonic()-start)
        if remaining<=0:stop='time_limit';break
        before=state['selections'];snapshot=selected(variants,state);source_hash=digest_texts(snapshot)
        fixed,candidates,capacity=proposal(state['vocab'],pool,ranked,rng,cfg)
        chosen,solver=repair_fn(snapshot,fixed,candidates,capacity,min(cfg['solver_seconds'],remaining))
        trial=fixed+chosen
        assert len(trial)==len(set(trial))<=256 and set(sel.ALPHABET)<=set(trial)
        assert not set(trial)&banned
        exact=check_solver(snapshot,trial,solver)
        candidate=choose(variants,trial) if exact is not None else None
        if candidate is not None:assert candidate['selections']<=exact
        accepted=candidate is not None and candidate['selections']<before
        row={'move':no,'round':round_no,**solver,'capacity':capacity,'candidates':len(candidates),'chosen_entries':len(chosen),
             'before':before,'snapshot_exact':exact,'reselected_exact':None if candidate is None else candidate['selections'],
             'reselection_gain':None if candidate is None else exact-candidate['selections'],
             'accepted':accepted,'selected_source_sha256':source_hash,'pool_sha256':pool_hash,'validation_loaded':False}
        if accepted:
            state=candidate
            analyze.write(folder/f'incumbent-{no:02d}.json',state['vocab'])
            analyze.write(folder/f'selected-{no:02d}.json',selected(variants,state))
            row['dictionary_sha256']=analyze.sha((folder/f'incumbent-{no:02d}.json').read_bytes())
            row['accepted_source_sha256']=digest_texts(selected(variants,state))
        row['incumbent']=state['selections'];moves.append(row)
        with (folder/'moves.jsonl').open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
        print(json.dumps({'phase':'repair',**row}),flush=True)
    return state,{'pool_entries':len(pool),'pool_sha256':pool_hash,'pool_source_sha256':digest_texts(snapshot) if not moves else moves[0]['selected_source_sha256'],
                  'moves':moves,'stop':stop,'seconds':time.monotonic()-start}


def polish(variants,state,banned,cfg,neighborhood):
    budget=v3.Budget(cfg);log=[];propose=m.hybrid_chosen([],variants)
    def safe(sources,current,limit,fraction):return [s for s in propose(sources,current,limit,fraction) if s not in banned]
    # The start is already evaluated; count one initial exact evaluation, as the controls do.
    state=v3.evaluate(variants,state['vocab'],8,None,budget)
    state,_=v3.refill(variants,state,8,safe,neighborhood,24,budget)
    state,stop=v3.local_search(variants,state,8,safe,neighborhood,budget,log)
    assert budget.trials<=cfg['trials'] and not set(state['vocab'])&banned
    return state,{'trials':budget.trials,'seconds':budget.elapsed(),'stop':stop,'selections':state['selections'],'trace':log}
