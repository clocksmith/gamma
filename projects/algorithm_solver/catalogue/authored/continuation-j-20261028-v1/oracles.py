"""Independent bounded literal references. No candidate imports."""
from functools import lru_cache
from itertools import combinations
from math import comb
IDS=(3819,3820,3821,3824,3825,3828,3830,3834,3835,3836)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer outside domain')
def array(a,lo,hi,minimum=1,maximum=100000):
    if type(a) is not list or not minimum<=len(a)<=maximum:raise ValueError('array length')
    for v in a:integer(v,lo,hi)
def validate_domain(pid,args):
    arity={3819:2,3820:5,3821:2,3824:1,3825:1,3828:1,3830:1,3834:1,3835:2,3836:3}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==3819:array(args[0],-100000,100000);integer(args[1],0,100000)
    if pid==3820:
        n,edges,x,y,z=args;integer(n,4,100000)
        if type(edges) is not list or len(edges)!=n-1:raise ValueError('edge count')
        parent=list(range(n))
        def find(v):
            while v!=parent[v]:parent[v]=parent[parent[v]];v=parent[v]
            return v
        for edge in edges:
            if type(edge) is not list or len(edge)!=2:raise ValueError('edge pair')
            a,b=edge;integer(a,0,n-1);integer(b,0,n-1);a,b=find(a),find(b)
            if a==b:raise ValueError('cycle')
            parent[a]=b
        for v in (x,y,z):integer(v,0,n-1)
        if len({x,y,z})!=3:raise ValueError('distinct targets')
    if pid==3821:
        integer(args[0],1,2**50);integer(args[1],1,50)
        if args[0]>comb(50,args[1]):raise ValueError('answer must be below2**50')
    if pid in (3824,3828,3830,3834):array(args[0],1,100000,2 if pid==3830 else 1)
    if pid==3825:array(args[0],0,10**9)
    if pid==3835:array(args[0],1,10**9);integer(args[1],0,10**15)
    if pid==3836:array(args[0],-10**6,10**6,maximum=100);array(args[1],-10**6,10**6,maximum=100);integer(args[2],1,min(map(len,args[:2])))
def reference(pid,args):
    validate_domain(pid,args)
    if pid==3819:
        a,k=args
        if len(a)>100 or k>300:raise ValueError('reference budget')
        positions=[i for i,v in enumerate(a) if v>=0];result=a[:]
        for _ in range(k):
            if positions:
                first=result[positions[0]]
                for j in range(len(positions)-1):result[positions[j]]=result[positions[j+1]]
                result[positions[-1]]=first
        return result
    if pid==3820:
        n,edges,x,y,z=args
        if n>35:raise ValueError('reference budget')
        distances=[[n]*n for _ in range(n)]
        for i in range(n):distances[i][i]=0
        for a,b in edges:distances[a][b]=distances[b][a]=1
        for middle in range(n):
            for a in range(n):
                for b in range(n):distances[a][b]=min(distances[a][b],distances[a][middle]+distances[middle][b])
        count=0
        for row in distances:
            a,b,c=sorted([row[x],row[y],row[z]])
            count+=a*a+b*b==c*c
        return count
    if pid==3821:
        n,k=args
        if n>100 or k>7:raise ValueError('reference budget')
        width=k
        while comb(width,k)<n:width+=1
        if width>18:raise ValueError('reference budget')
        values=sorted(sum(2**i for i in positions) for positions in combinations(range(width),k))
        return values[n-1]
    if pid==3824:
        nums=args[0]
        if len(nums)>40 or max(nums)>100:raise ValueError('reference budget')
        for k in range(1,1001):
            operations=0
            for value in nums:
                while value>0:value-=k;operations+=1
            if operations<=k*k:return k
    if pid==3825:
        a=args[0]
        if len(a)>16:raise ValueError('reference budget')
        best=0
        for mask in range(1,1<<len(a)):
            seq=[a[i] for i in range(len(a)) if mask>>i&1]
            if all(x<y for x,y in zip(seq,seq[1:])):
                value=seq[0]
                for v in seq[1:]:value&=v
                if value:best=max(best,len(seq))
        return best
    if pid==3828:
        if len(args[0])>10:raise ValueError('reference budget')
        @lru_cache(None)
        def play(state,alice):
            if len(state)==1:return state[0]
            values=[play(state[:left]+state[right:],not alice) for left in range(len(state)) for right in range(left+1,len(state)+1) if right-left<len(state)]
            return max(values) if alice else min(values)
        return play(tuple(args[0]),True)
    if pid==3830:
        a=args[0]
        if len(a)>35:raise ValueError('reference budget')
        best=1
        for removed in range(-1,len(a)):
            b=a[:] if removed==-1 else a[:removed]+a[removed+1:]
            for left in range(len(b)):
                for right in range(left+1,len(b)+1):
                    signs=[(b[i+1]>b[i])-(b[i+1]<b[i]) for i in range(left,right-1)]
                    if all(signs) and all(x==-y for x,y in zip(signs,signs[1:])):best=max(best,right-left)
        return best
    if pid==3834:
        a=args[0][:]
        if len(a)>100:raise ValueError('reference budget')
        while True:
            for i in range(len(a)-1):
                if a[i]==a[i+1]:a[i:i+2]=[a[i]+a[i+1]];break
            else:return a
    if pid==3835:
        a,k=args
        if len(a)>100:raise ValueError('reference budget')
        return sum((max(a[i:j])-min(a[i:j]))*(j-i)<=k for i in range(len(a)) for j in range(i+1,len(a)+1))
    if pid==3836:
        a,b,k=args
        if len(a)>9 or len(b)>9:raise ValueError('reference budget')
        return max(sum(a[i]*b[j] for i,j in zip(left,right)) for left in combinations(range(len(a)),k) for right in combinations(range(len(b)),k))
