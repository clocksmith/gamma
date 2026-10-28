"""Source-blind bounded reference models; never import candidates."""
from functools import lru_cache
from itertools import permutations
import heapq
IDS=(3781,3784,3788,3789,3790,3791,3795,3799,3800,3801)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer outside official domain')
def validate_domain(pid,args):
    arities={3781:2,3784:2,3788:1,3789:5,3790:1,3791:2,3795:2,3799:1,3800:5,3801:1}
    if pid not in arities or type(args) is not list or len(args)!=arities[pid]:raise ValueError('argument envelope')
    if pid in (3781,3788,3795):
        a=args[0]
        if type(a) is not list or not (2 if pid==3788 else 1)<=len(a)<=100000:raise ValueError('array length')
        for v in a:integer(v,-10**9 if pid==3788 else 1,100000 if pid==3795 else 10**9)
    if pid in (3781,3800):
        strings=[args[1]] if pid==3781 else args[:2]
        n=len(args[0])
        for s in strings:
            if type(s) is not str or not 1<=len(s)<=100000 or len(s)!=n or set(s)-set('01'):raise ValueError('binary string')
        if pid==3800:
            for cost in args[2:]:integer(cost,1,10**9)
    if pid==3784:
        s,cost=args
        if type(s) is not str or not 1<=len(s)<=100000 or set(s)-set('abcdefghijklmnopqrstuvwxyz') or type(cost) is not list or len(cost)!=len(s):raise ValueError('deletion domain')
        for c in cost:integer(c,1,10**9)
    if pid==3789:
        for c in args[:3]:integer(c,1,10**6)
        for need in args[3:]:integer(need,0,10**9)
    if pid==3790:integer(args[0],2,100000)
    if pid==3791:integer(args[0],1,10**15);integer(args[1],args[0],10**15)
    if pid==3795:integer(args[1],1,10**9)
    if pid==3799:
        words=args[0]
        if type(words) is not list or not 4<=len(words)<=15 or any(type(w) is not str or len(w)!=4 or set(w)-set('abcdefghijklmnopqrstuvwxyz') for w in words) or len(set(words))!=len(words):raise ValueError('words domain')
    if pid==3801:
        lists=args[0]
        if type(lists) is not list or not 2<=len(lists)<=12:raise ValueError('list count')
        total=0
        for row in lists:
            if type(row) is not list or not 1<=len(row)<=500:raise ValueError('list length')
            for v in row:integer(v,-10**9,10**9)
            if any(a>b for a,b in zip(row,row[1:])):raise ValueError('unsorted input')
            total+=len(row)
        if total>2000:raise ValueError('total length')
def reference(pid,args):
    validate_domain(pid,args)
    if pid==3781:
        nums,s=args
        if len(s)>12:raise ValueError('reference budget')
        seen={s};pending=[s];answer=0
        for state in pending:
            answer=max(answer,sum(v for v,c in zip(nums,state) if c=='1'))
            for i in range(len(s)-1):
                if state[i:i+2]=='01':
                    next_state=state[:i]+'10'+state[i+2:]
                    if next_state not in seen:seen.add(next_state);pending.append(next_state)
        return answer
    if pid==3784:
        s,cost=args
        if len(s)>15:raise ValueError('reference budget')
        answer=sum(cost)
        for mask in range(1,1<<len(s)):
            kept={s[i] for i in range(len(s)) if mask>>i&1}
            if len(kept)==1:answer=min(answer,sum(cost[i] for i in range(len(s)) if not(mask>>i&1)))
        return answer
    if pid==3788:
        a=args[0]
        if len(a)>100:raise ValueError('reference budget')
        return max(sum(a[:i])-min(a[i:]) for i in range(1,len(a)))
    if pid==3789:
        c1,c2,both,n1,n2=args
        if max(n1,n2)>30:raise ValueError('reference budget')
        return min(a*c1+b*c2+c*both for a in range(n1+1) for b in range(n2+1) for c in range(max(n1,n2)+1) if a+c>=n1 and b+c>=n2)
    if pid==3790:
        k=args[0]
        if k>2000:raise ValueError('reference budget')
        value=0
        for length in range(1,k+1):
            value=value*10+1
            if value%k==0:return length
        return -1
    if pid==3791:
        low,high=args
        if high-low>10000:raise ValueError('reference budget')
        return sum(len(str(v))>=2 and sum(map(int,str(v)[::2]))==sum(map(int,str(v)[1::2])) for v in range(low,high+1))
    if pid==3795:
        a,k=args
        if len(a)>50:raise ValueError('reference budget')
        return min((j-i for i in range(len(a)) for j in range(i+1,len(a)+1) if sum(set(a[i:j]))>=k),default=-1)
    if pid==3799:
        words=args[0]
        return sorted([list(row) for row in permutations(words,4) if row[0][0]==row[1][0] and row[0][3]==row[2][0] and row[3][0]==row[1][3] and row[3][3]==row[2][3]])
    if pid==3800:
        s,t,flip,swap,cross=args;n=len(s)
        if n>4:raise ValueError('reference budget')
        start=(s,t);distance={start:0};pending=[(0,s,t)]
        while pending:
            cost,a,b=heapq.heappop(pending)
            if cost!=distance[(a,b)]:continue
            if a==b:return cost
            edges=[]
            for index in range(n):
                for side in range(2):
                    row=a if side==0 else b;changed=row[:index]+('1' if row[index]=='0' else '0')+row[index+1:]
                    edges.append(((changed,b) if side==0 else (a,changed),flip))
                edges.append(((a[:index]+b[index]+a[index+1:],b[:index]+a[index]+b[index+1:]),cross))
            for i in range(n):
                for j in range(i+1,n):
                    for side in range(2):
                        row=list(a if side==0 else b);row[i],row[j]=row[j],row[i];changed=''.join(row)
                        edges.append(((changed,b) if side==0 else (a,changed),swap))
            for state,weight in edges:
                new_cost=cost+weight
                if new_cost<distance.get(state,float('inf')):distance[state]=new_cost;heapq.heappush(pending,(new_cost,*state))
    if pid==3801:
        lists=args[0]
        if len(lists)>6 or sum(map(len,lists))>25:raise ValueError('reference budget')
        @lru_cache(None)
        def search(state):
            if len(state)==1:return 0
            best=float('inf')
            for i in range(len(state)):
                for j in range(i+1,len(state)):
                    a,b=state[i],state[j];cost=len(a)+len(b)+abs(a[(len(a)-1)//2]-b[(len(b)-1)//2])
                    following=tuple(sorted([state[k] for k in range(len(state)) if k not in (i,j)]+[tuple(sorted(a+b))]))
                    best=min(best,cost+search(following))
            return best
        return search(tuple(sorted(map(tuple,lists))))
