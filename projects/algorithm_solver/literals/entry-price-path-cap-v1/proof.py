"""Item63 explicit supplied-input proof oracle; no corpus loader or optimization.

Shares57's tiny complete-graph baseline. All occurrence penalties, ownership,
price residuals and interval schedules are explicit, unsuitable for corpus use.
"""
import importlib.util
from pathlib import Path
_spec=importlib.util.spec_from_file_location('price63_parent57',Path(__file__).resolve().parents[1]/'owner-path-cap-v1/proof.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)


def certificate(texts,banned,q,lambdas,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(lambdas) is list and lambdas and all(type(v) is int and v>=0 for v in lambdas)
    assert lambdas==sorted(set(lambdas)) and lambdas[0]==0
    assert type(q) is dict
    for edge,value in q.items():
        assert type(edge) is tuple and len(edge)==3 and type(edge[0]) is str
        assert type(edge[1]) is type(edge[2]) is int and type(value) is int and value>=0
    banned=set(banned)
    assert all(type(w) is str and w for w in banned)
    base=parent.certificate(texts,banned,q,capacity,denominator)
    edges=parent.allowed(texts,set(banned));support=base['support'];counts={w:0 for w in support if support[w] is not None}
    for edge,word in edges.items():
        if word in counts:counts[word]+=1
    assert all(v>0 for v in counts.values())
    incoming={pid:[[] for _ in range(len(text)+1)] for pid,text in texts.items()}
    for (pid,start,end),word in edges.items():
        if support[word]==pid:incoming[pid][end].append((start,word,q[pid,start,end]))
    schedules={};residuals={};caps={};prefixes={};affine={}
    for pid,text in sorted(texts.items()):
        schedules[pid]={};residuals[pid]={};caps[pid]={}
        for price in lambdas:
            values=[0]*(len(text)+1);penalties={}
            for end in range(1,len(text)+1):
                best=values[end-1]
                for start,word,penalty in incoming[pid][end]:
                    residual=max(penalty-price//counts[word],0)
                    penalties[start,end]=residual;best=max(best,values[start]+residual)
                values[end]=best
            schedules[pid][price]=values;residuals[pid][price]=penalties;caps[pid][price]=values[-1]
        assert caps[pid][0]==base['owner_caps'][pid]
        affine[pid]=[min(price*t+caps[pid][price] for price in lambdas) for t in range(len(base['owner_prefixes'][pid]))]
        prefix=[min(a,line) for a,line in zip(base['owner_prefixes'][pid],affine[pid])]
        increments=[b-a for a,b in zip(prefix,prefix[1:])]
        assert prefix[0]==0 and all(v>=0 for v in increments) and increments==sorted(increments,reverse=True)
        assert all(a<=b for a,b in zip(prefix,base['capped_prefixes'][pid]))
        prefixes[pid]=prefix
    marginals=sorted(((values[j]-values[j-1],pid,j) for pid,values in prefixes.items() for j in range(1,len(values))),
                     key=lambda v:(-v[0],v[1],v[2]))[:capacity]
    totals=[0];choices=[]
    for value,pid,rank in marginals:totals.append(totals[-1]+value);choices.append((pid,rank,value))
    shared=base['shared_prefix'];rows=[]
    for k in range(capacity+1):
        charge,negj=max((totals[j]+shared[min(capacity-j,len(shared)-1)],-j) for j in range(min(k,len(totals)-1)+1))
        numerator=base['L']-charge
        assert charge<=base['rows'][k]['charge']
        rows.append({'k':k,'charge':charge,'one_owner_slots':-negj,'shared_slots':min(capacity+negj,len(shared)-1),
            'numerator':numerator,'integer_lower_bound':-(-numerator//denominator),
            'charge_reduction_vs57':base['rows'][k]['charge']-charge})
    return {'base57':base,'lambda_family':list(lambdas),'entry_occurrence_counts':counts,
        'residual_penalties':residuals,'price_schedules':schedules,'price_caps':caps,
        'affine_envelopes':affine,'priced_prefixes':prefixes,'one_owner_prefix':totals,'marginal_choices':choices,'rows':rows}
