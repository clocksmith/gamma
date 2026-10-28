"""Independent definition-based references; supplied candidate modules are never imported."""
from collections import Counter, deque
from functools import lru_cache
from itertools import combinations, permutations, product
import heapq
import math
import re

# These functions intentionally use direct enumeration on bounded small cases.
# Larger cases are included only where the reference has a practical exact path.

def powers(primes, n):
    values, seen = [1], {1}
    for _ in range(n):
        value = heapq.heappop(values)
        for p in primes:
            if value*p not in seen:
                seen.add(value*p); heapq.heappush(values, value*p)
    return value


def subsequences(xs):
    for mask in range(1 << len(xs)):
        yield [v for i,v in enumerate(xs) if mask >> i & 1]


def independent(xs, circular=False):
    return max(sum(v for i,v in enumerate(xs) if mask >> i & 1)
               for mask in range(1 << len(xs))
               if not mask & (mask << 1) and
               not (circular and len(xs)>1 and mask&1 and mask>>(len(xs)-1)&1))


def smooth(n, primes):
    return powers(tuple(primes), n)


@lru_cache(None)
def squares(n):
    if not n:return 0
    if math.isqrt(n)**2==n:return 1
    if any(math.isqrt(n-i*i)**2==n-i*i for i in range(1,math.isqrt(n)+1)):return 2
    x=n
    while x%4==0:x//=4
    return 4 if x%8==7 else 3


