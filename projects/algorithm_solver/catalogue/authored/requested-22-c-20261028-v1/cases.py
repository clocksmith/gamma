"""Private case generation from file-local independent references."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_r22c_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain
TWO_LETTER=[a+b for a in 'abcdefghijklmnopqrstuvwxyz' for b in 'abcdefghijklmnopqrstuvwxyz']
def expression(rng,names,depth):
    if depth==0 or rng.random()<0.25:return rng.choice(names) if rng.random()<0.6 else str(rng.randrange(0,30))
    text=expression(rng,names,depth-1)+' '+rng.choice('+-*')+' '+expression(rng,names,depth-1)
    return '('+text+')' if rng.random()<0.45 else text
def chessboard(n,first):
    return [[first^((i+j)&1) for j in range(n)] for i in range(n)]
def permuted(board,rng):
    n=len(board);rows=rng.sample(range(n),n);cols=rng.sample(range(n),n)
    return [[board[r][c] for c in cols] for r in rows]
def split_parity(board):
    order=list(range(0,len(board),2))+list(range(1,len(board),2))
    return [[board[r][c] for c in order] for r in order]
def chain(values):
    return {'values':values}
def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==770:
        names=['a','b','e','x','ab','ba','zz','temp']
        args=[['0',[],[]],['7',[],[]],['a',[],[]],['a',['a'],[0]],['a - a',[],[]],['ab * a * ba',[],[]],['((x))',['x'],[-4]]]
        while len(args)<400:
            text=expression(rng,names,rng.randrange(1,6))
            if len(text)>250:continue
            fixed=rng.sample(names,rng.randrange(0,4));row=[text,fixed,[rng.randrange(-100,101) for _ in fixed]]
            try:validate_domain(pid,row)
            except ValueError:continue
            args.append(row)
    elif pid==782:
        args=[[[list(r) for r in zip(*[iter(bits)]*n)]] for n in (2,3) for bits in itertools.product([0,1],repeat=n*n)]
        for n,count in ((4,150),(5,25)):
            args += [[permuted(chessboard(n,rng.randrange(2)),rng)] for _ in range(count)]
            args += [[[[rng.randrange(2) for _ in range(n)] for _ in range(n)]] for _ in range(count)]
    elif pid==799:
        args=[[p,r,g] for p in range(13) for r in range(6) for g in range(r+1)]
        for _ in range(300):
            r=rng.randrange(100);args.append([int(10**rng.uniform(0,9)),r,rng.randrange(r+1)])
    elif pid==803:
        cells=[[0,0],[0,1],[1,0],[1,1]]
        for bits in itertools.product([0,1],repeat=4):
            for k in range(1,5):
                for hits in itertools.permutations(cells,k):args.append([[list(bits[:2]),list(bits[2:])],[list(h) for h in hits]])
        for m,n,count,density in ((3,3,150,0.7),(6,5,150,0.6),(15,15,30,0.75)):
            for _ in range(count):
                grid=[[int(rng.random()<density) for _ in range(n)] for _ in range(m)]
                hits=rng.sample([[r,c] for r in range(m) for c in range(n)],rng.randrange(1,min(m*n,100)+1))
                args.append([grid,hits])
    elif pid==805:
        args=[[list(v)] for n in range(1,6) for v in itertools.product(range(4),repeat=n)]
        for _ in range(200):args.append([[rng.randrange(0,10**4+1) for _ in range(rng.randrange(13,31))]])
        for _ in range(100):
            nums=[rng.randrange(0,10**4+1) for _ in range(30)]
            while any(sum(nums)%p==0 for p in (2,3,5)):nums[-1]=rng.randrange(0,10**4+1)
            args.append([nums])
    elif pid==808:
        args=[[n] for n in range(0,600)]
        args += [[25*m+d] for m in range(24,1001) for d in (-24,0) if 25*m+d>=600]
        args += [[rng.randrange(25001,10**9+1)] for _ in range(50)]
    elif pid==817:
        for n in range(1,5):
            for order in itertools.permutations(range(n)):
                for k in range(1,n+1):
                    for nums in itertools.combinations(range(n),k):args.append([chain(list(order)),list(nums)])
        for _ in range(200):
            n=rng.randrange(5,40);order=rng.sample(range(n),n);args.append([chain(order),rng.sample(range(n),rng.randrange(1,n+1))])
    elif pid==818:
        args=[[t] for t in range(1,2001)]+[[rng.randrange(2001,10**4+1)] for _ in range(300)]
        args += [[v] for k in range(11,14) for v in (2**k-1,2**k,2**k+1)]+[[9999],[10000]]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if pid in _o.FLOAT_TOLERANCE:
        for row in rows:row['comparison']={'kind':'absolute-finite-float','absolute_tolerance':_o.FLOAT_TOLERANCE[pid]}
    if include_maximum:
        extra=[]
        if pid==770:
            # Output-size bound inferred from the qualification sandbox (1 GiB, 3 CPU s), not a statement constraint:
            # a full-length 21-factor distinct product has 2**21 answer terms, which no program can emit inside it.
            pairs=[TWO_LETTER[2*i:2*i+2] for i in range(14)];product=' * '.join('('+a+' + '+b+')' for a,b in pairs)
            repeated=' * '.join(['(a + b)']*25)
            names=['q'*20]+[TWO_LETTER[100+i]+'x'*18 for i in range(99)]
            extra=[(['1'+' + 1'*62,[],[]],['63']),(['('*124+'a'+')'*124,[],[]],['1*a']),(['2147483647 - a + a',[],[]],['2147483647']),
                   (['(65535 * a + 1) * (32768 * a - 1)',[],[]],['2147450880*a*a','-32767*a','-1']),
                   ([' + '.join(names[:11]),names,[-100]+[i%201-100 for i in range(99)]],[str(-100+sum(i%201-100 for i in range(10)))]),
                   ([product,[],[]],['1*'+'*'.join(choice) for choice in itertools.product(*pairs)]),([repeated,[],[]],None)]
        if pid==782:
            extra=[([chessboard(30,1)],0),([split_parity(chessboard(30,0))],14),([split_parity(chessboard(29,1))],14),
                   ([[[0]*30 for _ in range(30)]],-1),([[[1-v if (i,j)==(17,4) else v for j,v in enumerate(row)] for i,row in enumerate(chessboard(30,0))]],-1)]
        if pid==799:extra=[([10**9,99,g],None) for g in (0,1,49,50,98,99)]+[([0,99,49],0.0)]
        if pid==803:
            full=[[1]*200 for _ in range(200)];rowmajor=[[r,c] for r in range(200) for c in range(200)];colmajor=[[r,c] for c in range(200) for r in range(200)]
            extra=[([full,rowmajor],[0]*199+[39800]+[0]*39800),([full,colmajor],[0]*39800+[199]+[0]*199),([full,rowmajor[::-1]],[0]*40000),
                   ([[[0]*200 for _ in range(200)],rowmajor],[0]*40000),([[[1]*200]+[[0]*200 for _ in range(199)],colmajor],[0]*40000)]
        if pid==805:extra=[([[10**4]*30],True),([[0]*29+[10**4]],False),([[0]*30],True),([[1]*29+[0]],False)]
        if pid==808:extra=[([10**9],1.0),([0],0.5)]
        if pid==817:
            n=10**4;order=random.Random(8170).sample(range(n),n)
            extra=[([chain(list(range(n))),list(range(0,n,2))],5000),([chain(list(range(n))),list(range(n))],1),([chain(list(range(n-1,-1,-1))),[v for v in range(n) if v%3]],3333),
                   ([chain(order),sorted(random.Random(8171).sample(range(n),n//2))],None)]
        if pid==818:extra=[([10**4],None),([8191],13)]
        for a,expected in extra:
            validate_domain(pid,a)
            if expected is None:expected=reference(pid,a)
            row={'args':a,'expected':expected,'category':'analytic-maximum','isolate':True}
            if pid in _o.FLOAT_TOLERANCE:row['comparison']={'kind':'absolute-finite-float','absolute_tolerance':_o.FLOAT_TOLERANCE[pid]}
            rows.append(row)
    return rows
