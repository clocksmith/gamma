"""Independent source-free bounded references; no candidate imports."""
from collections import Counter
from functools import lru_cache
from itertools import combinations, combinations_with_replacement, product
from fractions import Fraction
from math import factorial
import random
IDS=(3839,3843,3844,3845,3847,3848,3849,3850,3853,3854)

def integer(x,l,h):return type(x) is int and l<=x<=h

def array(x,l,h,mn,mx):return type(x) is list and mn<=len(x)<=mx and all(integer(v,l,h) for v in x)

def letters(s,mn,mx,alphabet):return type(s) is str and mn<=len(s)<=mx and set(s)<=set(alphabet)

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list or len(args)!=(2 if pid in (3839,3845,3849,3850,3853) else 1):raise ValueError('Fixed identity and ordered args')
    a=args[0]
    if pid==3839:ok=type(a) is list and 1<=len(a)<=5000 and all(letters(s,1,100,'abcdefghijklmnopqrstuvwxyz') for s in a) and integer(args[1],1,100)
    elif pid==3843:ok=array(a,1,100000,1,100000)
    elif pid==3844:ok=letters(a,2,2500,'abcdefghijklmnopqrstuvwxyz')
    elif pid==3845:ok=array(a,0,32767,1,40000) and integer(args[1],0,32767)
    elif pid==3847:ok=array(a,1,1000,1,1000)
    elif pid==3848:ok=integer(a,1,10**9)
    elif pid==3849:ok=letters(a,1,200000,'01') and letters(args[1],len(a),len(a),'01')
    elif pid==3850:ok=array(a,1,6,1,19) and integer(args[1],1,10**15)
    elif pid==3853:ok=letters(a,1,100,'abcdefghijklmnopqrstuvwxyz') and integer(args[1],1,len(a))
    else:ok=array(a,-10**9,10**9,1,100000)
    if not ok:raise ValueError('Outside official domain')

@lru_cache(None)
def all_digitorials():
    # d>=8 impossible: d*9!<10^(d-1); enumerate every digit multiset for d<=7.
    found=set();facts=[factorial(i) for i in range(10)]
    for d in range(1,8):
        for digits in combinations_with_replacement(range(10),d):
            value=sum(facts[x] for x in digits)
            if tuple(sorted(map(int,str(value))))==digits:found.add(value)
    return frozenset(found)

