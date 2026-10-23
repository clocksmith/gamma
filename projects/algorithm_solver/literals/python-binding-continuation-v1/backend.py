"""Explicitly named existing research backends; no corpus access at import."""
import importlib.util
from pathlib import Path

HERE=Path(__file__).resolve().parent;LIT=HERE.parent

def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

names=module('python_continuation_name_optimizer',LIT/'binding-descent-v1/rewrite.py')
analyze=names.analyze
tail=module('python_continuation_tail',LIT/'tail-search-v1/search.py')
body=module('python_continuation_body',LIT/'python-name-v1/bindings.py')
style=module('python_continuation_style',LIT/'style150-v2/measure.py')
v3=style.v3
_original_prune=v3.prune

def capped_prune(sources,state,width,budget):
    return (state,[]) if budget.expired() else _original_prune(sources,state,width,budget)
v3.prune=capped_prune

def banned(variants,entries):
    return {s for pid,choices in variants.items() for text in choices.values()
            for s in body.forbidden(text,entries[pid])}

def polish(variants,vocab,width,entries,c,enabled):
    ban=banned(variants,entries);budget=v3.Budget(c['search'])
    state=v3.evaluate(variants,vocab,width,None,budget);log=[];stop='fixed_dictionary'
    if enabled:
        proposer=style.hybrid_chosen([],variants)
        def safe(s,st,limit,fraction):
            return [p for p in proposer(s,st,limit,fraction) if p not in ban]
        state,_=v3.refill(variants,state,width,safe,c['neighborhood'],24,budget)
        state,stop=v3.local_search(variants,state,width,safe,c['neighborhood'],budget,log)
    assert budget.trials<=c['search']['trials']
    return state,{'trials':budget.trials,'stop':stop,'seconds':budget.elapsed(),
                  'selections':state['selections'],'trace':log}

def parent_qualified_sources(c):
    """Only exact source/ID pairs in the pinned public passing receipt may reuse."""
    import json
    raw=(LIT/'python-name-v1/evidence/results.json').read_bytes()
    assert analyze.sha(raw)==c['parent_results_sha256']
    parent=json.loads(raw)
    return {(pid,row['source_sha256']) for arm in parent['arms']
            for pid,row in arm['per_problem'].items()
            if arm['qualification'][pid]['passed']}

def write_atomic(path,obj):
    """Persist a complete receipt before replacing its previous checkpoint."""
    import json,os
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w') as f:
        json.dump(obj,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temporary,path)
