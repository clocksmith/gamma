"""Small supplied-input oracle, not a scalable corpus implementation.

All allowed exact substrings and their occurrence penalties are explicit. The
proof applies to any nonnegative integer penalties, including fixed item53 q.
"""
from heapq import heappop, heappush


def allowed(texts,banned):
    return {(p,i,j):text[i:j] for p,text in texts.items()
            for i in range(len(text)) for j in range(i+1,len(text)+1)
            if text[i:j] not in banned}


def prefix(weights,capacity):
    out=[0]
    for weight in sorted(weights,reverse=True)[:capacity]:out.append(out[-1]+weight)
    return out


def capped_marginals(owner_prefixes,caps,capacity):
    """Stable owner/rank tie order preserves prefixes, even for zero ties."""
    capped={p:[min(x,caps[p]) for x in values] for p,values in owner_prefixes.items()}
    heap=[]
    for p,values in capped.items():
        if len(values)>1:heappush(heap,(-(values[1]-values[0]),p,1))
    total=[0];choices=[]
    while heap and len(choices)<capacity:
        negative,p,j=heappop(heap);total.append(total[-1]-negative);choices.append((p,j,-negative))
        if j+1<len(capped[p]):
            heappush(heap,(-(capped[p][j+1]-capped[p][j]),p,j+1))
    return total,choices,capped


def certificate(texts,banned,q,capacity=256,denominator=1):
    if not __debug__:raise RuntimeError('normal assertions required')
    assert type(capacity) is int and capacity>=0
    assert type(denominator) is int and denominator>0
    assert texts and all(type(p) is str and type(t) is str and t for p,t in texts.items())
    edges=allowed(texts,set(banned));assert set(q)==set(edges)
    assert all(type(value) is int and value>=0 for value in q.values())
    owners={};weights={}
    for edge,word in edges.items():
        owners.setdefault(word,set()).add(edge[0]);weights[word]=weights.get(word,0)+q[edge]
    support={word:next(iter(ps)) if len(ps)==1 else None for word,ps in owners.items()}
    owner_words={p:sorted((w for w in weights if support[w]==p),key=lambda w:(-weights[w],w))
                 for p in sorted(texts)}
    owner_prefix={p:prefix((weights[w] for w in words),capacity) for p,words in owner_words.items()}
    shared=prefix((weights[w] for w in weights if support[w] is None),capacity)
    old_one=prefix((weights[w] for w in weights if support[w] is not None),capacity)
    caps={};distances={};schedules={}
    for p,text in sorted(texts.items()):
        incoming=[[] for _ in range(len(text)+1)];outgoing=[[] for _ in text]
        for (pid,i,j),word in edges.items():
            if pid==p:
                outgoing[i].append((j,word,q[p,i,j]))
                if support[word]==p:incoming[j].append((i,q[p,i,j]))
        best=[0]*(len(text)+1)
        for j in range(1,len(text)+1):
            best[j]=max([best[j-1]]+[best[i]+value for i,value in incoming[j]])
        caps[p]=best[-1];schedules[p]=best
        d=[None]*len(text)+[0]
        for i in range(len(text)-1,-1,-1):
            candidates=[denominator*(9 if j-i==1 else -1)+value+d[j]
                        for j,word,value in outgoing[i] if d[j] is not None]
            d[i]=min(candidates) if candidates else None
        assert d[0] is not None,'full allowed graph has no complete path'
        distances[p]=d
    one,choices,capped=capped_marginals(owner_prefix,caps,capacity)
    L=sum(d[0] for d in distances.values());rows=[]
    for k in range(capacity+1):
        alternatives=[(one[j]+shared[min(capacity-j,len(shared)-1)],j)
                      for j in range(min(k,len(one)-1)+1)]
        charge,j=max(alternatives,key=lambda pair:(pair[0],-pair[1]))
        old=max(old_one[j]+shared[min(capacity-j,len(shared)-1)]
                for j in range(min(k,len(old_one)-1)+1))
        assert charge<=old
        rows.append({'k':k,'charge':charge,'old_charge':old,'one_owner_slots':j,
                     'numerator':L-charge,'integer_lower_bound':-(-(L-charge)//denominator)})
    return {'L':L,'distances':distances,'weights':weights,'support':support,
            'owner_top_entries':{p:words[:capacity] for p,words in owner_words.items()},
            'owner_prefixes':owner_prefix,'owner_caps':caps,'owner_schedule_values':schedules,
            'capped_prefixes':capped,'marginal_choices':choices,'one_owner_prefix':one,
            'shared_prefix':shared,'rows':rows}
