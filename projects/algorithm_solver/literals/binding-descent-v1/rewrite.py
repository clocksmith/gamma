"""Exact literal-cost coordinate descent over safe lexical name assignments."""
import importlib.util
import json
from pathlib import Path
import string
import subprocess
import sys

HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
_spec=importlib.util.spec_from_file_location('binding_descent_codec',LIT/'clusters-v1/search.py')
codec=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(codec)


def records(texts):
    got=subprocess.run(['node',str(HERE/'bindings.cjs')],input=json.dumps(texts),text=True,capture_output=True,check=True)
    return json.loads(got.stdout)


def legal(record,colors):
    return all((v['eligible'] or colors[v['id']]==v['name']) and (not v['eligible'] or colors[v['id']] not in v['forbidden']) and
        all(colors[v['id']]!=colors[j] or not (v['eligible'] or record['variables'][j]['eligible']) for j in v['neighbors']) for v in record['variables'])


def render(text,record,colors):
    assert legal(record,colors)
    edits=sorted((a,b,colors[v['id']]) for v in record['variables'] if colors[v['id']]!=v['name'] for a,b in v['spans'])
    output=[];offset=0
    for a,b,name in edits:
        assert a>=offset;output.extend([text[offset:a],name]);offset=b
    output.append(text[offset:]);return ''.join(output)


def optimize(text,record,vocab,mode='scope',sweeps=2,max_trials=12000):
    if not text.isascii() or record['unsafe']:
        return text,{'trials':0,'moves':0,'stop':'unsupported','reason':record['reason'] or 'non_ascii','_trace':[]}
    variables=record['variables'];colors=[v['name'] for v in variables]
    assert legal(record,colors)
    if mode=='global':
        groups={}
        for v in variables:groups.setdefault(v['name'],[]).append(v['id'])
        units=[ids for ids in groups.values() if all(variables[i]['eligible'] for i in ids)]
        reserved={v['name'] for v in variables if not v['eligible']}|{name for v in variables for name in v['forbidden']}
    else:
        units=[[v['id']] for v in variables if v['eligible']];reserved=set()
    units.sort(key=lambda ids:(-sum(len(variables[i]['spans']) for i in ids),min(ids)))
    tree=codec.trie(vocab);score=lambda t:len(codec.encode_text(t,tree))
    current=text;cost=score(text);trials=moves=0;trace=[];stop='sweep_limit'
    for sweep in range(sweeps):
        changed=False
        for ui,unit in enumerate(units):
            best=None;seen=set()
            def trial(proposal):
                nonlocal trials,best
                key=tuple(proposal)
                if trials>=max_trials or key in seen or key==tuple(colors):return
                seen.add(key)
                if not legal(record,proposal):return
                if mode=='global':
                    mapped=[proposal[u[0]] for u in units]
                    if len(mapped)!=len(set(mapped)) or set(mapped)&reserved:return
                candidate=render(text,record,proposal);value=score(candidate);trials+=1
                trace.append({'sweep':sweep,'unit':ui,'selections':value,'sha256':analyze.sha(candidate.encode())})
                order=(value,len(candidate.encode()),candidate)
                if value<cost and (best is None or order<best[0]):best=(order,proposal,candidate)
            for letter in string.ascii_lowercase:
                if letter in reserved:continue
                proposal=list(colors)
                for i in unit:proposal[i]=letter
                trial(proposal)
            # A pair swap can cross a collision barrier, but all graph constraints still apply.
            for other in units:
                if other is unit or colors[other[0]]==colors[unit[0]]:continue
                proposal=list(colors)
                for i in unit:proposal[i]=colors[other[0]]
                for i in other:proposal[i]=colors[unit[0]]
                trial(proposal)
            if best is not None:
                order,colors,current=best;cost=order[0];moves+=1;changed=True
                trace.append({'accepted_colors':list(colors),'selections':cost,'sha256':analyze.sha(current.encode())})
            if trials>=max_trials:stop='trial_limit';break
        if trials>=max_trials:break
        if not changed:stop='local_coordinate_stop';break
    return current,{'trials':trials,'moves':moves,'stop':stop,'reason':None,'eligible_bindings':sum(v['eligible'] for v in variables),
        'units':len(units),'initial_distinct_spellings':len(set(v['name'] for v in variables)),
        'final_distinct_spellings':len(set(colors)),'_trace':trace}
