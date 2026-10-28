"""Source-blind bounded models, no candidate imports."""
from collections import Counter,deque
from itertools import combinations
import heapq
IDS=(3909,3910,3913,3914,3915,3918,3919,3926,3932,3934,3937,3941,3942)
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def array(a,lo,hi,minimum=1,maximum=100000):
    if type(a) is not list or not minimum<=len(a)<=maximum:raise ValueError('array size')
    for v in a:integer(v,lo,hi)
def validate_domain(pid,args):
    arity={3909:1,3910:2,3913:1,3914:1,3915:2,3918:1,3919:2,3926:2,3932:3,3934:1,3937:2,3941:1,3942:1}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==3909:
        array(args[0],1,10**9,3);peak=args[0].index(max(args[0]));a=args[0]
        if any(a[i]>=a[i+1] for i in range(peak)) or any(a[i]<=a[i+1] for i in range(peak,len(a)-1)):raise ValueError('bitonic domain')
    if pid==3910:
        array(args[0],0,1,maximum=13);edges=args[1];n=len(args[0]);seen=set()
        if type(edges) is not list or len(edges)>n*(n-1)//2:raise ValueError('edge count')
        for e in edges:
            if type(e) is not list or len(e)!=2:raise ValueError('edge')
            integer(e[0],0,n-1);integer(e[1],e[0]+1,n-1)
            if tuple(e) in seen:raise ValueError('duplicateedge')
            seen.add(tuple(e))
    if pid==3913:
        if type(args[0]) is not str or not 1<=len(args[0])<=100000 or set(args[0])-set('abcdefghijklmnopqrstuvwxyz'):raise ValueError('lowercase string')
    if pid==3914:array(args[0],1,10**9)
    if pid==3915:array(args[0],1,100000);integer(args[1],1,len(args[0]))
    if pid==3918:integer(args[0],1,1000)
    if pid==3919:
        array(args[0],-10**9,10**9,2)
        if any(a>=b for a,b in zip(args[0],args[0][1:])):raise ValueError('strict increasing')
        if type(args[1]) is not list or not 1<=len(args[1])<=100000:raise ValueError('query count')
        for q in args[1]:
            if type(q) is not list or len(q)!=2:raise ValueError('query')
            for v in q:integer(v,0,len(args[0])-1)
    if pid==3926:
        for index,words in enumerate(args):
            if type(words) is not list or not 1<=len(words)<=100000 or sum(map(len,words))>100000:raise ValueError('string collection')
            for word in words:
                if type(word) is not str or not word or set(word)-set('abcdefghijklmnopqrstuvwxyz-' + (' ' if index==0 else '')):raise ValueError('word alphabet')
                if index==1 and (word.startswith('-') or word.endswith('-') or '--' in word):raise ValueError('validword')
    if pid==3932:integer(args[0],0,10**9);integer(args[1],args[0],10**9);integer(args[2],1,30)
    if pid==3934:array(args[0],1,100000)
    if pid==3937:array(args[0],1,10**9,maximum=100);integer(args[1],2,100)
    if pid==3941:
        if type(args[0]) is not str or not 1<=len(args[0])<=100000 or set(args[0])-set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$'):raise ValueError('password-domain')
    if pid==3942:
        array(args[0],0,len(args[0])-1)
        if len(set(args[0]))!=len(args[0]):raise ValueError('permutation')
