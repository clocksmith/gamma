"""Private-packet generator; imports independent references only."""
import itertools
import random
from oracles import reference,validate_domain

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==3741:
        args=[[[*v]] for n in range(1,6) for v in itertools.product(range(1,min(n,3)+1),repeat=n)]
    elif pid==3742:
        for m,n in [(1,1),(1,4),(2,2),(2,3),(3,2),(4,4)]:
            for _ in range(20):
                grid=[[rng.randrange(3) for _ in range(n)] for _ in range(m)];grid[0][0]=0
                args.append([grid,rng.randrange(m+n+1)])
    elif pid==3746:args=[[ ''.join(v)] for n in range(1,9) for v in itertools.product('ab',repeat=n)]
    elif pid==3747:args=[[n] for n in list(range(1,301))+[999,1000,1001,9999,10000,10101]]
    elif pid==3748:
        for _ in range(100):
            n=rng.randrange(1,16);a=[rng.randrange(1,8) for _ in range(n)];q=[]
            for _ in range(10):
                left=rng.randrange(n);q.append([left,rng.randrange(left,n)])
            args.append([a,q])
    elif pid in (3751,3753):
        args=[[n,n+30] for n in [1,90,98,120,198,999,1000,4848,9990]]
        args += [[rng.randrange(1,90000),0] for _ in range(70)]
        for row in args:
            if row[1]==0:row[1]=row[0]+rng.randrange(100)
        if pid==3753:args += [[10**15-100,10**15],[999999999999000,999999999999999],[101010101010101,101010101010101]]
    elif pid==3755:
        args=[[[*v]] for n in range(1,6) for v in itertools.product(range(4),repeat=n)]
        args += [[[rng.randrange(10**9+1) for _ in range(25)]] for _ in range(40)]
    elif pid==3756:
        for _ in range(100):
            n=rng.randrange(1,80);s=''.join(rng.choice('0000123456789') for _ in range(n));q=[]
            for _ in range(10):
                left=rng.randrange(n);q.append([left,rng.randrange(left,n)])
            args.append([s,q])
        args += [['0',[[0,0]]],['9876543210',[[0,9]]]]
    elif pid==3759:
        args=[[[*v],k] for n in range(1,6) for v in itertools.product(range(1,4),repeat=n) for k in range(n)]
    rows=[]
    for a in args:
        rows.append({'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'})
    if include_maximum:
        extra=[]
        if pid==3741:extra=[([[1]*100000],4),([[i//2+1 for i in range(100000)]],-1)]
        if pid==3742:extra=[([[[0]*200 for _ in range(200)],0],0),([[[0]+[2]*199]+[[2]*200 for _ in range(199)],1000],796)]
        if pid==3746:extra=[(['a'*100000],100000),(['ab'*50000],0)]
        if pid==3747:extra=[([10**15],sum(9**i for i in range(1,16)))]
        if pid==3748:extra=[([[1]*100000,[[0,99999],[50000,99999]]],[5000050000,1250025000])]
        if pid==3751:extra=[([100000,100000],0)]
        if pid==3753:extra=[([10**15,10**15],0)]
        if pid==3755:extra=[([[0,1,0,1]*25000],100000),([[0]*100000],0)]
        if pid==3756:extra=[(['0'*100000,[[0,99999],[1,99998]]],[0,0]),(['1'+'0'*99999,[[0,99999]]],[1])]
        if pid==3759:extra=[([[10**9]*100000,99999],0),([[1]*100000,0],100000)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
