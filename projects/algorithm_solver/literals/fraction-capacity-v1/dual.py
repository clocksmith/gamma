"""Capacity lower bound for 10C-N; occurrence relaxation on an acyclic graph."""
import importlib.util
from pathlib import Path
import sys
import time
import numpy as np
HERE=Path(__file__).resolve().parent;LIT=HERE.parent
sys.path.insert(0,str(LIT/'cost-decomposition-v1'));import analyze
ALPHABET=[chr(i) for i in range(32,127)]+['\n']


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
sel=module('fraction_capacity_selection',LIT/'lagrange-select-v2/selection.py')


class Graph:
    def __init__(self,texts,pool,mandatory):
        self.pool=list(pool);self.mandatory=set(mandatory);self.pids=sorted(texts);self.texts=texts
        assert len(set(pool))==len(pool) and not set(pool)&self.mandatory
        index={s:i for i,s in enumerate(pool)};maxlen=max(map(len,set(pool)|self.mandatory),default=1)
        self.at=[];entries=[];self.lengths=[];self.order=[]
        for pid in self.pids:
            text=texts[pid];rows=[];self.lengths.append(len(text))
            for i in range(len(text)):
                row=[]
                for n in range(1,min(maxlen,len(text)-i)+1):
                    word=text[i:i+n]
                    if word in self.mandatory:row.append((i+n,-1,10*(n==1)-1))
                    elif word in index:
                        o=len(entries);entries.append(index[word]);row.append((i+n,o,10*(n==1)-1));self.order.append((pid,i,i+n,index[word]))
                rows.append(row)
            self.at.append(rows)
        self.occ_entry=np.asarray(entries,dtype=np.int64)

    def shortest(self,lam):
        y=np.zeros(len(self.occ_entry));total=0.
        for rows,n in zip(self.at,self.lengths):
            cost=[float('inf')]*n+[0.];back=[None]*n
            for i in range(n-1,-1,-1):
                for j,o,base in rows[i]:
                    value=base+(lam[o] if o>=0 else 0)+cost[j]
                    if value<cost[i]:cost[i]=value;back[i]=(j,o)
            assert np.isfinite(cost[0]);total+=cost[0];i=0
            while i<n:
                j,o=back[i]
                if o>=0:y[o]=1
                i=j
        return total,y

    def certificate(self,lam,capacity,denominator):
        q=[int(v) for v in np.floor(lam*denominator)];assert min(q,default=0)>=0
        sums=[0]*len(self.pool)
        for o,e in enumerate(self.occ_entry.tolist()):sums[e]+=q[o]
        paths=[]
        for rows,n in zip(self.at,self.lengths):
            cost=[None]*n+[0]
            for i in range(n-1,-1,-1):
                values=[base*denominator+(q[o] if o>=0 else 0)+cost[j] for j,o,base in rows[i] if cost[j] is not None]
                cost[i]=min(values) if values else None
            assert cost[0] is not None;paths.append(cost[0])
        subtraction=sum(sorted(sums,reverse=True)[:capacity]);numerator=sum(paths)-subtraction
        return {'numerator':numerator,'denominator':denominator,'integer_lower_bound':-(-numerator//denominator),
                'relaxed_paths_numerator':sum(paths),'top_capacity_numerator':subtraction,'per_program_path_numerators':paths},q


def encode_objective(text,vocab):
    """Exact min-F path, then fewest selections, then lexicographically first IDs."""
    byfirst={}
    for idx,s in enumerate(vocab):byfirst.setdefault(s[0],[]).append((idx,s))
    n=len(text);cost=[None]*n+[(0,0)];back=[None]*n
    for i in range(n-1,-1,-1):
        for idx,s in byfirst.get(text[i],[]):
            j=i+len(s)
            if text.startswith(s,i) and cost[j] is not None:
                key=(10*(len(s)==1)-1+cost[j][0],1+cost[j][1],idx)
                if back[i] is None or key<back[i][0]:cost[i]=key[:2];back[i]=(key,j,idx)
    if cost[0] is None:raise ValueError('unencodable')
    seq=[];i=0
    while i<n:_,i,idx=back[i];seq.append(idx)
    return cost[0][0],seq


def objective(texts,vocab):
    return sum(encode_objective(t,vocab)[0] for t in texts.values())


def optimize(texts,pool,mandatory,capacity,seed,cfg,trace):
    graph=Graph(texts,pool,mandatory);count=len(graph.occ_entry);lam=np.zeros(count);best_lam=lam.copy()
    assert set(seed)<=set(pool)|set(mandatory) and len(set(seed)-set(mandatory))<=capacity
    seed_cost=objective(texts,seed);upper=seed_cost;best_vocab=list(seed);generated_vocab=None;generated_cost=None
    best_bound=-float('inf');theta=1.;stall=0;ergodic=np.zeros(len(pool));started=time.monotonic();rank=np.arange(len(pool));stop='iteration_limit';executed=0;primal_attempts=0;primal_infeasible=0
    for iteration in range(cfg['iterations']):
        if time.monotonic()-started>=cfg['seconds']:stop='time_limit';break
        sp,y=graph.shortest(lam);sums=np.bincount(graph.occ_entry,weights=lam,minlength=len(pool));chosen=sel.top(sums,capacity,rank)
        bound=sp-float(sums[chosen].sum())
        if bound>best_bound+1e-9:best_bound=bound;best_lam=lam.copy();stall=0
        else:stall+=1
        if stall>=cfg['halve_after']:theta/=2;stall=0
        usage=np.bincount(graph.occ_entry,weights=y,minlength=len(pool));ergodic=.9*ergodic+.1*usage
        if iteration%cfg['primal_every']==0:
            for values in (sums,usage,ergodic):
                indices=sel.top(values,capacity,rank)
                vocab=list(mandatory)+[pool[k] for k in sorted(indices) if values[k]>0]
                primal_attempts+=1
                try:value=objective(texts,vocab)
                except ValueError:
                    primal_infeasible+=1;continue  # optional alphabet may not cover; never a primal witness
                if generated_cost is None or value<generated_cost:generated_cost=value;generated_vocab=vocab
                if value<upper:upper=value;best_vocab=vocab
        assert bound<=upper+1e-6
        x=np.zeros(len(pool));x[chosen]=1;gradient=y-x[graph.occ_entry];norm=float(gradient@gradient)
        row={'iteration':iteration,'lower_bound':bound,'best_lower_bound':best_bound,'upper_bound':upper,'generated_objective':generated_cost,'theta':theta,'seconds':time.monotonic()-started}
        trace(row);executed+=1
        if norm==0 or upper-best_bound<1:stop='converged';break
        lam=np.maximum(0.,lam+theta*(upper-bound)/norm*gradient)
    certificate,q=graph.certificate(best_lam,capacity,cfg['denominator'])
    return graph,{'best_real_bound':best_bound,'seed_objective':seed_cost,'best_objective':upper,'generated_objective':generated_cost,
                  'certificate':certificate,'primal_attempts':primal_attempts,'primal_infeasible':primal_infeasible,'iterations':executed,'stop':stop,'seconds':time.monotonic()-started},q,best_vocab,generated_vocab


def independent_certificate(texts,pool,mandatory,q,capacity,denominator):
    """Forward DAG, independent substring enumeration/order and Python integers."""
    index={s:i for i,s in enumerate(pool)};mandatory=set(mandatory);sums=[0]*len(pool);cursor=0;total=0
    maxlen=max(map(len,set(pool)|mandatory),default=1)
    for pid,text in sorted(texts.items()):
        distance=[0]+[None]*len(text)
        for i in range(len(text)):
            for n in range(1,min(maxlen,len(text)-i)+1):
                word=text[i:i+n];entry=index.get(word)
                if word in mandatory:penalty=0
                elif entry is not None:
                    penalty=int(q[cursor]);assert penalty>=0;sums[entry]+=penalty;cursor+=1
                else:continue
                if distance[i] is not None:
                    candidate=distance[i]+(10*(n==1)-1)*denominator+penalty;j=i+n
                    if distance[j] is None or candidate<distance[j]:distance[j]=candidate
        assert distance[-1] is not None;total+=distance[-1]
    assert cursor==len(q)
    return total-sum(sorted(sums,reverse=True)[:capacity])
