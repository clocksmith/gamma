"""Exact coverage through actual selected literals; no implicit character arcs."""
import importlib.util
from pathlib import Path
import random
import sys
import time
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
ALPHABET=[chr(i) for i in range(32,127)]+['\n']


def solve(texts,fixed,candidates,capacity,seconds):
    import numpy as np
    from scipy.optimize import milp,LinearConstraint,Bounds
    from scipy.sparse import coo_matrix
    fixed=set(fixed);candidates=list(candidates);C=len(candidates);idx={s:i for i,s in enumerate(candidates)}
    assert len(idx)==C and not fixed&set(candidates) and all(fixed|set(candidates))
    maxlen=max(map(len,fixed|set(candidates)),default=1)
    tail=[];head=[];entry=[];src=[];sink=[];base=0
    for pid,text in sorted(texts.items()):
        src.append(base);sink.append(base+len(text))
        for i in range(len(text)):
            for length in range(1,min(maxlen,len(text)-i)+1):
                word=text[i:i+length]
                if word in fixed:
                    tail.append(base+i);head.append(base+i+length);entry.append(-1)
                elif word in idx:
                    tail.append(base+i);head.append(base+i+length);entry.append(idx[word])
        base+=len(text)+1
    tail=np.asarray(tail,dtype=np.int64);head=np.asarray(head,dtype=np.int64);entry=np.asarray(entry,dtype=np.int64)
    A=len(tail);V=C+A;arcs=np.arange(A);cost=np.zeros(V);cost[C:]=1
    flow=coo_matrix((np.concatenate([np.ones(A),-np.ones(A)]),(np.concatenate([tail,head]),np.concatenate([C+arcs,C+arcs]))),shape=(base,V)).tocsr()
    rhs=np.zeros(base);rhs[src]=1;rhs[sink]=-1
    optional=np.flatnonzero(entry>=0);J=len(optional)
    links=coo_matrix((np.concatenate([np.ones(J),-np.ones(J)]),(np.concatenate([np.arange(J),np.arange(J)]),np.concatenate([C+optional,entry[optional]]))),shape=(J,V)).tocsr()
    budget=np.zeros(V);budget[:C]=1;integ=np.zeros(V);integ[:C]=1
    start=time.monotonic()
    result=milp(cost,constraints=[LinearConstraint(flow,rhs,rhs),LinearConstraint(links,-np.inf,0),LinearConstraint(budget[None,:],-np.inf,capacity)],
                integrality=integ,bounds=Bounds(0,1),options={'time_limit':float(seconds),'mip_rel_gap':0.,'disp':False})
    chosen=[word for i,word in enumerate(candidates) if result.x is not None and result.x[i]>.5]
    assert len(chosen)<=capacity
    return chosen,{'status':int(result.status),'message':str(result.message),'feasible':result.x is not None,
                   'objective':None if result.fun is None else float(result.fun),'dual_bound':getattr(result,'mip_dual_bound',None),
                   'gap':getattr(result,'mip_gap',None),'solver_seconds':time.monotonic()-start,'arcs':A,'variables':V}


def exact(texts,vocab):
    rows={};counts={c:0 for c in vocab if len(c)==1}
    for pid,text in sorted(texts.items()):
        seq=analyze.shortest_encode(text,vocab);rows[pid]=len(seq)
        for i in seq:
            if len(vocab[i])==1:counts[vocab[i]]+=1
    return sum(rows.values()),rows,counts


def proposal(vocab,observed,reserved,pool,ranked,rng,mode,cfg,usage):
    learned=sorted(s for s in vocab if len(s)>1);chars=sorted(s for s in vocab if len(s)==1 and s in observed and s not in reserved)
    dropchars=[]
    if mode=='optional':
        number=min(cfg['free_characters'],len(chars));head=sorted(chars,key=lambda c:(usage.get(c,0),c))[:min(cfg['priority_characters'],number)]
        dropchars=head+rng.sample([c for c in chars if c not in head],number-len(head))
    removed=dropchars+rng.sample(learned,min(cfg['free_total']-len(dropchars),len(learned)))
    fixed=[s for s in vocab if s not in set(removed)];fixset=set(fixed)
    top=[s for s in ranked if s not in fixset][:cfg['top']];present=fixset|set(top)
    extra=[s for s in rng.sample(pool,min(len(pool),3*cfg['random'])) if s not in present][:cfg['random']]
    candidatechars=sorted(observed-fixset) if mode=='optional' else []
    candidates=list(dict.fromkeys(removed+candidatechars+top+extra))
    assert set(reserved)<=fixset
    if mode=='fixed96':assert set(ALPHABET)<=fixset
    return fixed,candidates,256-len(fixed),{'freed_characters':len(dropchars),'freed_learned':len(removed)-len(dropchars)}
