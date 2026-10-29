"""Private case generation from file-local independent references."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_r22b_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain

def _tie_free(grid):
    try:validate_domain(749,[grid]);return True
    except ValueError:return False

def _special_strings(length):
    out=[]
    for bits in itertools.product('10',repeat=length):
        s=''.join(bits)
        if _o.special(s):out.append(s)
    return out

def _code(i):
    letters=[]
    for _ in range(7):letters.append(chr(97+i%26));i//=26
    return ''.join(letters)

def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==745:
        small=[''.join(v) for n in range(1,4) for v in itertools.product('ab',repeat=n)]
        args=[[['WordFilter']+['f']*len(small)**2,[[small]]+[[p,q] for p in small for q in small]]]
        for _ in range(200):
            words=[''.join(rng.choice('abc') for _ in range(rng.randrange(1,5))) for _ in range(rng.randrange(1,9))]
            queries=[[''.join(rng.choice('abc') for _ in range(rng.randrange(1,5))),''.join(rng.choice('abc') for _ in range(rng.randrange(1,5)))] for _ in range(12)]
            args.append([['WordFilter']+['f']*len(queries),[[words]]+queries])
        words=[''.join(rng.choice('ab') for _ in range(7)) for _ in range(300)]
        queries=[[w[:rng.randrange(1,8)],w[-rng.randrange(1,8):]] for w in rng.sample(words,100)]+[['abababab'[:7],'b'],['a'*7,'a'*7],['zz','zz']]
        args.append([['WordFilter']+['f']*len(queries),[[words]]+queries])
    elif pid==749:
        for rows,cols in [(1,1),(1,4),(2,2),(2,3),(3,3)]:
            for bits in itertools.product([0,1],repeat=rows*cols):
                grid=[list(bits[r*cols:(r+1)*cols]) for r in range(rows)]
                if _tie_free(grid):args.append([grid])
        for size,density in [(5,0.2),(6,0.3),(8,0.15),(10,0.1),(12,0.25)]:
            made=0
            while made<30:
                grid=[[int(rng.random()<density) for _ in range(size)] for _ in range(size)]
                if _tie_free(grid):args.append([grid]);made+=1
    elif pid==753:args=[[n,k] for n in range(1,5) for k in range(1,11) if k**n<=4096]
    elif pid==756:
        patterns=[''.join(v) for v in itertools.product('AB',repeat=3)]
        for n in range(2,5):
            for bottom in itertools.product('AB',repeat=n):
                for mask in range(256):args.append([''.join(bottom),[patterns[i] for i in range(8) if mask>>i&1]])
        full=[''.join(v) for v in itertools.product('ABCDEF',repeat=3)]
        for density in (0.05,0.1,0.2,0.35,0.6):
            for _ in range(40):
                args.append([''.join(rng.choice('ABCDEF') for _ in range(rng.randrange(5,7))),[p for p in full if rng.random()<density]])
    elif pid==757:
        args=[[[[a,b]]] for a in range(9) for b in range(a+1,10)]
        for _ in range(400):
            intervals=[]
            for _ in range(rng.randrange(1,8)):
                a=rng.randrange(0,9);intervals.append([a,rng.randrange(a+1,10)])
            args.append([intervals])
        args += [[[[i,i+1] for i in range(11)]],[[[0,11]]*5],[[[i,11-i] for i in range(6)]]]
    elif pid==761:args=[[s] for n in range(2,15,2) for s in _special_strings(n)]
    elif pid==765:
        args=[[[*v]] for n in (4,6) for v in itertools.permutations(range(n))]
        for length in (8,10,12):
            for _ in range(40):args.append([rng.sample(range(length),length)])
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        extra=[]
        if pid==745:
            distinct=[_code(i) for i in range(10000)]
            extra=[([['WordFilter']+['f']*10000,[[distinct]]+[[w,w[-1:]] for w in distinct]],[None]+list(range(10000))),
                   ([['WordFilter']+['f']*10000,[[['a'*7]*10000]]+[['a','a'] if i%2 else ['b','a'] for i in range(10000)]],[None]+[9999 if i%2 else -1 for i in range(10000)])]
        if pid==749:
            extra=[([[[0]*50 for _ in range(50)]],0),([[[1]*50 for _ in range(50)]],0),([[[int(r==25 and c==25) for c in range(50)] for r in range(50)]],4),([[[int(c==0) for c in range(50)] for r in range(50)]],50)]
            made=0;seed=0
            while made<6:
                local=random.Random(7490000+seed);seed+=1;density=(0.02,0.05,0.1,0.2,0.4,0.6)[made]
                grid=[[int(local.random()<density) for _ in range(50)] for _ in range(50)]
                if _tie_free(grid):extra.append(([grid],reference(749,[grid])));made+=1
        if pid==756:
            full=[''.join(v) for v in itertools.product('ABCDEF',repeat=3)]
            extra=[(['ABCDEF',full],True),(['ABCDEF',[]],False),(['FFFFFF',[p for p in full if p[2]!='F']],True),(['AAAAAA',[p for p in full if p[:2]!='AA']],False),(['ABCDEF',[p for p in full if p[2]=='A' and p[:2]!='AA']],False)]
        if pid==757:
            extra=[([[[3*i,3*i+1] for i in range(3000)]],6000),([[[0,10**8]]*3000],2),([[[i,i+1] for i in range(3000)]],3001),([[[i,10**8-i] for i in range(3000)]],2)]
        if pid==761:
            extra=[(['10'*25],'10'*25),(['1'*25+'0'*25],'1'*25+'0'*25),(['10'*23+'1100'],'1100'+'10'*23),(['1'+'10'*24+'0'],'1'+'10'*24+'0')]
        if pid==765:
            extra=[([list(range(60))],0),([list(range(1,60))+[0]],29),([list(range(59,-1,-1))],0)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
