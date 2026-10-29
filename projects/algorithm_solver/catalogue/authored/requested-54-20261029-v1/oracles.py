"""Independent specification references for small inputs; never run at unbounded maxima.
TreeNode and class traces are host adapters for local development checks only.
"""
from collections import Counter, deque
from itertools import permutations, product, combinations
from math import gcd, isqrt

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val,self.left,self.right=val,left,right

def tree(value):
    if value is None:
        return None
    v,l,r=value
    return TreeNode(v,tree(l),tree(r))

def tree_value(node):
    if node is None:
        return None
    return [node.val,tree_value(node.left),tree_value(node.right)]

def validate_domain(pid,args):
    def integer(x,lo,hi):
        assert type(x) is int and lo<=x<=hi
    if pid==827:
        g,=args;integer(len(g),1,500)
        for r in g:
            assert len(r)==len(g)
            for x in r:integer(x,0,1)
    elif pid==828:
        s,=args;assert 1<=len(s)<=100000 and all('A'<=c<='Z' for c in s)
        # The public int32 answer guarantee is an additional promise.
        # Test generation separately justifies it: small strings or all-identical maximal string.
    elif pid==847:
        g,=args;n=len(g);integer(n,1,12)
        for i,row in enumerate(g):
            assert len(row)==len(set(row)) and len(row)<n and i not in row
            for j in row:integer(j,0,n-1);assert i in g[j]
        seen={0};q=[0]
        for i in q:
            for j in g[i]:
                if j not in seen:seen.add(j);q.append(j)
        assert len(seen)==n
    elif pid==851:
        edges,quiet=args;n=len(quiet);integer(n,1,500);assert sorted(quiet)==list(range(n))
        assert len(edges)<=n*(n-1)//2 and len({tuple(e) for e in edges})==len(edges)
        degree=[0]*n;g=[[] for _ in range(n)]
        for a,b in edges:integer(a,0,n-1);integer(b,0,n-1);assert a!=b;degree[b]+=1;g[a].append(b)
        q=[i for i in range(n) if degree[i]==0]
        for a in q:
            for b in g[a]:
                degree[b]-=1
                if degree[b]==0:q.append(b)
        assert len(q)==n
    elif pid==854:
        a,b=args;assert 1<=len(a)<=20 and Counter(a)==Counter(b) and set(a)<=set('abcdef')
    elif pid==862:
        nums,k=args;integer(len(nums),1,100000);integer(k,1,10**9)
        for x in nums:integer(x,-100000,100000)
    elif pid==864:
        g,=args;integer(len(g),1,30);integer(len(g[0]),1,30);assert all(len(r)==len(g[0]) for r in g)
        text=''.join(g);assert text.count('@')==1 and set(text)<=set('.#@abcdefABCDEF')
        keys=sorted(c for c in text if c.islower());assert 1<=len(keys)<=6 and keys==list('abcdef'[:len(keys)])
        locks=sorted(c.lower() for c in text if c.isupper());assert locks==keys
    elif pid==872:
        def check(t):
            if t is None:return 0
            assert len(t)==3;integer(t[0],0,200);return 1+check(t[1])+check(t[2])
        assert len(args)==2
        for t in args:integer(check(t),1,200)
    elif pid==882:
        edges,budget,n=args;integer(n,1,3000);integer(budget,0,10**9);assert len(edges)<=min(n*(n-1)//2,10000)
        assert len({(a,b) for a,b,c in edges})==len(edges)
        for a,b,c in edges:integer(a,0,n-1);integer(b,a+1,n-1);integer(c,0,10000)
    elif pid==894:
        n,=args;integer(n,1,20)
    elif pid==895:
        operations,rows=args;assert operations[0]=='FreqStack' and rows[0]==[] and len(operations)==len(rows)
        integer(len(operations)-1,0,20000);size=0
        for op,row in zip(operations[1:],rows[1:]):
            if op=='push':assert len(row)==1;integer(row[0],0,10**9);size+=1
            else:assert op=='pop' and row==[] and size>0;size-=1
    elif pid==902:
        digits,n=args;integer(n,1,10**9);assert 1<=len(digits)<=9 and digits==sorted(set(digits)) and set(digits)<=set('123456789')
    elif pid==906:
        a,b=args
        for s in args:assert type(s) is str and 1<=len(s)<=18 and s.isascii() and s.isdigit() and s[0]!='0'
        assert 1<=int(a)<=int(b)<=10**18-1
    elif pid==920:
        n,goal,k=args;integer(goal,1,100);integer(n,1,goal);integer(k,0,n-1)
    elif pid==927:
        a,=args;integer(len(a),3,30000)
        for x in a:integer(x,0,1)
    elif pid==932:
        n,=args;integer(n,1,1000)
    elif pid==952:
        nums,=args;integer(len(nums),1,20000);assert len(nums)==len(set(nums))
        for x in nums:integer(x,1,100000)
    elif pid==960:
        rows,=args;integer(len(rows),1,100);integer(len(rows[0]),1,100)
        assert all(len(r)==len(rows[0]) and all('a'<=c<='z' for c in r) for r in rows)
    else:raise ValueError(pid)

def reference(pid,args):
    validate_domain(pid,args)
    if pid==827:
        g,=args;n=len(g);best=0
        for flip in [None]+[(r,c) for r in range(n) for c in range(n) if not g[r][c]]:
            cells={(r,c) for r in range(n) for c in range(n) if g[r][c] or flip==(r,c)}
            while cells:
                group={cells.pop()};front=list(group)
                for r,c in front:
                    for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                        if p in cells:cells.remove(p);group.add(p);front.append(p)
                best=max(best,len(group))
        return best
    if pid==828:
        s,=args
        return sum(sum(v==1 for v in Counter(s[i:j]).values()) for i in range(len(s)) for j in range(i+1,len(s)+1))
    if pid==847:
        g,=args;n=len(g);d=[[0 if i==j else 100 for j in range(n)] for i in range(n)]
        for i,row in enumerate(g):
            for j in row:d[i][j]=1
        for k in range(n):
            for i in range(n):
                for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
        return min(sum(d[a][b] for a,b in zip(p,p[1:])) for p in permutations(range(n)))
    if pid==851:
        edges,quiet=args;answer=[]
        for x in range(len(quiet)):
            known={x};changed=True
            while changed:
                before=len(known)
                for a,b in edges:
                    if b in known:known.add(a)
                changed=len(known)!=before
            answer.append(min(known,key=lambda i:quiet[i]))
        return answer
    if pid==854:
        start,end=args;q=deque([(start,0)]);seen={start}
        while q:
            s,d=q.popleft()
            if s==end:return d
            for i,j in combinations(range(len(s)),2):
                a=list(s);a[i],a[j]=a[j],a[i];t=''.join(a)
                if t not in seen:seen.add(t);q.append((t,d+1))
    if pid==862:
        a,k=args
        return min((j-i for i in range(len(a)) for j in range(i+1,len(a)+1) if sum(a[i:j])>=k),default=-1)
    if pid==864:
        grid,=args;m,n=len(grid),len(grid[0]);k=sum(c.islower() for row in grid for c in row)
        start=next((r,c) for r in range(m) for c in range(n) if grid[r][c]=='@');dist={(*start,0):0}
        # Bellman relaxation of the literal key/cell transition graph, no BFS queue.
        for _ in range(m*n*(1<<k)):
            changed=False
            for (r,c,mask),d in list(dist.items()):
                for a,b in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if not(0<=a<m and 0<=b<n):continue
                    ch=grid[a][b]
                    if ch=='#' or ch.isupper() and not mask&(1<<(ord(ch)-65)):continue
                    nxt=mask|(1<<(ord(ch)-97)) if ch.islower() else mask;state=(a,b,nxt)
                    if d+1<dist.get(state,10**9):dist[state]=d+1;changed=True
            if not changed:break
        return min((d for (r,c,mask),d in dist.items() if mask==(1<<k)-1),default=-1)
    if pid==872:
        def leaves(t):
            if t is None:return []
            return [t[0]] if t[1] is None and t[2] is None else leaves(t[1])+leaves(t[2])
        return leaves(args[0])==leaves(args[1])
    if pid==882:
        edges,budget,n=args;graph=[[] for _ in range(n)]
        for u,v,c in edges:
            previous=u
            for _ in range(c):
                node=len(graph);graph.append([]);graph[previous].append(node);graph[node].append(previous);previous=node
            graph[previous].append(v);graph[v].append(previous)
        q=deque([(0,0)]);seen={0}
        while q:
            u,d=q.popleft()
            if d==budget:continue
            for v in graph[u]:
                if v not in seen:seen.add(v);q.append((v,d+1))
        return len(seen)
    if pid==894:
        n,=args
        if n%2==0:return []
        shapes=[]
        # Enumerate all binary preorder node-kind strings; a valid prefix consumes one slot and creates two for an internal node.
        for internal in combinations(range(n),(n-1)//2):
            inside=set(internal);slots=1;valid=True
            for i in range(n):
                if slots==0:valid=False;break
                slots+=1 if i in inside else -1
            if not valid or slots:continue
            cursor=iter(range(n))
            def parse():
                i=next(cursor)
                return [0,parse(),parse()] if i in inside else [0,None,None]
            shapes.append(parse())
        return shapes
    if pid==895:
        operations,rows=args;stack=[];out=[None]
        for op,row in zip(operations[1:],rows[1:]):
            if op=='push':stack.append(row[0]);out.append(None)
            else:
                counts=Counter(stack);maximum=max(counts.values());i=next(i for i in range(len(stack)-1,-1,-1) if counts[stack[i]]==maximum);out.append(stack.pop(i))
        return out
    if pid==902:
        digits,n=args;allowed=set(digits)
        return sum(set(str(i))<=allowed for i in range(1,n+1))
    if pid==906:
        left,right=map(int,args)
        return sum(str(i)==str(i)[::-1] and str(i*i)==str(i*i)[::-1] for i in range(isqrt(left-1)+1,isqrt(right)+1))
    if pid==920:
        n,goal,k=args
        return sum(len(set(p))==n and all(p[i] not in p[max(0,i-k):i] for i in range(goal)) for p in product(range(n),repeat=goal))%1000000007
    if pid==927:
        a,=args
        def value(v):return int(''.join(map(str,v)),2)
        return [[i,j] for i in range(len(a)-2) for j in range(i+2,len(a)) if value(a[:i+1])==value(a[i+1:j])==value(a[j:])]
    if pid==932:
        n,=args
        return [list(p) for p in permutations(range(1,n+1)) if all(p[i]+p[j]!=2*p[k] for i in range(n) for k in range(i+1,n) for j in range(k+1,n))]
    if pid==952:
        nums,=args;unseen=set(range(len(nums)));best=0
        while unseen:
            group={unseen.pop()};front=list(group)
            for a in front:
                for b in list(unseen):
                    if gcd(nums[a],nums[b])>1:unseen.remove(b);group.add(b);front.append(b)
            best=max(best,len(group))
        return best
    if pid==960:
        rows,=args;w=len(rows[0]);best=0
        for mask in range(1<<w):
            indices=[i for i in range(w) if mask>>i&1]
            if all(all(row[a]<=row[b] for a,b in zip(indices,indices[1:])) for row in rows):best=max(best,len(indices))
        return w-best
    raise ValueError(pid)

def compare(pid,args,result,expected):
    if pid==927:
        a,=args
        if expected is not None:
            return result in expected if expected else result==[-1,-1]
        if not isinstance(result,list) or len(result)!=2:return False
        i,j=result
        if not(0<=i and i+1<j<len(a)):return False
        parts=[a[:i+1],a[i+1:j],a[j:]]
        normalized=[''.join(map(str,p)).lstrip('0') for p in parts]
        return normalized[0]==normalized[1]==normalized[2]
    if pid==932:
        n,=args
        if sorted(result)!=list(range(1,n+1)):return False
        position={v:i for i,v in enumerate(result)}
        return all(not(i<position[(a+b)//2]<j) for i,a in enumerate(result) for j in range(i+1,n) if (a+(b:=result[j]))%2==0)
    if pid==894:
        encode=lambda t:json_shape(t)
        if expected is not None:return sorted(map(encode,result))==sorted(map(encode,expected))
        n,=args
        from math import comb
        count=0 if n%2==0 else comb(n-1,(n-1)//2)//((n+1)//2)
        def nodes(t):
            if t is None:return 0
            assert t[0]==0 and ((t[1] is None)==(t[2] is None))
            return 1+nodes(t[1])+nodes(t[2])
        return len(result)==count and len({encode(t) for t in result})==count and all(nodes(t)==n for t in result)
    return type(result) is type(expected) and result==expected

def json_shape(t):
    if t is None:return '#'
    return '('+str(t[0])+json_shape(t[1])+json_shape(t[2])+')'
