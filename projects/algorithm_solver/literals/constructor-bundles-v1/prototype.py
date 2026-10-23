"""Synthetic-only atomic constructor/operand bundles; unchanged item32 codec."""
from collections import defaultdict
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent;PARENT=HERE.parent/'stacking-structured-v1'
import codec
_spec=importlib.util.spec_from_file_location('constructor_bundle_parent_search',PARENT/'search.py')
parent_search=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent_search)


def operands(text,node,kind):
    return [text[a:b] for a,b in node['holes']] if kind=='P' else node['args'][:]


def proposals(texts,nodes,current,allowed,forbidden,max_operand_length=160):
    """One existing constructor instance plus at most four paid literal operands.

    No input discovery/reading, optimizer loop, source rewrite or grammar change.
    All missing operands must independently occur as operands in >=2 programs.
    """
    owners=defaultdict(set);instances=[];present=set(current);allowed=set(allowed)
    for pid,text in texts.items():
        for kind,family in (('P','prefix'),('I','identifier')):
            for node in nodes[str(pid)][family]:
                if not node['key'] or node['key'] not in allowed:continue
                args=operands(text,node,kind);instances.append((pid,node,kind,args))
                for word in set(args):
                    if word not in forbidden and 2<=len(word)<=max_operand_length:owners[word].add(pid)
    eligible={word for word,support in owners.items() if len(support)>=2}
    bundles={}
    for pid,node,kind,args in instances:
        if any(codec.literal(word) not in present and word not in eligible for word in args):continue
        additions=set([node['key']]+[codec.literal(word) for word in args])-present
        if not additions or len(additions)>5:continue
        signature=tuple(codec.order(additions));row=bundles.setdefault(signature,{'keys':list(signature),'constructor':node['key'],
                    'kind':kind,'operand_keys':codec.order(codec.literal(word) for word in set(args)),'program_ids':set()})
        row['program_ids'].add(str(pid))
    return [{**row,'program_ids':sorted(row['program_ids'])} for _,row in sorted(bundles.items())],eligible


def evaluate_bundle(texts,nodes,current,additions,removals,forbidden,typed=True):
    """Atomic, freshly evaluated whole-fit score; operands never free or implicit."""
    mandatory={k for k in current if k.startswith('L') and len(k)==2}
    assert not (set(additions)&set(removals))
    keys=codec.order((set(current)-set(removals))|set(additions))
    if not mandatory<=set(keys) or not 1<=len(keys)<=256:return None
    if any(k.startswith('L') and k[1:] in forbidden for k in keys):return None
    budget=parent_search.Budget(1,float('inf'))
    state=parent_search.evaluate(texts,nodes,keys,budget)
    if state is None:return None
    dictionary=codec.dictionary(keys) if typed else codec.literal_dictionary(keys)
    return {**state,'dictionary_bytes':len(dictionary),
            'package_bytes':len(dictionary)+sum(41+r['selections'] for r in state['rows'].values()),
            'actions':state['selections']+len(texts),
            'argument_codes':sum(r['argument_codes'] for r in state['rows'].values()),
            'constructor_codes':sum(r['constructor_codes'] for r in state['rows'].values())}


def counterexample(full_capacity=False):
    """Invented shared Math.max family, unrelated to research source populations."""
    from itertools import product
    texts={};initial=set(map(codec.literal,codec.ALPHABET))
    for i,(left,right) in enumerate(product(('longAlpha','longGamma'),('longBeta','longDelta'))):
        prefix=f'function solve({left},{right}){{let pad=0;return '
        texts[str(i)]=prefix+f'Math.max({left},{right});}}'
        initial.update(map(codec.literal,[prefix,'Math.ma','x(long',left[4:]+',lo',right[2:]+')',';}']))
    fillers=[]
    if full_capacity:
        while len(initial)<256:
            word=f'__synthetic_unused_{len(fillers):03d}__';key=codec.literal(word);fillers.append(key);initial.add(key)
    nodes=codec.extract(texts);banned={word for group in nodes.values() for word in group['bodies']}
    return texts,nodes,codec.order(initial),banned,fillers
