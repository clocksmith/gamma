"""Exact additive DAG objectives for a fixed literal dictionary and fixed source."""


def encode(text,vocab,policy):
    assert policy in ('canonical','shortest_min_char','shortest_max_char','min_char')
    tree={}
    for i,word in enumerate(vocab):
        assert word
        node=tree
        for c in word:node=node.setdefault(c,{})
        node[None]=i
    size=len(text);cost=[None]*(size+1);edge=[None]*size;cost[size]=(0,0)
    for pos in range(size-1,-1,-1):
        node=tree;end=pos
        while end<size and text[end] in node:
            node=node[text[end]];end+=1
            if None not in node or cost[end] is None:continue
            i=node[None];char=int(len(vocab[i])==1)
            add=(1,0) if policy=='canonical' else (1,char) if policy=='shortest_min_char' else (1,-char) if policy=='shortest_max_char' else (char,1)
            value=tuple(a+b for a,b in zip(add,cost[end]))
            if cost[pos] is None or (value,i)<(cost[pos],edge[pos][0]):cost[pos]=value;edge[pos]=(i,end)
    if cost[0] is None:raise ValueError('unrepresentable')
    seq=[];pos=0
    while pos<size:
        i,pos=edge[pos];seq.append(i)
    return seq
