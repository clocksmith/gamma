"""Independent bounded literal references; never import candidate implementations."""
from functools import lru_cache
from itertools import combinations
IDS=(3741,3742,3746,3747,3748,3751,3753,3755,3756,3759)
MOD=10**9+7

def integer(x, lo, hi):
    if type(x) is not int or not lo <= x <= hi:
        raise ValueError('integer outside domain')

def validate_domain(pid,args):
    arity=2 if pid in (3742,3748,3751,3753,3756,3759) else 1
    if type(args) is not list or len(args)!=arity:
        raise ValueError('argument envelope')
    if pid in (3741,3748,3755,3759):
        nums=args[0]
        if type(nums) is not list or not 1<=len(nums)<=100000: raise ValueError('array length')
        for v in nums: integer(v,0 if pid==3755 else 1,len(nums) if pid==3741 else 10**9 if pid in (3755,3759) else 100000)
    if pid==3742:
        grid,k=args
        if type(grid) is not list or not 1<=len(grid)<=200 or type(grid[0]) is not list or not 1<=len(grid[0])<=200:raise ValueError('grid dimensions')
        for row in grid:
            if type(row) is not list or len(row)!=len(grid[0]):raise ValueError('ragged grid')
            for v in row:integer(v,0,2)
        if grid[0][0]!=0:raise ValueError('start cell')
        integer(k,0,1000)
    if pid==3746:
        if type(args[0]) is not str or not 1<=len(args[0])<=100000 or set(args[0])-set('ab'):raise ValueError('binary string')
    if pid==3747:integer(args[0],1,10**15)
    if pid in (3751,3753):
        integer(args[0],1,100000 if pid==3751 else 10**15);integer(args[1],args[0],100000 if pid==3751 else 10**15)
    if pid==3756:
        if type(args[0]) is not str or not 1<=len(args[0])<=100000 or set(args[0])-set('0123456789'):raise ValueError('digit string')
    if pid in (3748,3756):
        if type(args[1]) is not list or not 1<=len(args[1])<=100000:raise ValueError('query count')
        for q in args[1]:
            if type(q) is not list or len(q)!=2:raise ValueError('query pair')
            integer(q[0],0,len(args[0])-1);integer(q[1],q[0],len(args[0])-1)
    if pid==3759:integer(args[1],0,len(args[0])-1)
    if pid not in IDS:raise ValueError('unknown problem')

def reference(pid,args):
    validate_domain(pid,args)
    if pid==3741:
        nums=args[0]
        if len(nums)>30:raise ValueError('reference budget')
        distances=[abs(i-j)+abs(j-k)+abs(k-i) for i,j,k in combinations(range(len(nums)),3) if nums[i]==nums[j]==nums[k]]
        return min(distances,default=-1)
    if pid==3742:
        grid,k=args
        if len(grid)+len(grid[0])>16:raise ValueError('reference budget')
        def walk(i,j,cost,score):
            cost+=int(grid[i][j]!=0);score+=grid[i][j]
            if cost>k:return -1
            if i==len(grid)-1 and j==len(grid[0])-1:return score
            choices=[]
            if i+1<len(grid):choices.append(walk(i+1,j,cost,score))
            if j+1<len(grid[0]):choices.append(walk(i,j+1,cost,score))
            return max(choices,default=-1)
        return walk(0,0,0,0)
    if pid==3746:
        if len(args[0])>12:raise ValueError('reference budget')
        @lru_cache(None)
        def reduce(s):
            best=len(s)
            for i in range(len(s)):
                for j in range(i+1,len(s)+1):
                    if s[i:j].count('a')==s[i:j].count('b'):best=min(best,reduce(s[:i]+s[j:]))
            return best
        return reduce(args[0])
    if pid==3747:
        n=args[0]
        if n>20000:raise ValueError('reference budget')
        return len({int(str(x).replace('0','')) for x in range(1,n+1)})
    if pid==3748:
        nums,queries=args
        if len(nums)>35 or len(queries)>100:raise ValueError('reference budget')
        return [sum(all(nums[i]<=nums[j] for i in range(a,b+1) for j in range(i+1,b+1)) for a in range(left,right+1) for b in range(a,right+1)) for left,right in queries]
    if pid in (3751,3753):
        start,end=args
        if end-start>10000:raise ValueError('reference budget')
        total=0
        for number in range(start,end+1):
            digits=list(map(int,str(number)))
            total+=sum((digits[i]>digits[i-1] and digits[i]>digits[i+1]) or (digits[i]<digits[i-1] and digits[i]<digits[i+1]) for i in range(1,len(digits)-1))
        return total
    if pid==3755:
        nums=args[0]
        if len(nums)>35:raise ValueError('reference budget')
        answer=0
        for left in range(len(nums)):
            for right in range(left,len(nums)):
                xor=0
                for v in nums[left:right+1]:xor^=v
                evens=sum(v%2==0 for v in nums[left:right+1])
                if xor==0 and evens*2==right-left+1:answer=max(answer,right-left+1)
        return answer
    if pid==3756:
        s,queries=args
        if len(s)>1000 or len(queries)>100:raise ValueError('reference budget')
        answers=[]
        for left,right in queries:
            digits=[int(c) for c in s[left:right+1] if c!='0'];value=0
            for digit in digits:value=value*10+digit
            answers.append(value*sum(digits)%MOD)
        return answers
    if pid==3759:
        nums,k=args
        if len(nums)>100:raise ValueError('reference budget')
        return sum(sum(other>value for other in nums)>=k for value in nums)