def roman(n):
    out=''
    for value,letter in [(1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),(100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
        q,n=divmod(n,value);out+=letter*q
    return out


ROMANS={roman(i):i for i in range(1,4000)}


def expected(pid, a):
    x=a[0]
    if pid==7:
        v=int(str(abs(x))[::-1])*(-1 if x<0 else 1)
        return v if -2**31<=v<2**31 else 0
    if pid==9:return x>=0 and str(x)==str(x)[::-1]
    if pid==13:return ROMANS[x]
    if pid==70:return sum(math.comb(x-k,k) for k in range(x//2+1))
    if pid==118:return [[math.comb(r,k) for k in range(r+1)] for r in range(x)]
    if pid==119:return [math.comb(x,k) for k in range(x+1)]
    if pid==150:
        # Parse the postfix expression into an explicit tree before evaluation.
        stack=[]
        for t in x:
            if t not in ('+','-','*','/') :stack.append(int(t));continue
            right,left=stack.pop(),stack.pop();stack.append((t,left,right))
        def evaluate(t):
            if type(t)is int:return t
            op,left,right=t;l,r=evaluate(left),evaluate(right)
            if op=='+':return l+r
            if op=='-':return l-r
            if op=='*':return l*r
            return (abs(l)//abs(r))*(-1 if (l<0)!=(r<0) else 1)
        assert len(stack)==1
        return evaluate(stack[0])
    if pid==151:return ' '.join(re.findall('[^ ]+',x)[::-1])
    if pid==153:return min(x)
    if pid==162:return [i for i,v in enumerate(x) if (i==0 or v>x[i-1]) and (i==len(x)-1 or v>x[i+1])]
    if pid==167:
        pairs=[[i+1,j+1] for i,j in combinations(range(len(x)),2) if x[i]+x[j]==a[1]]
        assert len(pairs)==1
        return pairs[0]
    if pid==168:
        # Search base-26 length blocks, then ordinary positional digits.
        length,total=1,26
        while x>total:length+=1;total+=26**length
        offset=x-1-sum(26**k for k in range(1,length))
        return ''.join(chr(65+(offset//26**k)%26) for k in range(length-1,-1,-1))
    if pid==172:
        # Sum prime valuations of individual factors, not divisions of n by five.
        total=0
        for i in range(5,x+1,5):
            while i%5==0:total+=1;i//=5
        return total
    if pid==179:return max((''.join(map(str,p)) for p in permutations(x)),key=lambda s:int(s)).lstrip('0') or '0'
    if pid==189:
        out=[None]*len(x)
        for i,v in enumerate(x):out[(i+a[1])%len(x)]=v
        return out
    if pid in (198,213):return independent(x,pid==213)
    if pid==204:return sum(all(i%d for d in range(2,math.isqrt(i)+1)) for i in range(2,x))
    if pid==209:return min([j-i for i in range(len(a[1])) for j in range(i+1,len(a[1])+1) if sum(a[1][i:j])>=x] or [0])
    if pid==215:return next(v for v in set(x) if sum(t>v for t in x)<a[1]<=sum(t>=v for t in x))
    if pid==221:
        return max([0]+[s*s for s in range(1,min(len(x),len(x[0]))+1) for r in range(len(x)-s+1) for c in range(len(x[0])-s+1) if all(x[i][j]=='1' for i in range(r,r+s) for j in range(c,c+s))])
    if pid==228:
        runs=[]
        for value in x:
            if runs and runs[-1][-1]+1==value:runs[-1].append(value)
            else:runs.append([value])
        return [str(r[0]) if len(r)==1 else str(r[0])+'->'+str(r[-1]) for r in runs]
    if pid==229:return sorted(v for v,n in Counter(x).items() if 3*n>len(x))
    if pid==238:return [math.prod(x[:i]+x[i+1:]) for i in range(len(x))]
    if pid==240:return any(a[1] in row for row in x)
    if pid==260:return sorted(v for v,n in Counter(x).items() if n==1)
    if pid==264:return smooth(x,(2,3,5))
    if pid in (274,275):return max(h for h in range(len(x)+1) if sum(v>=h for v in x)>=h)
    if pid==279:return squares(x)
    if pid==283:return [v for v in x if v]+[0]*x.count(0)
    if pid==287:return next(v for v,n in Counter(x).items() if n>1)
    if pid==289:
        live={(r,c) for r,row in enumerate(x) for c,v in enumerate(row) if v}
        counts=Counter((r+dr,c+dc) for r,c in live for dr,dc in product((-1,0,1),repeat=2) if dr or dc)
        return [[int(counts[r,c]==3 or ((r,c)in live and counts[r,c]==2)) for c in range(len(x[0]))] for r in range(len(x))]
    if pid==299:
        bulls=sum(l==r for l,r in zip(x,a[1]));cows=sum((Counter(x)&Counter(a[1])).values())-bulls
        return f'{bulls}A{cows}B'
    if pid==300:return max(len(s) for s in subsequences(x) if all(l<r for l,r in zip(s,s[1:])))
    if pid==309:
        @lru_cache(None)
        def choices(day,held,cool):
            if day==len(x):return 0 if not held else -10**9
            rest=choices(day+1,held,False)
            return max(rest,x[day]+choices(day+1,False,True)) if held else max(rest,-x[day]+choices(day+1,True,False) if not cool else -10**9)
        return choices(0,False,False)
    if pid==313:return smooth(x,a[1])
    if pid==316:
        return min(''.join(s) for s in subsequences(x) if len(s)==len(set(x)) and set(s)==set(x))
    if pid==318:return max([0]+[len(l)*len(r) for l,r in combinations(x,2) if not(set(l)&set(r))])
    if pid==319:return sum(i*i<=x for i in range(1,math.isqrt(x)+1))
    if pid==322:
        queue=deque([(0,0)]);seen={0}
        while queue:
            value,cost=queue.popleft()
            if value==a[1]:return cost
            for coin in x:
                nxt=value+coin
                if nxt<=a[1] and nxt not in seen:seen.add(nxt);queue.append((nxt,cost+1))
        return -1
    if pid==324:return sorted(x)
    if pid==334:return any(l<m<r for l,m,r in combinations(x,3))
    if pid==342:return x in {4**i for i in range(16)}
    if pid==343:
        @lru_cache(None)
        def partition(total,minimum):
            return max([total]+[v*partition(total-v,v) for v in range(minimum,total//2+1)])
        return max(v*partition(x-v,v) for v in range(1,x//2+1))
    if pid==344:return list(reversed(x))
    if pid==345:
        vowels=[c for c in x if c in 'aeiouAEIOU'];it=iter(vowels[::-1])
        return ''.join(next(it) if c in 'aeiouAEIOU' else c for c in x)
    if pid==349:return sorted(set(x)&set(a[1]))
    if pid==350:return sorted((Counter(x)&Counter(a[1])).elements())
    if pid==357:return 1+sum(9*math.perm(9,k-1) for k in range(1,x+1))
    if pid==365:
        y,target=a[1:];queue=deque([(0,0)]);seen={(0,0)}
        while queue:
            l,r=queue.popleft()
            if target in (l,r,l+r):return True
            lr,rl=min(l,y-r),min(r,x-l)
            for t in ((0,r),(l,0),(x,r),(l,y),(l-lr,r+lr),(l+rl,r-rl)):
                if t not in seen:seen.add(t);queue.append(t)
        return False
    if pid==367:return math.isqrt(x)**2==x
    if pid==368:return max(len(s) for s in subsequences(x) if all(max(l,r)%min(l,r)==0 for l,r in combinations(s,2)))
    if pid==371:return x+a[1]
    if pid==372:
        exponent=0
        for digit in a[1]:exponent=10*exponent+digit
        return pow(x,exponent,1337)
    if pid==376:
        return max(len(s) for s in subsequences(x) if all(l!=r for l,r in zip(s,s[1:])) and all((m-l)*(r-m)<0 for l,m,r in zip(s,s[1:],s[2:])))
    if pid==377:
        @lru_cache(None)
        def words(t):return int(t==0) if t<=0 else sum(words(t-v) for v in x if v<=t)
        return words(a[1])
    if pid==378:return sorted(v for row in x for v in row)[a[1]-1]
    if pid==383:return not(Counter(x)-Counter(a[1]))
    if pid==386:
        # Enumerate a decimal trie, rather than sorting its full output.
        result=[]
        def visit(n):
            if n>x:return
            result.append(n)
            for d in range(10):visit(10*n+d)
        for first in range(1,10):visit(first)
        return result
    if pid==389:return ''.join((Counter(a[1])-Counter(x)).elements())
    if pid==390:
        values=list(range(1,x+1));left=True
        while len(values)>1:
            values=values[1::2] if left else values[::-1][1::2][::-1];left=not left
        return values[0]
    if pid==392:
        # LCS against an independently computed prefix table.
        previous=[0]*(len(a[1])+1)
        for ch in x:
            row=[0]
            for i,v in enumerate(a[1]):row.append(previous[i]+1 if v==ch else max(row[-1],previous[i+1]))
            previous=row
        return previous[-1]==len(x)
    if pid==393:return bool(re.fullmatch(r'(?:0[01]{7}|110[01]{5}10[01]{6}|1110[01]{4}(?:10[01]{6}){2}|11110[01]{3}(?:10[01]{6}){3})*',''.join(format(v,'08b') for v in x)))
    if pid==394:
        while '[' in x:
            x=re.sub(r'(\d+)\[([a-z]*)\]',lambda m:int(m[1])*m[2],x)
        return x
    if pid==395:return max([0]+[j-i for i in range(len(x)) for j in range(i+1,len(x)+1) if min(Counter(x[i:j]).values())>=a[1]])
    if pid==396:return max(sum(i*v for i,v in enumerate(x[k:]+x[:k])) for k in range(len(x)))
    if pid==397:
        @lru_cache(None)
        def distance(n):return 0 if n==1 else 1+distance(n//2) if n%2==0 else 2+min(distance((n-1)//2),distance((n+1)//2))
        return distance(x)
    raise ValueError('unregistered oracle '+str(pid))


def exact(a,b):
    return type(a)is type(b) and (len(a)==len(b) and all(exact(l,r) for l,r in zip(a,b)) if type(a)is list else a==b)


def matches(pid,args,value,want):
    if pid==162:return type(value)is int and value in want
    if pid==324:return type(value)is list and all(type(v)is int for v in value) and sorted(value)==want and all((value[i-1]<value[i] if i%2 else value[i-1]>value[i]) for i in range(1,len(value)))
    if pid==368:return type(value)is list and len(value)==want and all(type(v)is int for v in value) and len(set(value))==len(value) and set(value)<=set(args[0]) and all(max(l,r)%min(l,r)==0 for l,r in combinations(value,2))
    if pid in (229,260,349,350):return type(value)is list and all(type(v)is int for v in value) and sorted(value)==want
    return exact(value,want)


MANDATORY_FAILURES={
    (7,'python'):'Accumulator can exceed signed 32-bit before the final overflow test',
    (7,'javascript'):'Accumulator can exceed signed 32-bit before the final overflow test',
    (287,'python'):'seen set grows with input; official contract requires constant extra space',
    (287,'javascript'):'seen set grows with input; official contract requires constant extra space',
    (371,'python'):'Signed conversion uses subtraction, forbidden by the problem contract',
    (378,'python'):'Materialized flattened n*n list violates the mandatory subquadratic memory bound',
    (378,'javascript'):'Materialized flattened n*n array violates the mandatory subquadratic memory bound',
    (386,'python'):'Sorting a materialized range violates mandatory linear time and constant auxiliary space',
    (386,'javascript'):'Sorting a materialized range violates mandatory linear time and constant auxiliary space',
}
FUNCTIONAL_ADAPTER_IDS=(189,283,289,324,344)


def compare(pid,args,want,record,language):
    if 'error'in record:return False,'candidate_error'
    kind=int if pid==162 else list if pid==368 else type(want)
    types={'python':{list:'list',int:'int',bool:'bool',str:'str'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
    if record.get('result_type')!=types[language][kind]:return False,'result_type'
    if not matches(pid,args,record.get('result'),want):return False,'result_value'
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args):return False,'input_effects'
    if record.get('alias_edges')!=[]:return False,'mutable_return_alias'
    return True,None
