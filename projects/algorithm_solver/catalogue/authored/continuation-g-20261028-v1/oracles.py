"""Source-free independent bounded references; candidates are never imported."""
from itertools import combinations
from math import isqrt
from functools import lru_cache
import random
IDS=(3760,3761,3765,3766,3767,3770,3775,3776,3777,3780)

def integer(x,lo,hi):return type(x) is int and lo<=x<=hi

def array(x,lo,hi,minimum,maximum):return type(x) is list and minimum<=len(x)<=maximum and all(integer(v,lo,hi) for v in x)

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('Fixed identity and ordered args required')
    if len(args)!=(3 if pid==3767 else 2 if pid==3777 else 1):raise ValueError('Argument count')
    a=args[0]
    if pid==3760:ok=type(a) is str and 1<=len(a)<=100000 and all('a'<=x<='z' for x in a)
    elif pid in (3761,3780):ok=array(a,1,10**9 if pid==3761 else 100000,1 if pid==3761 else 3,100000)
    elif pid==3765:ok=integer(a,1,10**9)
    elif pid==3766:ok=array(a,1,5000,1,5000)
    elif pid==3767:ok=array(a,1,100000,1,100000) and array(args[1],1,100000,len(a),len(a)) and integer(args[2],0,len(a))
    elif pid==3770:ok=integer(a,1,500000)
    elif pid==3775:ok=type(a) is str and 1<=len(a)<=100000 and all('a'<=x<='z' or x==' ' for x in a) and not a.startswith(' ') and not a.endswith(' ') and '  ' not in a
    elif pid==3776:ok=array(a,-10**9,10**9,1,100000) and sum(x<0 for x in a)<=1
    else:
        ok=type(a) is str and 1<=len(a)<=100000 and set(a)<={'A','B'} and type(args[1]) is list and 1<=len(args[1])<=100000
        if ok:
            for q in args[1]:
                if type(q) is not list or not q or type(q[0]) is not int:ok=False;break
                if q[0]==1:ok=len(q)==2 and integer(q[1],0,len(a)-1)
                elif q[0]==2:ok=len(q)==3 and integer(q[1],0,len(a)-1) and integer(q[2],q[1],len(a)-1)
                else:ok=False
                if not ok:break
    if not ok:raise ValueError('Outside exact official domain')

@lru_cache(None)
def prime_divisors():
    limit=31623;flags=bytearray(b'\x01')*(limit+1);flags[0:2]=b'\x00\x00'
    for p in range(2,isqrt(limit)+1):
        if flags[p]:
            for multiple in range(p*p,limit+1,p):flags[multiple]=0
    return tuple(p for p in range(2,limit+1) if flags[p])

def prime(x):
    if x<2:return False
    for p in prime_divisors():
        if p*p>x:break
        if x%p==0:return False
    return True

@lru_cache(None)
def nearest_binary(x):
    for distance in range(x+1):
        for y in (x-distance,x+distance):
            text=bin(y)[2:]
            if text==text[::-1]:return distance
    raise AssertionError('1 provides finite certificate')

def expected(pid,args):
    validate(pid,args);a=args[0]
    if pid==3760:
        if len(set(a))==1:return 1
        if len(a)>16:raise ValueError('Partition reference budget')
        answer=0
        for mask in range(1<<(len(a)-1)):
            starts=[a[0]]+[a[i+1] for i in range(len(a)-1) if mask>>i&1]
            if len(starts)==len(set(starts)):answer=max(answer,len(starts))
        return answer
    if pid==3761:
        if len(a)>1000:
            if len(set(a))==1:return 1 if len(a)>1 and int(str(a[0])[::-1])==a[0] else -1
            raise ValueError('Pair enumeration budget')
        return min((j-i for i in range(len(a)) for j in range(i+1,len(a)) if int(str(a[i])[::-1])==a[j]),default=-1)
    if pid==3765:
        text=str(a);return all(prime(int(text[:i])) and prime(int(text[-i:])) for i in range(1,len(text)+1))
    if pid==3766:return [nearest_binary(x) for x in a]
    if pid==3767:
        b,k=args[1:]
        if len(a)>16:
            if len(set(a))==len(set(b))==1:return len(a)*max(a[0],b[0]) if a[0]>=b[0] else k*a[0]+(len(a)-k)*b[0]
            raise ValueError('Subset reference budget')
        return max(sum(a[i] if mask>>i&1 else b[i] for i in range(len(a))) for mask in range(1<<len(a)) if mask.bit_count()>=k)
    if pid==3770:
        def trial(x):return x>=2 and all(x%d for d in range(2,isqrt(x)+1))
        total=answer=0
        for x in range(2,a+1):
            if trial(x):
                total+=x
                if total>a:break
                if trial(total):answer=total
        return answer
    if pid==3775:
        words=a.split(' ');vowels=lambda word:sum(word.count(c) for c in 'aeiou');target=vowels(words[0])
        return ' '.join(word if i==0 or vowels(word)!=target else ''.join(reversed(word)) for i,word in enumerate(words))
    if pid==3776:
        if sum(a)<0:return -1
        if min(a)>=0:return 0
        sink=next(i for i,x in enumerate(a) if x<0);need=-a[sink]
        if len(a)>10 or need>24:
            donors=[i for i,x in enumerate(a) if x>0]
            if len(donors)==1:
                d=abs(donors[0]-sink);return need*min(d,len(a)-d)
            raise ValueError('Unit allocation DP budget')
        cost={0:0}
        for i,available in enumerate(a):
            if available<=0:continue
            distance=min(abs(i-sink),len(a)-abs(i-sink));following={}
            for supplied,value in cost.items():
                for units in range(min(available,need-supplied)+1):
                    key=supplied+units;following[key]=min(following.get(key,10**30),value+units*distance)
            cost=following
        return cost[need]
    if pid==3777:
        if sum(q[2]-q[1]+1 for q in args[1] if q[0]==2)>1000000:raise ValueError('Subsequence DP budget')
        text=list(a);answers=[]
        for q in args[1]:
            if q[0]==1:text[q[1]]='B' if text[q[1]]=='A' else 'A'
            else:
                l,r=q[1:];best_a=best_b=0
                for c in text[l:r+1]:
                    if c=='A':best_a=max(best_a,best_b+1)
                    else:best_b=max(best_b,best_a+1)
                answers.append(r-l+1-max(best_a,best_b))
        return answers
    if len(a)>80:
        if len(set(a))==1:return 3*a[0]
        raise ValueError('Triple reference budget')
    return max((sum(t) for t in combinations(a,3) if sum(t)%3==0),default=0)

