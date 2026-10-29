"""Private case generation from file-local independent references; no official examples."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_r22a_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain,CLASSES=_o.reference,_o.validate_domain,_o.CLASSES
ELEMENTS=['H','He','O','Mg','C','Cl','N','Zz','Ab']
def _formula(rng,depth):
    out=''
    for _ in range(rng.randrange(1,4)):
        if depth and rng.random()<0.35:out+='('+_formula(rng,depth-1)+')'+rng.choice(['','2','3','10','1'])
        else:out+=rng.choice(ELEMENTS)+rng.choice(['','','2','3','12'])
    return out
def _lisp(rng,depth,names):
    roll=rng.random()
    if depth==0 or roll<0.25:
        return rng.choice(names) if names and rng.random()<0.6 else str(rng.randrange(-10,11))
    if roll<0.6:return '('+rng.choice(['add','mult'])+' '+_lisp(rng,depth-1,names)+' '+_lisp(rng,depth-1,names)+')'
    parts=['let'];scope=list(names)
    for _ in range(rng.randrange(1,4)):
        name=rng.choice(['x','y','z','a1','b2']);parts+=[name,_lisp(rng,depth-1,scope)]
        if name not in scope:scope.append(name)
    parts.append(_lisp(rng,depth-1,scope));return '('+' '.join(parts)+')'
def _trace(pid,pairs):return [[CLASSES[pid]]+['book']*len(pairs),[[]]+[list(p) for p in pairs]]
def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==726:
        args=[[f] for f in ['H','HH','HHe','HeH','(H)','((H))','(H)2','(HO)2O','Zz2Ab3','(Ab(Cd2)3)4','Cl(Cl2)1','((N2)3(He)2)5Mg']]
        while len(args)<262:
            f=_formula(rng,3)
            if len(f)<=1000:args.append([f])
    elif pid in CLASSES:
        args=[_trace(pid,[])]
        for _ in range(200):
            pairs=[]
            for _ in range(rng.randrange(1,26)):
                s=rng.randrange(0,15);pairs.append((s,s+rng.randrange(1,6)))
            args.append(_trace(pid,pairs))
        for _ in range(30):
            pairs=[]
            for _ in range(rng.randrange(1,40)):
                a,b=sorted(rng.sample(range(0,10**9+1),2));pairs.append((a,b))
            args.append(_trace(pid,pairs+[(10**9-1,10**9),(0,1)]))
    elif pid==730:
        args=[[''.join(v)] for n in range(1,6) for v in itertools.product('abcd',repeat=n)]
        args+=[[''.join(rng.choice('abcd') for _ in range(rng.randrange(6,13)))] for _ in range(150)]
        args+=[[''.join(rng.choice('abcd') for _ in range(rng.randrange(13,301)))] for _ in range(40)]
    elif pid==736:
        args=[[e] for e in ['5','-7','(add 1 2)','(mult -3 4)','(let x 1 x)','(let x 1 (let x 2 x))','(let x 1 (add (let x 2 x) x))','(let x 2 y x x 5 (add x y))','(let a0 3 a0)','(let x 1 y (let x 7 x) (mult x y))']]
        while len(args)<310:
            e=_lisp(rng,4,[])
            try:validate_domain(pid,[e])
            except ValueError:continue
            args.append([e])
    elif pid==741:
        args=[[[[0]]],[[[1]]]]
        args+=[[[[a,b],[c,d]]] for a in (0,1) for b in (-1,0,1) for c in (-1,0,1) for d in (0,1)]
        for n,count in [(3,200),(4,100),(5,60),(6,30)]:
            for _ in range(count):
                g=[[rng.choice([-1,0,1,1]) for _ in range(n)] for _ in range(n)];g[0][0]=rng.choice([0,1]);g[-1][-1]=rng.choice([0,1]);args.append([g])
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-bounded-reference'} for a in args]
    if include_maximum:
        extra=[]
        if pid==726:
            many=sorted((chr(65+a)+chr(97+b) for a in range(26) for b in range(26)),reverse=True)[:333]
            extra=[(['('*499+'H'+')'*499+'O'],'HO'),(['H'*1000],'H1000'),(['H(H)2147483646'],'H2147483647'),([''.join(many)+'Q'],''.join(sorted(many+['Q'])))]
        if pid==729:extra=[(_trace(pid,[(0,10**9)]*1000),[None,True]+[False]*999),(_trace(pid,[(i*10**6,(i+1)*10**6) for i in range(1000)]),[None]+[True]*1000)]
        if pid==731:extra=[(_trace(pid,[(0,10**9)]*1000),[None,True,True]+[False]*998),(_trace(pid,[(i*10**6,(i+1)*10**6) for i in range(1000)]),[None]+[True]*1000),(_trace(pid,[(i,10**9-i) for i in range(1000)]),[None,True,True]+[False]*998)]
        if pid==732:extra=[(_trace(pid,[(0,10**9)]*400),[None]+list(range(1,401))),(_trace(pid,[(i,10**9-i) for i in range(400)]),[None]+list(range(1,401))),(_trace(pid,[(i*10**6,(i+1)*10**6) for i in range(400)]),[None]+[1]*400)]
        if pid==730:extra=[(['a'*1000],1000),(['d'*1000],1000),(['a'+'b'*998+'a'],1998)]
        if pid==736:
            chain='(let v0 1 '+' '.join(f'v{i} (add v{i-1} 1)' for i in range(1,111))+' v110)'
            extra=[(['(add 1 '*249+'1'+')'*249],250),(['(let x 1 '*199+'x'+')'*199],1),(['(mult 46340 46341)'],46340*46341),(['(add 2147483647 0)'],2147483647),(['(add -2147483648 0)'],-2147483648),([chain],111)]
        if pid==741:
            single=[[1 if r==0 or c==49 else -1 for c in range(50)] for r in range(50)]
            extra=[([[[1]*50 for _ in range(50)]],196),([[[0]*50 for _ in range(50)]],0),([[[-1 if r==25 else 1 for _ in range(50)] for r in range(50)]],0),([[[-1 if r+c==49 else 1 for c in range(50)] for r in range(50)]],0),([single],99)]
        for a,expected in extra:validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True})
    return rows
