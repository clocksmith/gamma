"""Independent source-free host references; never import or execute candidates."""
from itertools import combinations
from collections import deque
import random
IDS=(3804,3805,3806,3809,3810,3811,3812,3814,3816,3818)
MOD=1000000007

def integer(x,lo,hi):return type(x) is int and lo<=x<=hi

def array(x,lo,hi,mn,mx):return type(x) is list and mn<=len(x)<=mx and all(integer(v,lo,hi) for v in x)

def validate(pid,args):
    if type(pid) is not int or pid not in IDS or type(args) is not list:raise ValueError('Fixed identity and ordered arguments')
    arity=4 if pid==3812 else 3 if pid in (3806,3809,3811,3814) else 2 if pid==3810 else 1
    if len(args)!=arity:raise ValueError('Argument count')
    a=args[0]
    if pid==3804:ok=array(a,-100000,100000,1,500)
    elif pid==3805:
        ok=type(a) is list and 1<=len(a)<=100000 and all(type(s) is str and 1<=len(s)<=100000 and all('a'<=c<='z' for c in s) for s in a)
        if ok:ok=all(len(s)==len(a[0]) for s in a) and len(a)*len(a[0])<=100000
    elif pid==3806:ok=array(a,1,10**9,1,50000) and integer(args[1],1,10**9) and integer(args[2],1,len(a))
    elif pid==3809:ok=type(a) is list and 1<=len(a)<=100000 and all(array(t,0,100000,3,3) for t in a) and array(args[1],0,100000,2,2) and integer(args[2],0,100000)
    elif pid==3810:ok=array(a,1,100000,1,100000) and array(args[1],1,100000,len(a),len(a))
    elif pid==3811:ok=array(a,0,100000,1,100000) and integer(args[1],0,100000) and integer(args[2],0,100000) and args[1]!=args[2]
    elif pid==3812:
        n,edges,start,target=args;ok=integer(n,2,100000) and type(edges) is list and len(edges)==n-1 and type(start) is str and type(target) is str and len(start)==len(target)==n and set(start)<=set('01') and set(target)<=set('01')
        if ok:
            parent=list(range(n))
            def root(x):
                while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
                return x
            for edge in edges:
                if not array(edge,0,n-1,2,2):ok=False;break
                u,v=map(root,edge)
                if u==v:ok=False;break
                parent[u]=v
    elif pid==3814:ok=array(a,1,100000,1,100000) and array(args[1],1,100000,len(a),len(a)) and integer(args[2],1,200000)
    elif pid==3816:ok=type(a) is str and 1<=len(a)<=100000 and all('a'<=c<='z' for c in a)
    else:ok=array(a,-10**9,10**9,1,100000)
    if not ok:raise ValueError('Outside exact official domain')