def expected(pid,args):
    validate(pid,args);a=args[0]
    if pid==3839:
        k=args[1]
        if len(a)>300:
            if len(set(a))==1:return int(len(a)>1 and len(a[0])>=k)
            raise ValueError('Pair graph budget')
        unseen={i for i,s in enumerate(a) if len(s)>=k};count=0
        while unseen:
            seed=unseen.pop();group={seed};todo=[seed]
            while todo:
                i=todo.pop();neighbors={j for j in unseen if all(a[i][p]==a[j][p] for p in range(k))};unseen-=neighbors;group|=neighbors;todo.extend(neighbors)
            count+=len(group)>=2
        return count
    if pid==3843:
        if len(a)>1000:
            if len(set(a))==1:return a[0]
            if len(set(a))==len(a):return -1
            raise ValueError('Literal frequency budget')
        unique=set(a);counts={x:a.count(x) for x in unique}
        return next((x for x in a if sum(counts[y]==counts[x] for y in unique)==1),-1)
    if pid==3844:
        if len(set(a))==1:return len(a)
        if len(a)>30:raise ValueError('Substring deletion enumeration budget')
        answer=1
        for l in range(len(a)):
            for r in range(l+1,len(a)+1):
                text=a[l:r]
                if any((removed:=text[:i]+text[i+1:])==removed[::-1] for i in range(len(text))):answer=max(answer,len(text))
        return answer
    if pid==3845:
        if len(a)>200:
            if len(set(a))==1:return a[0]
            raise ValueError('Interval XOR enumeration budget')
        answer=0
        for l in range(len(a)):
            for r in range(l,len(a)):
                values=a[l:r+1]
                if max(values)-min(values)<=args[1]:
                    value=0
                    for x in values:value^=x
                    answer=max(answer,value)
        return answer
    if pid==3847:
        active=0;scores=[0,0]
        for i,x in enumerate(a):
            if x%2:active=1-active
            if i%6==5:active=1-active
            scores[active]+=x
        return scores[0]-scores[1]
    if pid==3848:return any(Counter(str(x))==Counter(str(a)) for x in all_digitorials())
    if pid==3849:
        t=args[1];ones=t.count('1')
        if len(set(a))==1:
            output_ones=ones if a[0]=='0' else len(t)-ones
            return '1'*output_ones+'0'*(len(t)-output_ones)
        if len(a)>14:raise ValueError('Binary arrangement enumeration budget')
        outputs=[]
        for positions in combinations(range(len(a)),ones):
            chosen=set(positions);outputs.append(''.join(str(int(c)^int(i in chosen)) for i,c in enumerate(a)))
        return max(outputs)
    if pid==3850:
        k=args[1]
        if all(x==1 for x in a):return 3**len(a) if k==1 else 0
        if len(a)>10:raise ValueError('Exact fraction choice enumeration budget')
        count=0
        for choices in product((-1,0,1),repeat=len(a)):
            value=Fraction(1)
            for x,action in zip(a,choices):
                if action==1:value*=x
                elif action==-1:value/=x
            count+=value==k
        return count
    if pid==3853:
        alive=list(range(len(a)));k=args[1]
        while True:
            pair=next(((i,j) for i in range(len(alive)) for j in range(i+1,min(len(alive),i+k+1)) if a[alive[i]]==a[alive[j]]),None)
            if pair is None:return ''.join(a[i] for i in alive)
            del alive[pair[1]]
    if len(a)==1:return [0,0]
    if len(a)>14:
        if len(set(a))==1:return [len(a)//2,1]
        raise ValueError('Exact minimum operation outcome enumeration budget')
    outcomes=[]
    for first in (0,1):
        wrong=[i for i,x in enumerate(a) if x%2!=(first+i)%2]
        for signs in product((-1,1),repeat=len(wrong)):
            values=a[:]
            for i,d in zip(wrong,signs):values[i]+=d
            outcomes.append((len(wrong),max(values)-min(values)))
    return list(min(outcomes))

def matches(pid,args,result,wanted=None):
    if wanted is None:wanted=expected(pid,args)
    if pid==3848:return type(result) is bool and result is wanted
    if pid==3854:return type(result) is list and all(type(x) is int for x in result) and result==wanted
    return type(result) is type(wanted) and result==wanted

PUBLIC_EXAMPLES={3839:[([['apple','apply','banana','bandit'],2],2),([['car','cat','cartoon'],3],1),([['bat','dog','dog','doggy','bat'],3],2)],3843:[([[20,10,30,30]],30),([[20,20,10,30,30,30]],20),([[10,10,20,20]],-1)],3844:[(['abca'],4),(['abba'],4),(['zzabba'],5)],3845:[([[5,4,5,6],2],7),([[5,4,5,6],1],6)],3847:[([[1,2,3]],0),([[2,4,2,1,2,1]],4),([[1]],-1)],3848:[([145],True),([10],False)],3849:[(['101','011'],'110'),(['0110','1110'],'1101'),(['0101','1001'],'1111')],3850:[([[2,3,2],6],2),([[4,6,3],2],2),([[1,5],1],3)],3853:[(['abca',3],'abc'),(['aabca',2],'abca'),(['yybyzybz',2],'ybzybz')],3854:[([[-2,-3,1,4]],[2,6]),([[0,2,-2]],[1,3]),([[7]],[0,0])]}

def build_cases(pid):
    rng=random.Random(20261028+pid);rows=[{'args':args,'expected':value,'tag':'public example'} for args,value in PUBLIC_EXAMPLES[pid]];generated=[]
    for _ in range(24):
        n=rng.randint(1,7)
        if pid==3839:args=[[''.join(rng.choice('abc') for _ in range(rng.randint(1,6))) for _ in range(n)],rng.randint(1,6)]
        elif pid==3843:args=[[rng.randint(1,4) for _ in range(n)]]
        elif pid==3844:args=[''.join(rng.choice('abc') for _ in range(max(2,n))) ]
        elif pid==3845:args=[[rng.randint(0,31) for _ in range(n)],rng.randint(0,31)]
        elif pid==3847:args=[[rng.randint(1,1000) for _ in range(rng.randint(1,20))]]
        elif pid==3848:args=[rng.randint(1,10**9)]
        elif pid==3849:args=[''.join(rng.choice('01') for _ in range(n)),''.join(rng.choice('01') for _ in range(n))]
        elif pid==3850:args=[[rng.randint(1,6) for _ in range(n)],rng.choice([1,2,3,5,6,7,12,36])]
        elif pid==3853:args=[''.join(rng.choice('abc') for _ in range(n)),rng.randint(1,n)]
        else:args=[[rng.randint(-5,5) for _ in range(n)]]
        generated.append(args)
    edges={3839:[[ ['a'*100]*5000,100],[['a','a'],2]],3843:[[[100000]*100000],[list(range(1,100001))]],3844:[['a'*2500],['ab']],3845:[[[32767]*40000,0],[[0]*40000,32767],[[0,32767,0],0]],3847:[[[1000]*1000],[[1]*12]],3848:[[1],[2],[154],[40585],[10**9],[0+100]],3849:[['0'*200000,'1'*100000+'0'*100000],['1'*200000,'1'*200000]],3850:[[[1]*19,1],[[1]*19,10**15],[[6]*5,7776]],3853:[['a'*100,1],['ab'*50,100]],3854:[[[10**9]*100000],[[-10**9,10**9]],[[-1,0,-1,0]]]}[pid]
    seen={repr(row['args']) for row in rows}
    for args in generated+edges:
        key=repr(args)
        if key not in seen:seen.add(key);rows.append({'args':args,'expected':expected(pid,args),'tag':'seeded independent reference or boundary'})
    return rows
cases=build_cases
