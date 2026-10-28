"""Independent private-packet generator; no candidate imports."""
import itertools
import random
from oracles import reference,validate_domain

def balanced_full_decimal_blocks():
    total=0
    for length in range(2,16):
        coefficients={0:1}
        for position in range(length):
            following={}
            for power,count in coefficients.items():
                for digit in range(1 if position==0 else 0,10):
                    key=power+(digit if position%2==0 else -digit)
                    following[key]=following.get(key,0)+count
            coefficients=following
        total+=coefficients.get(0,0)
    return total

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==3781:
        for n in range(1,7):
            for word in itertools.product('01',repeat=n):args.append([[rng.randrange(1,20) for _ in range(n)],''.join(word)])
        args += [[[10**9,1,10**9],'001'],[[1,10**9,1],'110']]
    elif pid==3784:
        for n in range(1,7):
            for word in itertools.product('abc',repeat=n):args.append([''.join(word),[rng.randrange(1,20) for _ in range(n)]])
    elif pid==3788:
        args=[[[*v]] for n in range(2,6) for v in itertools.product([-2,0,3],repeat=n)]
        args += [[[rng.randrange(-10**9,10**9+1) for _ in range(30)]] for _ in range(40)]
    elif pid==3789:
        args=[[a,b,c,x,y] for a,b,c in itertools.product([1,3,7],repeat=3) for x,y in itertools.product(range(4),repeat=2)]
    elif pid==3790:args=[[k] for k in range(2,301)]
    elif pid==3791:
        args=[[n,n+50] for n in [1,9,90,99,100,109,999,1000,9990,10000]]
        args += [[rng.randrange(1,10**15-100),0] for _ in range(60)]
        for row in args:
            if row[1]==0:row[1]=row[0]+rng.randrange(100)
        args += [[10**15-50,10**15],[11111111111111,11111111111111],[999999999999999,999999999999999]]
    elif pid==3795:
        args=[[[*v],k] for n in range(1,6) for v in itertools.product([1,2,3],repeat=n) for k in [1,3,6,7]]
    elif pid==3799:
        args=[[['able','area','echo','also']],[['code','cafe','eden','edge']],[['aaaa','aaab','aaba','abaa']]]
        universe=[''.join(x) for x in itertools.product('ab',repeat=4)]
        args += [[rng.sample(universe,rng.randrange(4,11))] for _ in range(50)]
    elif pid==3800:
        args=[[a,b,*costs] for n in range(1,4) for a in map(''.join,itertools.product('01',repeat=n)) for b in map(''.join,itertools.product('01',repeat=n)) for costs in [(1,1,1),(7,2,3),(2,9,9),(5,9,1)]]
        args += [[''.join(rng.choice('01') for _ in range(4)),''.join(rng.choice('01') for _ in range(4)),rng.randrange(1,15),rng.randrange(1,15),rng.randrange(1,15)] for _ in range(30)]
    elif pid==3801:
        for _ in range(80):args.append([[sorted(rng.randrange(-10,11) for _ in range(rng.randrange(1,5))) for _ in range(rng.randrange(2,6))]])
        args += [[[[1,3,5],[2,4],[6,7,8]]],[[[-10**9],[10**9]]],[[[1,1],[1],[1,1,1]]]]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        extra=[]
        if pid==3781:extra=[([[10**9]*100000,'1'*100000],10**14),([[10**9]*100000,'0'*99999+'1'],10**9)]
        if pid==3784:extra=[(['a'*50000+'b'*50000,[10**9]*100000],5*10**13)]
        if pid==3788:extra=[([[10**9]*99999+[-10**9]],10**14)]
        if pid==3789:extra=[([10**6,10**6,10**6,10**9,10**9],10**15),([10**6,10**6,1,10**9,0],10**9)]
        if pid==3790:extra=[([100000],-1),([99999],45)]
        if pid==3791:extra=[([1,10**15],balanced_full_decimal_blocks()),([10**15,10**15],0)]
        if pid==3795:extra=[([[1]*100000,2],-1),([list(range(1,100001)),100000],1)]
        if pid==3799:extra=[([['aaa'+chr(97+i) for i in range(15)]],[])]
        if pid==3800:extra=[(['0'*100000,'1'*100000,10**9,1,1],100000),(['0'*100000,'0'*100000,10**9,10**9,10**9],0)]
        if pid==3801:extra=[([[[0]]*12],44),([[[0]*500 for _ in range(4)]],4000)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
