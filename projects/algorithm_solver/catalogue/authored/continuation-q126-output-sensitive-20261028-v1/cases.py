"""Frozen Q126 cases plus an independent induced-path certificate."""
import importlib.util
from pathlib import Path
ORIGINAL=Path(__file__).resolve().parent.parent/'continuation-q-20261028-v1'

def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
reference=load(ORIGINAL/'oracles.py','q126_original_reference')
generator=load(ORIGINAL/'cases.py','q126_original_case_owner')


def induced_chain_args(last_letter=25):
    if type(last_letter) is not int or not 1<=last_letter<=25:raise ValueError('bounded chain extent')
    path=['aa']
    for index in range(1,last_letter+1):
        current,previous=chr(97+index),chr(96+index)
        path.extend((current+previous,current+current))
    return [path[0],path[-1],path[1:]]


def induced_path_certificate(args):
    reference.validate_domain(126,args)
    begin,end,words=args
    if len(begin)!=2 or len(words)>50 or end not in words or begin in words:raise ValueError('bounded two-character induced path required')
    vertices=[begin]+words
    adjacency=[[j for j,other in enumerate(vertices) if i!=j and sum(a!=b for a,b in zip(word,other))==1] for i,word in enumerate(vertices)]
    target=vertices.index(end)
    if any(len(row)!=(1 if i in (0,target) else 2) for i,row in enumerate(adjacency)):raise ValueError('not an induced endpoint path')
    distances=[None]*len(vertices);distances[0]=0;parents=[None]*len(vertices);ways=[0]*len(vertices);ways[0]=1;pending=[0]
    for node in pending:
        for neighbor in adjacency[node]:
            if distances[neighbor] is None:
                distances[neighbor]=distances[node]+1;parents[neighbor]=node;pending.append(neighbor)
            if distances[neighbor]==distances[node]+1:ways[neighbor]+=ways[node]
    if len(pending)!=len(vertices) or distances[target]!=len(vertices)-1 or ways[target]!=1:raise ValueError('unique full-length shortest path not certified')
    path=[];node=target
    while node is not None:path.append(vertices[node]);node=parents[node]
    path.reverse()
    return [path]


def build_cases():
    rows=[{**row,'inherited_q_case_index':index} for index,row in enumerate(generator.build_cases(126,include_maximum=True))]
    args=induced_chain_args();wanted=induced_path_certificate(args)
    if len(wanted)!=1 or len(wanted[0])!=51:raise ValueError('required51-word certificate missing')
    rows.append({'args':args,'expected':wanted,'category':'closed-induced-two-character-chain','isolate':True,
                 'certificate':'Independent pairwise Hamming graph has endpoint degrees1, all other degrees2, connected, distance50, one shortest path.',
                 'comparison':{'kind':'unordered-distinct-sequences','duplicates_forbidden':True}})
    return rows