def matches(pid,args,answer,wanted=None):
    if wanted is None:wanted=expected(pid,args)
    if pid==3765:return type(answer) is bool and answer is wanted
    if pid in (3766,3777):return type(answer) is list and all(type(x) is int for x in answer) and answer==wanted
    return type(answer) is type(wanted) and answer==wanted

PUBLIC_EXAMPLES={3760:[(['abab'],2),(['abcd'],4),(['aaaa'],1)],3761:[([[12,21,45,33,54]],1),([[120,21]],1),([[21,120]],-1)],3765:[([23],True),([39],False),([7],True)],3766:[([[1,2,4]],[0,1,1]),([[6,7,12]],[1,0,3])],3767:[([[5,2,10],[10,3,8],2],22),([[10,20,30],[5,15,25],2],60),([[1,2,3],[4,5,6],0],15)],3770:[([20],17),([2],2)],3775:[(['cat and mice'],'cat dna mice'),(['book is nice'],'book is ecin'),(['banana healthy'],'banana healthy')],3776:[([[5,1,-4]],4),([[1,2,-5,2]],6),([[-3,2]],-1)],3777:[(['ABA',[[2,1,2],[1,1],[2,0,2]]],[0,2]),(['ABB',[[2,0,2],[1,2],[2,0,2]]],[1,0]),(['BABA',[[2,0,3],[1,1],[2,1,3]]],[0,1])],3780:[([[4,2,3,1]],9),([[2,1,5]],0)]}

def build_cases(pid):
    rng=random.Random(20261028+pid);rows=[{'args':args,'expected':wanted,'tag':'public example'} for args,wanted in PUBLIC_EXAMPLES[pid]];generated=[]
    for _ in range(24):
        n=rng.randint(1,8)
        if pid==3760:args=[''.join(rng.choice('abcd') for _ in range(n))]
        elif pid==3761:args=[[rng.choice([1,10,12,21,120,33,40,4,10**9]) for _ in range(n)]]
        elif pid==3765:args=[rng.randint(1,10**9)]
        elif pid==3766:args=[[rng.randint(1,5000) for _ in range(n)]]
        elif pid==3767:args=[[rng.randint(1,15) for _ in range(n)],[rng.randint(1,15) for _ in range(n)],rng.randint(0,n)]
        elif pid==3770:args=[rng.randint(1,5000)]
        elif pid==3775:args=[' '.join(''.join(rng.choice('abcdeiouxyz') for _ in range(rng.randint(1,8))) for _ in range(n))]
        elif pid==3776:
            values=[rng.randint(0,5) for _ in range(n)];values[rng.randrange(n)]=-rng.randint(0,12);args=[values]
        elif pid==3777:
            text=''.join(rng.choice('AB') for _ in range(n));qs=[]
            for _ in range(12):
                if rng.randrange(2):qs.append([1,rng.randrange(n)])
                else:
                    l=rng.randrange(n);qs.append([2,l,rng.randrange(l,n)])
            args=[text,qs]
        else:args=[[rng.randint(1,100000) for _ in range(max(n,3))]]
        generated.append(args)
    edges={3760:[['a'*100000],['z']],3761:[[[11]*100000],[[10]*100000],[[1]],[[10,1]],[[1,10]]],3765:[[1],[10**9],[2],[3797]],3766:[[[5000]*5000],[[1]],[[4095,4096,4097]]],3767:[[[100000]*100000,[1]*100000,100000],[[1]*100000,[100000]*100000,1]],3770:[[1],[500000]],3775:[['z'*100000],['rhythm crypt fly'],['a b c']],3776:[[[-10**9]+[0]*49999+[10**9]+[0]*49999],[[-1]],[[0]*100000]],3777:[['A'*100000,[[2,0,99999],[1,50000],[2,0,99999],[1,50000],[2,0,99999]]],['A',[[2,0,0],[1,0],[2,0,0]]]],3780:[[[100000]*100000],[[99999]*100000],[[1,1,1]]]}[pid]
    seen={repr(row['args']) for row in rows}
    for args in generated+edges:
        key=repr(args)
        if key not in seen:seen.add(key);rows.append({'args':args,'expected':expected(pid,args),'tag':'seeded reference or boundary'})
    return rows
cases=build_cases
