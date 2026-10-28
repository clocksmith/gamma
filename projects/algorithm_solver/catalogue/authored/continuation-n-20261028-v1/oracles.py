"""Independent bounded references; no candidate imports."""
from itertools import product,permutations
from math import gcd,atan2,degrees,isfinite
from decimal import Decimal,localcontext
IDS=(3891,3895,3896,3897,3899,3900,3901,3904,3905,3906)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def array(a,lo,hi,minimum=1,maximum=100000):
    if type(a) is not list or not minimum<=len(a)<=maximum:raise ValueError('array size')
    for v in a:integer(v,lo,hi)
def validate_domain(pid,args):
    arity={3891:1,3895:2,3896:1,3897:2,3899:1,3900:1,3901:3,3904:2,3905:3,3906:3}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==3891:array(args[0],1,10**9,3)
    if pid==3895:array(args[0],1,10**6,maximum=1000);integer(args[1],0,9)
    if pid==3896:array(args[0],1,100000)
    if pid==3897:
        array(args[0],0,10000);array(args[1],0,10000)
        if len(args[0])!=len(args[1]) or any(a+b==0 for a,b in zip(*args)) or sum(map(sum,args))>200000:raise ValueError('binary segments')
    if pid==3899:array(args[0],1,1000,3,3)
    if pid==3900:
        if type(args[0]) is not str or not 1<=len(args[0])<=100000 or set(args[0])-set('01'):raise ValueError('binary string')
    if pid==3901:
        array(args[0],1,50000,2,50000);integer(args[1],1,50000)
        if type(args[2]) is not list or not 1<=len(args[2])<=50000:raise ValueError('query count')
        for q in args[2]:
            if type(q) is not list or len(q)!=2:raise ValueError('query pair')
            integer(q[0],0,len(args[0])-1);integer(q[1],1,50000)
    if pid==3904:array(args[0],0,10**9);integer(args[1],0,10**9)
    if pid==3905:
        n,m,sources=args;integer(n,1,100000);integer(m,1,100000)
        if n*m>100000 or type(sources) is not list or not 1<=len(sources)<=n*m:raise ValueError('grid/source size')
        seen=set()
        for row in sources:
            if type(row) is not list or len(row)!=3:raise ValueError('source tuple')
            a,b,color=row;integer(a,0,n-1);integer(b,0,m-1);integer(color,1,10**6)
            if (a,b) in seen:raise ValueError('duplicate source')
            seen.add((a,b))
    if pid==3906:
        integer(args[0],1,9*10**15);integer(args[1],args[0],9*10**15)
        if type(args[2]) is not str or len(args[2])!=6 or args[2].count('D')!=3 or args[2].count('R')!=3:raise ValueError('path')
def compare(pid,actual,expected):
    if pid==3899:
        return type(actual) is list and len(actual)==len(expected) and all(type(a) in (int,float) and isfinite(a) and abs(a-b)<=1e-5 for a,b in zip(actual,expected))
    return type(actual) is type(expected) and actual==expected

def reference(pid,args):
    validate_domain(pid,args)
    if pid==3891:
        nums=args[0]
        if len(nums)>6 or max(nums)>8:raise ValueError('reference budget')
        best=(-1,0)
        for state in product(*(range(v,max(nums)+2) for v in nums)):
            peaks=sum(state[i]>state[i-1] and state[i]>state[i+1] for i in range(1,len(nums)-1));cost=sum(a-b for a,b in zip(state,nums))
            if peaks>best[0] or peaks==best[0] and cost<best[1]:best=(peaks,cost)
        return best[1]
    if pid==3895:return sum(str(value).count(str(args[1])) for value in args[0])
    if pid==3896:
        nums=args[0]
        if len(nums)>100 or max(nums)>1000:raise ValueError('reference budget')
        def prime(v):return v>=2 and all(v%d for d in range(2,int(v**0.5)+1))
        total=0
        for i,v in enumerate(nums):
            original=v
            while prime(v)!=(i%2==0):v+=1
            total+=v-original
        return total
    if pid==3897:
        a,b=args
        if len(a)>7 or sum(a)+sum(b)>1000:raise ValueError('reference budget')
        segments=['1'*x+'0'*y for x,y in zip(a,b)]
        return max(int(''.join(order),2) for order in permutations(segments))%(10**9+7)
    if pid==3899:
        a,b,c=sorted(args[0])
        if a+b<=c:return []
        with localcontext() as ctx:
            ctx.prec=50;half=Decimal(a+b+c)/2;area=(half*(half-a)*(half-b)*(half-c)).sqrt()
            return [degrees(atan2(float(4*area),y*y+z*z-x*x)) for x,y,z in [(a,b,c),(b,a,c),(c,a,b)]]
    if pid==3900:
        s=args[0]
        if len(s)>20:raise ValueError('reference budget')
        states={s}
        for i in range(len(s)):
            for j in range(i+1,len(s)):states.add(s[:i]+s[j]+s[i+1:j]+s[i]+s[j+1:])
        return max((right-left for state in states for left in range(len(s)) for right in range(left+1,len(s)+1) if state[left:right].count('0')==state[left:right].count('1')),default=0)
    if pid==3901:
        nums,p,queries=args;nums=nums[:]
        if len(nums)>12 or len(queries)>100:raise ValueError('reference budget')
        answer=0
        for index,value in queries:
            nums[index]=value;found=False
            for mask in range(1,(1<<len(nums))-1):
                divisor=0
                for i,v in enumerate(nums):
                    if mask>>i&1:divisor=gcd(divisor,v)
                if divisor==p:found=True;break
            answer+=found
        return answer
    if pid==3904:
        nums,k=args
        if len(nums)>100:raise ValueError('reference budget')
        return next((i for i in range(len(nums)) if max(nums[:i+1])-min(nums[i:])<=k),-1)
    if pid==3905:
        n,m,sources=args
        if n*m*len(sources)>100000:raise ValueError('reference budget')
        return [[max(sources,key=lambda src:(-abs(src[0]-row)-abs(src[1]-col),src[2]))[2] for col in range(m)] for row in range(n)]
    if pid==3906:
        left,right,directions=args
        if right-left>10000:raise ValueError('reference budget')
        answer=0
        for value in range(left,right+1):
            digits=str(value).zfill(16);row=col=0;visited=[digits[0]]
            for step in directions:
                row+=step=='D';col+=step=='R';visited.append(digits[row*4+col])
            answer+=all(a<=b for a,b in zip(visited,visited[1:]))
        return answer
