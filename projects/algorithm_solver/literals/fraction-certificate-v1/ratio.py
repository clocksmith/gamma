"""Exact aggregate character/selection ratio, integer Dinkelbach on finite DAG paths."""
from fractions import Fraction


def trie(vocab):
    root={}
    for code,word in enumerate(vocab):
        assert word
        node=root
        for ch in word:node=node.setdefault(ch,{})
        assert None not in node
        node[None]=code
    return root


def encode(text,vocab,tree,p,q):
    """Minimize (q*C-p*N, N, ID sequence) without floating point."""
    n=len(text);cost=[None]*(n+1);steps=[None]*n;cost[n]=(0,0)
    for i in range(n-1,-1,-1):
        node=tree;best=None
        for j in range(i,n):
            node=node.get(text[j])
            if node is None:break
            code=node.get(None)
            if code is not None and cost[j+1] is not None:
                value=(q*int(len(vocab[code])==1)-p+cost[j+1][0],1+cost[j+1][1],code)
                if best is None or value<best:best=value;steps[i]=(code,j+1)
        if best is not None:cost[i]=best[:2]
    if cost[0] is None:raise ValueError('unencodable source')
    seq=[];i=0
    while i<n:
        code,i=steps[i];seq.append(code)
    return seq,cost[0]


def counts(vocab,seq):return sum(len(vocab[i])==1 for i in seq),len(seq)


def solve(texts,vocab,max_iterations=64):
    """One shared p/q optimizes sums across the complete supplied text group."""
    tree=trie(vocab);initial={pid:encode(t,vocab,tree,0,0)[0] for pid,t in sorted(texts.items())}
    C=sum(counts(vocab,s)[0] for s in initial.values());N=sum(map(len,initial.values()))
    if not N:raise ValueError('empty aggregate')
    ratio=Fraction(C,N);history=[]
    for iteration in range(max_iterations):
        p,q=ratio.numerator,ratio.denominator;sequences={};transformed=0
        for pid,text in sorted(texts.items()):
            seq,cost=encode(text,vocab,tree,p,q);sequences[pid]=seq;transformed+=cost[0]
        C=sum(counts(vocab,s)[0] for s in sequences.values());N=sum(map(len,sequences.values()))
        assert transformed==q*C-p*N and transformed<=0
        history.append({'iteration':iteration,'p':p,'q':q,'characters':C,'selections':N,'minimum_transformed_cost':transformed})
        if transformed==0:
            assert Fraction(C,N)==ratio
            return sequences,{'p':p,'q':q,'characters':C,'selections':N,'iterations':history,'certified':True}
        updated=Fraction(C,N);assert updated<ratio;ratio=updated
    raise RuntimeError('fractional iteration cap; no optimum claimed')


def certificate(texts,vocab,p,q):
    """Independent forward DAG: enumerate vocab strings, not encoder trie/backpointers."""
    minima={}
    for pid,text in sorted(texts.items()):
        values=[None]*(len(text)+1);values[0]=(0,0)
        for i in range(len(text)):
            if values[i] is None:continue
            for word in vocab:
                if text.startswith(word,i):
                    j=i+len(word);candidate=(values[i][0]+q*int(len(word)==1)-p,values[i][1]+1)
                    if values[j] is None or candidate<values[j]:values[j]=candidate
        if values[-1] is None:raise ValueError('certificate source unencodable')
        minima[pid]={'minimum_transformed_cost':values[-1][0],'minimum_selections_at_cost':values[-1][1]}
    return minima