def expected(pid,args):
    validate(pid,args);a=args[0]
    if pid==3804:return sum(sum(a[l:r+1]) in a[l:r+1] for l in range(len(a)) for r in range(l,len(a)))
    if pid==3805:
        if len(a)>200:
            if len(set(a))==1:return len(a)*(len(a)-1)//2
            if len(a[0])==1:return len(a)*(len(a)-1)//2
            raise ValueError('Shift-pair reference budget')
        return sum(any(all((ord(x)+shift-97)%26+97==ord(y) for x,y in zip(a[i],a[j])) for shift in range(26)) for i in range(len(a)) for j in range(i+1,len(a)))
    if pid==3806:
        k,m=args[1:]
        if len(a)==1:return a[0]+k
        if len(set(a))==1:return a[0]+k//m
        if len(a)>8 or k>9:raise ValueError('Increment allocation budget')
        answer=0
        for subset in combinations(a,m):
            def assign(i,left,current):
                nonlocal answer
                if i==m:answer=max(answer,current);return
                for delta in range(left+1):
                    value=subset[i]+delta
                    assign(i+1,left-delta,value if i==0 else current&value)
            assign(0,k,0)
        return answer
    if pid==3809:
        center,radius=args[1:];reachable=[t for t in a if abs(t[0]-center[0])+abs(t[1]-center[1])<=radius]
        if not reachable:return [-1,-1]
        quality=max(t[2] for t in reachable);return list(min((t[0],t[1]) for t in reachable if t[2]==quality))
    if pid==3810:
        target=tuple(args[1]);start=tuple(a)
        if start==target:return 0
        if len(a)>12:
            if len(set(a))==1:return 1
            raise ValueError('Literal update BFS budget')
        work=deque([(start,0)]);seen={start}
        while work:
            state,d=work.popleft()
            for value in set(state):
                nxt=tuple(target[i] if x==value else x for i,x in enumerate(state))
                if nxt==target:return d+1
                if nxt not in seen:seen.add(nxt);work.append((nxt,d+1))
        raise AssertionError('Every original mismatch can be fixed')
    if pid==3811:
        t1,t2=args[1:]
        if len(a)>1000:
            if all(x==0 for x in a):return int(t1==0)
            raise ValueError('Block partition DP budget')
        odd=[0]*(len(a)+1);even=[0]*(len(a)+1);even[0]=1
        for end in range(1,len(a)+1):
            value=0
            for start in range(end-1,-1,-1):
                value^=a[start]
                if value==t1:odd[end]=(odd[end]+even[start])%MOD
                if value==t2:even[end]=(even[end]+odd[start])%MOD
        return (odd[-1]+even[-1])%MOD
    if pid==3812:
        n,edges,start,target=args
        if start==target:return []
        if sum(x!=y for x,y in zip(start,target))%2:return [-1]
        if n>14:
            if edges==[[i,i+1] for i in range(n-1)] and start=='0'*n and target=='1'+'0'*(n-2)+'1':return list(range(n-1))
            raise ValueError('Edge subset reference budget')
        solutions=[]
        for mask in range(1<<(n-1)):
            colors=list(start);selected=[]
            for i,(u,v) in enumerate(edges):
                if mask>>i&1:
                    selected.append(i)
                    for j in (u,v):colors[j]='1' if colors[j]=='0' else '0'
            if ''.join(colors)==target:solutions.append(selected)
        return min(solutions,key=lambda row:(len(row),row)) if solutions else [-1]
    if pid==3814:
        cap,budget=args[1:]
        if len(a)>500:
            if len(set(a))==len(set(cap))==1:return cap[0]*min(2,len(a),(budget-1)//a[0])
            raise ValueError('Machine subset enumeration budget')
        return max([0]+[cap[i] for i in range(len(a)) if a[i]<budget]+[cap[i]+cap[j] for i in range(len(a)) for j in range(i+1,len(a)) if a[i]+a[j]<budget])
    if pid==3816:
        alphabet=set(a)
        if len(alphabet)==1:return a[0]
        if len(a)>16:raise ValueError('Legal subsequence enumeration budget')
        return min(t for mask in range(1,1<<len(a)) if set(t:=''.join(a[i] for i in range(len(a)) if mask>>i&1))==alphabet)
    if len(a)>2000:
        if len(set(a))==1:return len(a)-1
        if all(x<y for x,y in zip(a,a[1:])):return 0
        raise ValueError('Prefix enumeration reference budget')
    for cut in range(len(a)):
        if all(x<y for x,y in zip(a[cut:],a[cut+1:])):return cut
    raise AssertionError('Singleton suffix always succeeds')

def matches(pid,args,answer,wanted=None):
    if wanted is None:wanted=expected(pid,args)
    if pid in (3809,3812):return type(answer) is list and all(type(x) is int for x in answer) and answer==wanted
    return type(answer) is type(wanted) and answer==wanted

PUBLIC_EXAMPLES={3804:[([[-1,1,0]],5),([[2,-3]],2)],3805:[([['fusion','layout']],1),([['ab','aa','za','aa']],2)],3806:[([[3,1,2],8,2],6),([[1,2,8,4],7,3],4),([[1,1],3,2],2)],3809:[([[[1,2,5],[2,1,7],[3,1,9]],[1,1],2],[3,1]),([[[1,3,4],[2,2,4],[4,4,7]],[0,0],5],[1,3]),([[[5,6,8],[0,3,5]],[1,2],1],[-1,-1])],3810:[([[1,2,3],[2,1,3]],2),([[4,1,4],[5,1,4]],1),([[7,3,7],[5,5,9]],2)],3811:[([[2,3,1,4],1,5],1),([[1,0,0],1,0],3),([[7],1,7],0)],3812:[([3,[[0,1],[1,2]],'010','100'],[0]),([7,[[0,1],[1,2],[2,3],[3,4],[3,5],[1,6]],'0011000','0010001'],[1,2,5]),([2,[[0,1]],'00','01'],[-1])],3814:[([[4,8,5,3],[1,5,2,7],8],8),([[3,5,7,4],[2,4,3,6],7],6),([[2,2,2],[3,5,4],5],9)],3816:[(['aaccb'],'aacb'),(['z'],'z')],3818:[([[1,-1,2,3,3,4,5]],4),([[4,3,-2,-5]],3),([[1,2,3,4]],0)]}

def build_cases(pid):
    rng=random.Random(20261028+pid);rows=[{'args':args,'expected':wanted,'tag':'public example'} for args,wanted in PUBLIC_EXAMPLES[pid]];generated=[]
    for _ in range(24):
        n=rng.randint(1,7)
        if pid==3804:args=[[rng.randint(-4,4) for _ in range(n)]]
        elif pid==3805:
            m=rng.randint(1,6);args=[[''.join(rng.choice('abxyz') for _ in range(m)) for _ in range(n)]]
        elif pid==3806:args=[[rng.randint(1,15) for _ in range(n)],rng.randint(1,7),rng.randint(1,n)]
        elif pid==3809:args=[[[rng.randint(0,8),rng.randint(0,8),rng.randint(0,5)] for _ in range(n)],[rng.randint(0,8),rng.randint(0,8)],rng.randint(0,10)]
        elif pid==3810:args=[[rng.randint(1,4) for _ in range(n)],[rng.randint(1,4) for _ in range(n)]]
        elif pid==3811:
            t1=rng.randint(0,7);t2=rng.choice([x for x in range(8) if x!=t1]);args=[[rng.randint(0,7) for _ in range(n)],t1,t2]
        elif pid==3812:
            n=max(2,n);edges=[[i,rng.randrange(i)] for i in range(1,n)];rng.shuffle(edges);args=[n,edges,''.join(rng.choice('01') for _ in range(n)),''.join(rng.choice('01') for _ in range(n))]
        elif pid==3814:args=[[rng.randint(1,12) for _ in range(n)],[rng.randint(1,10) for _ in range(n)],rng.randint(1,25)]
        elif pid==3816:args=[''.join(rng.choice('abcd') for _ in range(n))]
        else:args=[[rng.randint(-10,10) for _ in range(n)]]
        generated.append(args)
    edges={3804:[[[0]*500],[[100000,-100000]]],3805:[[['a']*100000],[['a'*100000]],[['az','ba','za']]],3806:[[[10**9],10**9,1],[[10**9]*50000,10**9,50000],[[1]*50000,10**9,1],[[1,2,3],1,3]],3809:[[[[100000,100000,0]],[100000,100000],0],[[[0,0,0]],[100000,100000],100000]],3810:[[[1]*100000,[2]*100000],[[1]*100000,[1]*100000],[[1,2,1],[2,1,2]]],3811:[[[0]*100000,0,1],[[0]*100000,1,0],[[1]+[0]*99,1,0]],3812:[[100000,[[i,i+1] for i in range(99999)],'0'*100000,'1'+'0'*99998+'1'],[100000,[[0,i] for i in range(1,100000)],'0'*100000,'1'+'0'*99999],[2,[[1,0]],'11','00']],3814:[[[100000]*100000,[100000]*100000,200000],[[1]*100000,[100000]*100000,3],[[1],[1],1]],3816:[['a'*100000],['aaaa'],['cbcb'],['aaba']],3818:[[[1]*100000],[list(range(-50000,50000))],[[10**9,-10**9]]]}[pid]
    seen={repr(row['args']) for row in rows}
    for args in generated+edges:
        key=repr(args)
        if key not in seen:seen.add(key);rows.append({'args':args,'expected':expected(pid,args),'tag':'seeded reference or boundary'})
    return rows
cases=build_cases
