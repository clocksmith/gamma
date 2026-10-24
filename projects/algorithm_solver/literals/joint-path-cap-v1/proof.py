"""Tiny supplied-input joint path-cap oracle. No loader or corpus algorithm."""
from heapq import heappop,heappush


def allowed(texts,banned):
    return {(p,i,j):t[i:j] for p,t in texts.items() for i in range(len(t))
            for j in range(i+1,len(t)+1) if t[i:j] not in banned}


def prefix(words,weights,B):
    chosen=sorted(words,key=lambda w:(-weights.get(w,0),w))[:B]
    values=[0]
    for w in chosen:values.append(values[-1]+weights.get(w,0))
    return values,chosen


def allocate(prefixes,capacity):
    """Exact at-most capacity allocation for finite concave owner sequences.

    Nonzero f_p(0) is a baseline, not an entry marginal. Zero increments remain
    finite real-entry slots, with owner/rank ties preserving prefix closure.
    """
    heap=[];totals=[sum(values[0] for values in prefixes.values())];choices=[]
    for p,values in sorted(prefixes.items()):
        increments=[b-a for a,b in zip(values,values[1:])]
        assert all(v>=0 for v in increments) and increments==sorted(increments,reverse=True)
        if increments:heappush(heap,(-increments[0],p,1))
    while heap and len(choices)<capacity:
        negative,p,rank=heappop(heap);totals.append(totals[-1]-negative);choices.append((p,rank,-negative))
        v=prefixes[p]
        if rank+1<len(v):heappush(heap,(-(v[rank+1]-v[rank]),p,rank+1))
    return totals,choices


def certificate(texts,banned,q,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    assert type(denominator) is int and denominator>0
    assert texts and all(type(p) is str and type(t) is str and t for p,t in texts.items())
    edges=allowed(texts,set(banned));assert set(q)==set(edges)
    assert all(type(v) is int and v>=0 for v in q.values())
    owners={};weights={};local={p:{} for p in texts}
    incoming={p:[[] for _ in range(len(t)+1)] for p,t in texts.items()}
    outgoing={p:[[] for _ in t] for p,t in texts.items()}
    for edge,w in edges.items():
        p,i,j=edge;v=q[edge];owners.setdefault(w,set()).add(p);weights[w]=weights.get(w,0)+v
        local[p][w]=local[p].get(w,0)+v
        incoming[p][j].append((i,w,v));outgoing[p][i].append((j,w,v))
    support={w:next(iter(ps)) if len(ps)==1 else None for w,ps in owners.items()}
    shared_words=[w for w in weights if support[w] is None]
    owner_words={p:[w for w in weights if support[w]==p] for p in texts}
    Ap={};owner_top={};Sp={};shared_local_top={}
    for p in sorted(texts):
        Ap[p],owner_top[p]=prefix(owner_words[p],weights,capacity)
        # Absent shared entries have local weight zero. Keeping their true entry
        # identities is optional for value, but makes finite counts explicit.
        Sp[p],shared_local_top[p]=prefix(shared_words,local[p],capacity)
    H,shared_top=prefix(shared_words,weights,capacity)
    Rall={};Rone={};all_schedules={};one_schedules={};distances={}
    for p,t in sorted(texts.items()):
        ra=[0]*(len(t)+1);ro=list(ra)
        for j in range(1,len(t)+1):
            ra[j]=max([ra[j-1]]+[ra[i]+v for i,w,v in incoming[p][j]])
            ro[j]=max([ro[j-1]]+[ro[i]+v for i,w,v in incoming[p][j] if support[w]==p])
        Rall[p]=ra[-1];Rone[p]=ro[-1];all_schedules[p]=ra;one_schedules[p]=ro
        d=[None]*len(t)+[0]
        for i in range(len(t)-1,-1,-1):
            values=[denominator*(9 if j-i==1 else -1)+v+d[j] for j,w,v in outgoing[p][i] if d[j] is not None]
            d[i]=min(values) if values else None
        assert d[0] is not None,'full allowed graph has no covering path'
        distances[p]=d
    old_functions={p:[min(a,Rone[p]) for a in Ap[p]] for p in Ap}
    U,old_choices=allocate(old_functions,capacity)
    alternatives=[]
    for j in range(len(U)):
        s=capacity-j
        functions={p:[min(Sp[p][min(s,len(Sp[p])-1)]+a,Rall[p]) for a in Ap[p]] for p in Ap}
        totals,choices=allocate(functions,j)
        assert len(totals)==j+1
        joint=totals[j];prior=H[min(s,len(H)-1)]+U[j]
        alternatives.append({'one_owner_slots':j,'shared_slots':s,'joint_charge':joint,'prior57_charge':prior,
                             'charge':min(joint,prior),'owner_functions':functions,'allocation_choices':choices})
    L=sum(d[0] for d in distances.values());rows=[]
    for k in range(capacity+1):
        candidates=alternatives[:min(k,len(alternatives)-1)+1]
        selected=max(candidates,key=lambda a:(a['charge'],-a['one_owner_slots']))
        T=selected['charge'];old=max(a['prior57_charge'] for a in candidates);assert T<=old
        numerator=L-T
        rows.append({'k':k,'charge':T,'prior57_charge':old,'one_owner_slots':selected['one_owner_slots'],
                     'numerator':numerator,'integer_lower_bound':-(-numerator//denominator)})
    return {'L':L,'distances':distances,'weights':weights,'local_weights':local,'support':support,
      'owner_prefixes':Ap,'owner_top_entries':owner_top,'shared_prefix':H,'shared_top_entries':shared_top,
      'local_shared_prefixes':Sp,'local_shared_top_entries':shared_local_top,'all_caps':Rall,'one_owner_caps':Rone,
      'all_schedule_values':all_schedules,'one_owner_schedule_values':one_schedules,
      'prior57_one_owner_prefix':U,'prior57_choices':old_choices,'alternatives':alternatives,'rows':rows}