def reference(pid,args):
    validate_domain(pid,args)
    if pid==3909:
        a=args[0];peak=max(range(len(a)),key=a.__getitem__);left=sum(a[:peak+1]);right=sum(a[peak:]);return 0 if left>right else 1 if right>left else -1
    if pid==3910:
        nums,edges=args;n=len(nums)
        if n>10:raise ValueError('reference budget')
        result=0
        for mask in range(1,1<<n):
            nodes={i for i in range(n) if mask>>i&1}
            if sum(nums[i] for i in nodes)%2:continue
            seen={next(iter(nodes))};changed=True
            while changed:
                changed=False
                for a,b in edges:
                    if a in nodes and b in nodes and ((a in seen)!=(b in seen)):seen.update((a,b));changed=True
            result+=seen==nodes
        return result
    if pid==3913:
        s=args[0];vowels=[c for c in s if c in 'aeiou'];remaining=Counter(vowels);ordered=[]
        while remaining:
            chosen=min(remaining,key=lambda c:(-remaining[c],s.index(c)));ordered.extend([chosen]*remaining.pop(chosen))
        iterator=iter(ordered);return ''.join(next(iterator) if c in 'aeiou' else c for c in s)
    if pid==3914:
        a=tuple(args[0])
        if len(a)>5 or max(a)>5:raise ValueError('reference budget')
        pending=deque([(a,0)]);seen={a};bound=max(a)+sum(max(0,x-y) for x,y in zip(a,a[1:]))
        while pending:
            state,cost=pending.popleft()
            if all(x<=y for x,y in zip(state,state[1:])):return cost
            for left in range(len(a)):
                for right in range(left+1,len(a)+1):
                    other=state[:left]+tuple(v+1 for v in state[left:right])+state[right:]
                    if max(other)<=bound and other not in seen:seen.add(other);pending.append((other,cost+1))
    if pid==3915:
        nums,k=args
        if len(nums)>18:raise ValueError('reference budget')
        answer=0
        for mask in range(1,1<<len(nums)):
            indices=[i for i in range(len(nums)) if mask>>i&1]
            if any(b-a<k for a,b in zip(indices,indices[1:])):continue
            values=[nums[i] for i in indices];signs=[(b>a)-(b<a) for a,b in zip(values,values[1:])]
            if all(signs) and all(a==-b for a,b in zip(signs,signs[1:])):answer=max(answer,sum(values))
        return answer
    if pid==3918:
        n=args[0];rev=int(str(n)[::-1]);low,high=sorted((n,rev));return sum(v for v in range(max(2,low),high+1) if all(v%d for d in range(2,int(v**0.5)+1)))
    if pid==3919:
        a,queries=args;n=len(a)
        if n>30:raise ValueError('reference budget')
        closest=[min((j for j in [i-1,i+1] if 0<=j<n),key=lambda j:(abs(a[i]-a[j]),j)) for i in range(n)]
        distances=[[0 if i==j else min(abs(a[i]-a[j]),1 if closest[i]==j else float('inf')) for j in range(n)] for i in range(n)]
        for middle in range(n):
            for i in range(n):
                for j in range(n):distances[i][j]=min(distances[i][j],distances[i][middle]+distances[middle][j])
        return [distances[i][j] for i,j in queries]
    if pid==3926:
        chunks,queries=args;s=''.join(chunks);words=[];current=''
        for i,c in enumerate(s):
            letter='a'<=c<='z';joiner=c=='-' and i>0 and i+1<len(s) and 'a'<=s[i-1]<='z' and 'a'<=s[i+1]<='z'
            if letter or joiner:current+=c
            elif current:words.append(current);current=''
        if current:words.append(current)
        return [words.count(q) for q in queries]
    if pid==3932:
        left,right,k=args
        if right>10000:raise ValueError('reference budget')
        return len({x**k for x in range(right+1) if left<=x**k<=right})
    if pid==3934:
        a=args[0]
        if len(a)>80:raise ValueError('reference budget')
        for length in range(1,len(a)+1):
            counts=Counter(tuple(a[i:i+length]) for i in range(len(a)-length+1))
            if 1 in counts.values():return length
    if pid==3937:
        nums,k=args
        if len(nums)>30 or k>15:raise ValueError('reference budget')
        costs=[]
        for parity in (0,1):
            row=[]
            for residue in range(k):row.append(sum(min(abs(final-v) for final in range(v-k,v+k+1) if final%k==residue) for v in nums[parity::2]))
            costs.append(row)
        return min(costs[0][x]+costs[1][y] for x in range(k) for y in range(k) if x!=y)
    if pid==3941:
        s=args[0];return sum(c in s for c in 'abcdefghijklmnopqrstuvwxyz')+2*sum(c in s for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')+3*sum(c in s for c in '0123456789')+5*sum(c in s for c in '!@#$')
    if pid==3942:
        a=tuple(args[0]);n=len(a)
        if n>9:raise ValueError('reference budget')
        target=tuple(range(n));pending=deque([(a,0)]);seen={a}
        while pending:
            state,cost=pending.popleft()
            if state==target:return cost
            for other in (state[::-1],state[1:]+state[:1]):
                if other not in seen:seen.add(other);pending.append((other,cost+1))
        return -1
