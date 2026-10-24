"""Item61 tiny supplied-input theorem oracle; no corpus adapter or I/O loader.

Shares item57's explicit full-graph quantities. The new calculation derives
forced owners and allocates finite capped prefixes with their mandatory slot.
"""
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('required_owner61_parent57',Path(__file__).resolve().parents[1]/'owner-path-cap-v1/proof.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)


def required_allocation(prefixes,forced,capacity):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    assert type(forced) is list and forced==sorted(set(forced)) and set(forced)<=set(prefixes)
    for pid,values in prefixes.items():
        assert type(pid) is str and type(values) is list and values and values[0]==0
        assert all(type(v) is int and v>=0 for v in values)
        increments=[b-a for a,b in zip(values,values[1:])]
        assert increments==sorted(increments,reverse=True) and all(v>=0 for v in increments)
    r=len(forced)
    if r>capacity:return {},[],None
    assert all(len(prefixes[pid])>=2 for pid in forced),'forced owner has no available entry'
    mandatory=set(forced);base=sum(prefixes[pid][1] for pid in forced)
    marginals=[]
    for pid,values in prefixes.items():
        for rank in range(2 if pid in mandatory else 1,len(values)):
            marginals.append((values[rank]-values[rank-1],pid,rank))
    marginals.sort(key=lambda v:(-v[0],v[1],v[2]))
    allocated={pid:int(pid in mandatory) for pid in prefixes}
    totals={r:base};choices=[]
    for value,pid,rank in marginals[:capacity-r]:
        assert rank==allocated[pid]+1
        allocated[pid]+=1;choices.append((pid,rank,value));totals[r+len(choices)]=totals[r+len(choices)-1]+value
    return totals,choices,base


def certificate(texts,banned,q,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    base=parent.certificate(texts,banned,q,capacity,denominator)
    edges=parent.allowed(texts,set(banned));shared={w for w,pid in base['support'].items() if pid is None}
    reachable={};forced=[]
    for pid,text in sorted(texts.items()):
        vector=[True]+[False]*len(text)
        for end in range(1,len(text)+1):
            vector[end]=any(vector[start] and edges.get((pid,start,end)) in shared for start in range(end))
        reachable[pid]=vector
        if not vector[-1]:forced.append(pid)
    counts={pid:sum(owner==pid for owner in base['support'].values()) for pid in texts}
    assert all(counts[pid]>0 for pid in forced),'unreachable in full allowed graph'
    totals,choices,mandatory=required_allocation(base['capped_prefixes'],forced,capacity)
    rows=[];r=len(forced);shared_prefix=base['shared_prefix']
    for k in range(capacity+1):
        if k<r:
            rows.append({'k':k,'empty_by_required_owners':True,'one_owner_slots':None,'shared_slots':None,
                         'charge':None,'numerator':None,'integer_lower_bound':None,'charge_reduction_vs57':None})
            continue
        candidates=[(value+shared_prefix[min(capacity-j,len(shared_prefix)-1)],-j)
                    for j,value in totals.items() if j<=k]
        assert candidates
        charge,negative_j=max(candidates);j=-negative_j;numerator=base['L']-charge
        assert charge<=base['rows'][k]['charge']
        rows.append({'k':k,'empty_by_required_owners':False,'one_owner_slots':j,
                     'shared_slots':min(capacity-j,len(shared_prefix)-1),'charge':charge,'numerator':numerator,
                     'integer_lower_bound':-(-numerator//denominator),
                     'charge_reduction_vs57':base['rows'][k]['charge']-charge})
    return {'base57':base,'forced_owners':forced,'coverage_floor':r,'shared_reachability':reachable,
            'owner_entry_counts':counts,'mandatory_value':mandatory,'required_owner_prefix':totals,
            'remaining_marginal_choices':choices,'rows':rows}
