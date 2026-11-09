"""Overlap-aware literal shortlist; a monotone surrogate, never an optimality claim."""
from collections import defaultdict
import heapq


def select(sources, metadata, candidates, width, count):
    pool=set(candidates);occ=defaultdict(list);weights={}
    for pid,source in sources.items():
        raw=source.encode();weights[pid]=[9.0]*len(raw);tokens=metadata.get(pid,{}).get('tokens',[])
        seen=set()
        for i,(a,_) in enumerate(tokens):
            for j in range(i,min(i+8,len(tokens))):
                b=tokens[j][1]
                if b-a>160:break
                text=raw[a:b]
                if text in pool and (text,a,b) not in seen:
                    seen.add((text,a,b));occ[text].append((pid,a,b))
    for values in occ.values():values.sort()
    def score(text):
        total=0.0;last={}
        for pid,a,b in occ[text]:
            if a<last.get(pid,0):continue
            saving=sum(weights[pid][a:b])-width
            if saving>0:total+=saving;last[pid]=b
        return total
    heap=[(-score(t),t) for t in candidates];heapq.heapify(heap);selected=[]
    while heap and len(selected)<count:
        bound,text=heapq.heappop(heap);actual=score(text)
        if heap and actual < -heap[0][0]-1e-8:
            heapq.heappush(heap,(-actual,text));continue
        selected.append(text);last={}
        for pid,a,b in occ[text]:
            if a<last.get(pid,0):continue
            if sum(weights[pid][a:b])>width:
                density=width/(b-a)
                for i in range(a,b):weights[pid][i]=min(weights[pid][i],density)
                last[pid]=b
    return selected


def packet_score(sources, fragments, width):
    """Exact two-state FSP bit cost; final packets are checked by existing codec."""
    trie={}
    for part in fragments:
        node=trie
        for b in part:node=node.setdefault(b,{})
        node[None]=True
    total=0
    for source in sources.values():
        raw=source.encode();n=len(raw);normal=[0]*(n+1);opened=[0]*(n+1);opened[n]=1
        for i in range(n-1,-1,-1):
            best=width+9+opened[i+1];node=trie;j=i
            while j<n and raw[j] in node:
                node=node[raw[j]];j+=1
                if None in node:best=min(best,width+normal[j])
            normal[i]=best;opened[i]=min(9+opened[i+1],1+best)
        total+=(9+(normal[0]+7)//8)*8
    return total
