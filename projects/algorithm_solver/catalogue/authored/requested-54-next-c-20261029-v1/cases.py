"""Separate small reference checks from analytic official-domain maxima."""
import random
from itertools import product,combinations
IDS=[912,919,924,933,943,959]

def small_cases():
    rng=random.Random(54063)
    for n in range(1,7):
        for nums in product([-2,0,1],repeat=n):yield 912,[list(nums)]
    for count in range(1,10):
        for _ in range(20):
            initial=[rng.randrange(5001) for _ in range(count)];ops=['CBTInserter'];rows=[[initial]]
            for _ in range(rng.randrange(1,15)):
                if rng.randrange(3)==0:ops.append('get_root');rows.append([])
                else:ops.append('insert');rows.append([rng.randrange(5001)])
            ops.append('get_root');rows.append([]);yield 919,[ops,rows]
    for n in range(2,5):
        edges=list(combinations(range(n),2))
        for bits in product([0,1],repeat=len(edges)):
            graph=[[int(i==j) for j in range(n)] for i in range(n)]
            for (a,b),on in zip(edges,bits):graph[a][b]=graph[b][a]=on
            for mask in range(1,1<<n):yield 924,[graph,[i for i in range(n) if mask>>i&1]]
    timestamps=[1,2,3000,3001,3002,6001,10**9]
    for mask in range(1,1<<len(timestamps)):
        times=[t for i,t in enumerate(timestamps) if mask>>i&1];yield 933,[['RecentCounter']+['ping']*len(times),[[]]+[[t] for t in times]]
    words=[''.join(p) for p in product('ab',repeat=3)]
    for n in range(1,5):
        for chosen in combinations(words,n):yield 943,[list(chosen)]
    for n in [1,2]:
        for chars in product('/\\ ',repeat=n*n):yield 959,[[''.join(chars[i*n:(i+1)*n]) for i in range(n)]]
    for _ in range(50):
        n=rng.randint(3,6);yield 959,[[''.join(rng.choice('/\\ ') for _ in range(n)) for _ in range(n)]]

def boundary_cases():
    yield 912,[list(range(50000,0,-1))],list(range(1,50001)),'Maximum length reversed distinct input; known ascending range.'
    yield 912,[[-50000,50000]*25000],[-50000]*25000+[50000]*25000,'Maximum length and both value extrema; half at each value.'
    initial=list(range(1000));ops=['CBTInserter']+['insert']*9999+['get_root'];rows=[[initial]]+[[5000]]*9999+[[]]
    expected=[None]+[(index-1)//2 if (index-1)//2<1000 else 5000 for index in range(1000,10999)]+[initial+[5000]*9999]
    yield 919,[ops,rows],expected,'Maximum initial1000 nodes, exactly10000 methods, maximal inserted value; complete-tree parent index=floor((index-1)/2).'
    yield 924,[[[1]*300 for _ in range(300)],list(range(300))],0,'Complete graph with all seeds: removing any seed changes nothing; minimum index wins.'
    yield 924,[[[int(i==j) for j in range(300)] for i in range(300)],[299]],299,'Single seed in isolated maximum graph; removing it eliminates all infection.'
    times=list(range(10**9-9999,10**9+1))
    yield 933,[['RecentCounter']+['ping']*10000,[[]]+[[t] for t in times]],[None]+[min(i,3001) for i in range(1,10001)],'Exactly10000 pings reaching1e9; inclusive unit-spaced3000ms window contains3001 pings.'
    words=[chr(97+i)*20 for i in range(12)]
    yield 943,[words],240,'Maximum12 words each20 letters, disjoint alphabets; no cross-word overlap possible, so all240 letters required.'
    yield 959,[[' '*30]*30],1,'Maximum dimension blank square has a single connected region.'
    yield 959,[['/'*30]*30],60,'Parallel slash diagonals x+y=1..59 span the square, creating60 regions.'
