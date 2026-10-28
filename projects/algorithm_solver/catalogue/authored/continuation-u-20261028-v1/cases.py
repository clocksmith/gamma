"""U source-free prospective indexed-tree cases; unavailable IDs stay excluded."""
import importlib.util
from pathlib import Path
from functools import lru_cache
from itertools import product
import json
import random
_SPEC=importlib.util.spec_from_file_location('gamma_u_case_reference',Path(__file__).with_name('oracles.py'))
o=importlib.util.module_from_spec(_SPEC);_SPEC.loader.exec_module(o)
IDS=o.IDS

def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
@lru_cache(None)
def shapes(n):
    if n==0:return (None,)
    return tuple((left,right) for left_size in range(n) for left in shapes(left_size) for right in shapes(n-1-left_size))
def indexed_shape(shape,values):
    left=[];right=[]
    def make(node):
        if node is None:return None
        index=len(left);left.append(None);right.append(None);left[index]=make(node[0]);right[index]=make(node[1]);return index
    root=make(shape)
    return {'values':list(values),'left':left,'right':right,'root':root}
def complete(values):
    n=len(values)
    return {'values':values,'left':[2*i+1 if 2*i+1<n else None for i in range(n)],'right':[2*i+2 if 2*i+2<n else None for i in range(n)],'root':0}
def chain(values,leftward):
    n=len(values)
    return {'values':values,'left':[i+1 if leftward and i+1<n else None for i in range(n)],'right':[i+1 if not leftward and i+1<n else None for i in range(n)],'root':0}
def permute(packet,permutation):
    n=len(permutation);values=[None]*n;left=[None]*n;right=[None]*n
    for old,new in enumerate(permutation):
        values[new]=packet['values'][old]
        for key,destination in (('left',left),('right',right)):
            child=packet[key][old];destination[new]=None if child is None else permutation[child]
    return {'values':values,'left':left,'right':right,'root':permutation[packet['root']]}
def build_cases():
    rows=[];seen=set();rng=random.Random(2026102833)
    def add(packet,tag):
        args=[packet];key=encoded(args)
        if key in seen:return
        seen.add(key);rows.append({'args':args,'expected':o.expected(257,args),'category':tag,'requires_native_identity_observer':True})
    for n in range(1,6):
        for shape in shapes(n):
            for values in product((-1,1),repeat=n):add(indexed_shape(shape,values),'exhaustive-small-tree-shape-and-values')
    add({'values':[1,2,3,5],'left':[1,None,None,None],'right':[2,3,None,None],'root':0},'public-root-to-leaf-example')
    add({'values':[1,2,2],'left':[1,None,None],'right':[2,None,None],'root':0},'identical-path-strings-two-distinct-leaves')
    add(complete([0]*7),'zero-values-and-identical-leaf-paths')
    for _ in range(64):
        n=rng.randint(1,100);values=[rng.randint(-100,100) for _ in range(n)];left=[None]*n;right=[None]*n;slots=[(0,'left'),(0,'right')]
        for index in range(1,n):
            parent,field=slots.pop(rng.randrange(len(slots)));(left if field=='left' else right)[parent]=index;slots.extend(((index,'left'),(index,'right')))
        p={'values':values,'left':left,'right':right,'root':0};add(permute(p,rng.sample(range(n),n)),'seeded-permuted-original-pool')
    for leftward in (True,False):add(chain([-100]*100,leftward),'maximum-depth-and-negative-string-width')
    add(complete([1]*100),'maximum-nodecount-duplicate-path-multiplicity')
    add(complete([-100 if i%2 else 100 for i in range(100)]),'maximum-mixed-sign-complete-tree')
    #100-node comb with many long leaf paths; node allocation remains finite.
    left=[None]*100;right=[None]*100
    for level in range(49):left[level]=level+1;right[level]=50+level
    left[49]=99
    add({'values':[-100]*100,'left':left,'right':right,'root':0},'maximum-comb-output-volume')
    return {257:rows}
