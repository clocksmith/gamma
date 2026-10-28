"""Independent bounded reference algorithms; no candidate imports."""
from collections import Counter,deque
from functools import lru_cache
from itertools import product
from math import prod
IDS=(3855,3857,3858,3859,3862,3863,3864,3867,3868,3869)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def array(a,lo,hi,minimum=1,maximum=100000):
    if type(a) is not list or not minimum<=len(a)<=maximum:raise ValueError('array size')
    for v in a:integer(v,lo,hi)
def validate_domain(pid,args):
    arity={3855:3,3857:1,3858:1,3859:3,3862:1,3863:1,3864:3,3867:1,3868:2,3869:2}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==3855:integer(args[0],0,9);integer(args[1],args[0],9);integer(args[2],1,10**9)
    if pid==3857:integer(args[0],1,500)
    if pid==3858:
        grid=args[0]
        if type(grid) is not list or not 1<=len(grid)<=100000:raise ValueError('grid rows')
        width=None
        for row in grid:
            array(row,1,100000)
            if width is None:width=len(row)
            if len(row)!=width:raise ValueError('grid width')
        if len(grid)*width>100000:raise ValueError('grid area')
    if pid==3859:array(args[0],1,100000);integer(args[1],1,len(args[0]));integer(args[2],1,len(args[0]))
    if pid in (3862,3867):array(args[0],1,10**9)
    if pid in (3863,3864):
        s=args[0];alphabet='abcdefghijklmnopqrstuvwxyz' if pid==3863 else '01'
        if type(s) is not str or not 1<=len(s)<=100000 or set(s)-set(alphabet):raise ValueError('string domain')
        if pid==3864:integer(args[1],1,100000);integer(args[2],1,100000)
    if pid==3868:
        array(args[0],1,80000,2,80000);array(args[1],1,80000,2,80000)
        if len(args[0])!=len(args[1]):raise ValueError('array length equality')
    if pid==3869:integer(args[0],1,10**15);integer(args[1],args[0],10**15)
def good(number):
    digits=str(number)
    return all(a<b for a,b in zip(digits,digits[1:])) or all(a>b for a,b in zip(digits,digits[1:]))
def reference(pid,args):
    validate_domain(pid,args)
    if pid==3855:
        left,right,k=args
        if k>8 or (right-left+1)**k>100000:raise ValueError('reference budget')
        return sum(sum(d*10**i for i,d in enumerate(digits)) for digits in product(range(left,right+1),repeat=k))%(10**9+7)
    if pid==3857:
        if args[0]>60:raise ValueError('reference budget')
        @lru_cache(None)
        def split(n):return min((a*(n-a)+split(a)+split(n-a) for a in range(1,n)),default=0)
        return split(args[0])
    if pid==3858:
        grid=args[0]
        if len(grid)>8 or len(grid[0])**len(grid)>100000:raise ValueError('reference budget')
        answers=[]
        for choices in product(*grid):
            value=0
            for x in choices:value|=x
            answers.append(value)
        return min(answers)
    if pid==3859:
        nums,k,m=args
        if len(nums)>45:raise ValueError('reference budget')
        return sum(len(c)==k and min(c.values())>=m for left in range(len(nums)) for right in range(left+1,len(nums)+1) for c in [Counter(nums[left:right])])
    if pid==3862:
        nums=args[0]
        if len(nums)>100:raise ValueError('reference budget')
        return next((i for i in range(len(nums)) if sum(nums[:i])==prod(nums[i+1:])), -1)
    if pid==3863:
        s=args[0]
        if len(s)>7:raise ValueError('reference budget')
        target=''.join(sorted(s));pending=deque([(s,0)]);seen={s}
        while pending:
            state,cost=pending.popleft()
            if state==target:return cost
            for left in range(len(s)):
                for right in range(left+1,len(s)+1):
                    if right-left==len(s):continue
                    other=state[:left]+''.join(sorted(state[left:right]))+state[right:]
                    if other not in seen:seen.add(other);pending.append((other,cost+1))
        return -1
    if pid==3864:
        s,enc,flat=args
        if len(s)>100:raise ValueError('reference budget')
        def costs(word):
            count=word.count('1');own=len(word)*count*enc if count else flat
            if len(word)%2:return [own]
            half=len(word)//2
            return [own]+[a+b for a in costs(word[:half]) for b in costs(word[half:])]
        if len(s)>16:raise ValueError('reference partition budget')
        return min(costs(s))
    if pid==3867:
        nums=args[0]
        if len(nums)>100 or max(nums)>10000:raise ValueError('reference budget')
        def gcd(a,b):return max(d for d in range(1,min(a,b)+1) if a%d==b%d==0)
        values=sorted(gcd(v,max(nums[:i+1])) for i,v in enumerate(nums))
        return sum(gcd(values[i],values[-1-i]) for i in range(len(values)//2))
    if pid==3868:
        a,b=args
        if len(a)>6:raise ValueError('reference budget')
        start=(tuple(sorted(a)),tuple(sorted(b)));pending=deque([(start,0)]);seen={start}
        while pending:
            (left,right),cost=pending.popleft()
            if left==right:return cost
            for i in range(len(a)):
                for j in range(len(a)):
                    x,y=list(left),list(right);x[i],y[j]=y[j],x[i];state=(tuple(sorted(x)),tuple(sorted(y)))
                    if state not in seen:seen.add(state);pending.append((state,cost+1))
        return -1
    if pid==3869:
        left,right=args
        if right-left>10000:raise ValueError('reference budget')
        return sum(good(v) or good(sum(map(int,str(v)))) for v in range(left,right+1))
