"""Private serialized models; native observer must enforce identity/effects."""
import importlib.util
from pathlib import Path
import itertools
import random
_spec=importlib.util.spec_from_file_location('gamma_q_case_oracles',Path(__file__).with_name('oracles.py'))
_o=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_o)
reference,validate_domain=_o.reference,_o.validate_domain

def tree(values):
    n=len(values)
    return {'values':values,'left':[2*i+1 if 2*i+1<n else None for i in range(n)],'right':[2*i+2 if 2*i+2<n else None for i in range(n)],'root':0 if n else None}
def build_cases(pid,include_maximum=False):
    rng=random.Random(pid);args=[]
    if pid==126:
        args=[['hit','cog',['hot','dot','dog','lot','log','cog']],['hit','cog',['hot','dot','dog','lot','log']]]
        universe=[''.join(v) for v in itertools.product('ab',repeat=3)]
        for _ in range(80):
            begin,end=rng.sample(universe,2);args.append([begin,end,rng.sample(universe,rng.randrange(1,9))])
    elif pid in (129,144):
        for n in range(1 if pid==129 else 0,40):args.append([tree([rng.randrange(3) if pid==129 else rng.randrange(-100,101) for _ in range(n)])])
        args += [[{'values':[1,2,3],'left':[1,None,None],'right':[2,None,None],'root':0}]]
    elif pid==132:args=[[''.join(v)] for n in range(1,10) for v in itertools.product('ab',repeat=n)]
    elif pid==133:
        args=[[{'values':[],'neighbors':[],'root':None}]]
        for n in range(1,13):
            for _ in range(5):
                neighbors=[[] for _ in range(n)]
                for i in range(1,n):
                    j=rng.randrange(i);neighbors[i].append(j);neighbors[j].append(i)
                for i in range(n):
                    for j in range(i+1,n):
                        if j not in neighbors[i] and rng.randrange(4)==0:neighbors[i].append(j);neighbors[j].append(i)
                for row in neighbors:rng.shuffle(row)
                args.append([{'values':list(range(1,n+1)),'neighbors':neighbors,'root':0}])
    elif pid==138:
        for n in range(0,25):
            for _ in range(4):args.append([{'values':[rng.randrange(-2,3) for _ in range(n)],'random':[rng.choice([None]+list(range(n))) for _ in range(n)]}])
    elif pid==140:
        for n in range(1,8):
            for chars in itertools.product('ab',repeat=n):
                s=''.join(chars);words=sorted({s[i:j] for i in range(n) for j in range(i+1,min(n,i+4)+1) if rng.randrange(2)==0}) or ['a'];args.append([s,words])
    elif pid in (141,142):args=[[{'values':[1]*n,'pos':pos}] for n in range(0,20) for pos in range(-1,n)]
    elif pid==143:args=[[{'values':[rng.randrange(1,4) for _ in range(n)]}] for n in range(1,101)]
    rows=[{'args':a,'expected':reference(pid,a),'category':'independent-serialized-model'} for a in args]
    for row in rows:
        if pid in _o.NATIVE:row['requires_native_identity_observer']=True
        if pid in (126,140):row['comparison']={'kind':'unordered-distinct-sequences','duplicates_forbidden':True}
    if include_maximum:
        extra=[]
        if pid==126:
            words=['b'+''.join(chr(97+(i//(26**power))%26) for power in range(3,-1,-1)) for i in range(500)];extra=[(['aaaaa','zzzzz',words],[])]
        if pid==129:extra=[([tree([0]*1000)],0)]
        if pid==132:extra=[(['a'*2000],0),(['ab'*1000],1)]
        if pid==133:
            packet={'values':list(range(1,101)),'neighbors':[[j for j in range(100) if i!=j] for i in range(100)],'root':0};extra=[([packet],packet)]
        if pid==138:
            packet={'values':[1]*1000,'random':[(i+1)%1000 for i in range(1000)]};extra=[([packet],packet)]
        if pid==140:extra=[(['a'*20,['a']],[' '.join(['a']*20)])]
        if pid in (141,142):extra=[([{'values':[1]*10000,'pos':pos}],pos!=-1 if pid==141 else pos if pos!=-1 else None) for pos in (-1,0,9999)]
        if pid==143:
            packet={'values':[1]*50000};extra=[([packet],reference(pid,[packet]))]
        if pid==144:
            packet={'values':[1]*100,'left':[i+1 if i<99 else None for i in range(100)],'right':[None]*100,'root':0};extra=[([packet],[1]*100)]
        for a,expected in extra:
            validate_domain(pid,a);rows.append({'args':a,'expected':expected,'category':'analytic-maximum','isolate':True,'requires_native_identity_observer':pid in _o.NATIVE})
    return rows
