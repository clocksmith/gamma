"""Independent bounded models, reconstructed after the recorded folder collision.
No candidate imports, source reads, language-agreement oracle, or qualification.
"""
from collections import Counter, deque
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, permutations, product
import math

IDS=(589,590,600,606,617,622,623,629,630,632,637,639,641,652,653,654,655,662,664,671,675,676,677,679,687,689,690,699,700,701,703,705,706,707,710,715,719,721,725)
CLASSES={622:'MyCircularQueue',641:'MyCircularDeque',676:'MagicDictionary',677:'MapSum',703:'KthLargest',705:'MyHashSet',706:'MyHashMap',707:'MyLinkedList',710:'Solution',715:'RangeModule'}
TREE_IDS={606,617,623,637,652,653,655,662,671,687,700,701}
MOD=1000000007


def tree(rows):
    if not rows:return []
    if rows[0] is None:raise ValueError('null roots use empty arrays')
    nodes=[[rows[0],None,None]];q=deque([0]);at=1
    while q and at<len(rows):
        i=q.popleft()
        for side in (1,2):
            if at==len(rows):break
            v=rows[at];at+=1
            if v is not None:nodes[i][side]=len(nodes);nodes.append([v,None,None]);q.append(len(nodes)-1)
    if at!=len(rows):raise ValueError('unreachable serialized nodes')
    return nodes


def serialized(nodes,root=0):
    if not nodes or root is None:return []
    out=[];q=deque([root])
    while q:
        i=q.popleft()
        if i is None:out.append(None)
        else:out.append(nodes[i][0]);q.extend(nodes[i][1:])
    while out and out[-1] is None:out.pop()
    return out


def validate_domain(pid,args):
    def need(ok):
        if not ok:raise ValueError('outside official/transport domain: '+str(pid))
    need(pid in IDS and isinstance(args,list))
    if pid in CLASSES:
        need(len(args)==2);ops,argv=args;need(len(ops)==len(argv) and bool(ops) and ops[0]==CLASSES[pid])
        limits={622:3000,641:2000,676:101,677:50,703:10000,705:10000,706:10000,707:2000,710:20000,715:10000};need(len(ops)-1<=limits[pid])
        methods={622:{'enQueue':1,'deQueue':0,'Front':0,'Rear':0,'isEmpty':0,'isFull':0},641:{'insertFront':1,'insertLast':1,'deleteFront':0,'deleteLast':0,'getFront':0,'getRear':0,'isEmpty':0,'isFull':0},676:{'buildDict':1,'search':1},677:{'insert':2,'sum':1},703:{'add':1},705:{'add':1,'remove':1,'contains':1},706:{'put':2,'get':1,'remove':1},707:{'get':1,'addAtHead':1,'addAtTail':1,'addAtIndex':2,'deleteAtIndex':1},710:{'pick':0},715:{'addRange':2,'queryRange':2,'removeRange':2}}[pid]
        need(all(op in methods and isinstance(a,list) and len(a)==methods[op] for op,a in zip(ops[1:],argv[1:])))
        if pid in (622,641):need(len(argv[0])==1 and 1<=argv[0][0]<=1000 and all(not a or 0<=a[0]<=1000 for a in argv[1:]))
        elif pid==676:
            need(argv[0]==[] and len(ops)>1 and ops[1]=='buildDict' and ops.count('buildDict')==1 and ops.count('search')<=100);words=argv[1][0];need(1<=len(words)<=100 and len(set(words))==len(words));need(all(1<=len(w)<=100 and w.isascii() and w.isalpha() and w.islower() for w in words+[a[0] for a in argv[2:]]))
        elif pid==677:
            need(argv[0]==[])
            for op,a in zip(ops[1:],argv[1:]):need(1<=len(a[0])<=50 and a[0].isascii() and a[0].isalpha() and a[0].islower() and (op!='insert' or 1<=a[1]<=1000))
        elif pid==703:
            need(len(argv[0])==2);k,nums=argv[0];need(len(nums)<=10000 and 1<=k<=len(nums)+1 and all(-10000<=v<=10000 for v in nums+[a[0] for a in argv[1:]]));need(bool(ops[1:]) or len(nums)>=k)
        elif pid in (705,706):need(argv[0]==[] and all(0<=v<=10**6 for a in argv[1:] for v in a))
        elif pid==707:need(argv[0]==[] and all(0<=v<=1000 for a in argv[1:] for v in a))
        elif pid==710:
            need(len(argv[0])==2);n,b=argv[0];need(1<=n<=10**9 and len(b)<=min(100000,n-1) and len(set(b))==len(b) and all(0<=x<n for x in b))
        else:need(argv[0]==[] and all(1<=a[0]<a[1]<=10**9 for a in argv[1:]))
        return
    if pid in (589,590):
        need(len(args)==1);r=args[0];need(set(r)=={'values','children'} and len(r['values'])==len(r['children'])<=10000 and all(0<=v<=10000 for v in r['values']));n=len(r['values']);seen=set();stack=[(0,1)] if n else []
        while stack:
            i,depth=stack.pop();need(0<=i<n and i not in seen and depth<=1000);seen.add(i);stack.extend((j,depth+1) for j in r['children'][i])
        need(len(seen)==n);return
    if pid in TREE_IDS:
        need(len(args)==(3 if pid==623 else 2 if pid in (617,653,700,701) else 1));ts=[tree(args[0])]+([tree(args[1])] if pid==617 else [])
        cap={606:10000,617:2000,623:10000,637:10000,652:5000,653:10000,655:1024,662:3000,671:25,687:10000,700:5000,701:10000}[pid]
        lo,hi={606:(-1000,1000),617:(-10000,10000),623:(-100,100),637:(-2**31,2**31-1),652:(-200,200),653:(-10000,10000),655:(-99,99),662:(-100,100),671:(1,2**31-1),687:(-1000,1000),700:(1,10**7),701:(-10**8,10**8)}[pid]
        for t in ts:need(len(t)<=cap and (bool(t) or pid in (617,687,701)) and all(lo<=v<=hi for v,_,_ in t))
        t=ts[0];depth=0;stack=[(0,1,-math.inf,math.inf)] if t else []
        while stack:
            i,d,lbound,rbound=stack.pop();v,l,r=t[i];depth=max(depth,d)
            if pid in (653,700,701):need(lbound<v<rbound)
            if pid==671:need((l is None)==(r is None) and (l is None or v==min(t[l][0],t[r][0])))
            if l is not None:stack.append((l,d+1,lbound,v))
            if r is not None:stack.append((r,d+1,v,rbound))
        if pid==623:need(-100000<=args[1]<=100000 and 1<=args[2]<=depth+1)
        if pid==655:need(depth<=10)
        if pid==687:need(depth<=1000)
        if pid==653:need(-100000<=args[1]<=100000)
        if pid==700:need(1<=args[1]<=10**7)
        if pid==701:need(-10**8<=args[1]<=10**8 and args[1] not in [r[0] for r in t])
        return
    if pid==600:need(len(args)==1 and 1<=args[0]<=10**9)
    elif pid==629:need(len(args)==2 and 1<=args[0]<=1000 and 0<=args[1]<=1000)
    elif pid==630:need(len(args)==1 and 1<=len(args[0])<=10000 and all(len(r)==2 and all(1<=v<=10000 for v in r) for r in args[0]))
    elif pid==632:need(len(args)==1 and 1<=len(args[0])<=3500 and all(1<=len(r)<=50 and r==sorted(r) and all(-100000<=v<=100000 for v in r) for r in args[0]))
    elif pid==639:need(len(args)==1 and 1<=len(args[0])<=100000 and all(c in '0123456789*' for c in args[0]))
    elif pid==654:need(len(args)==1 and 1<=len(args[0])<=1000 and len(set(args[0]))==len(args[0]) and all(0<=v<=1000 for v in args[0]))
    elif pid==664:need(len(args)==1 and 1<=len(args[0])<=100 and args[0].isascii() and args[0].isalpha() and args[0].islower())
    elif pid==675:
        need(len(args)==1);g=args[0];need(1<=len(g)<=50 and 1<=len(g[0])<=50 and all(len(r)==len(g[0]) and all(0<=v<=10**9 for v in r) for r in g));vs=[v for r in g for v in r if v>1];need(len(set(vs))==len(vs))
    elif pid==679:need(len(args)==1 and len(args[0])==4 and all(1<=v<=9 for v in args[0]))
    elif pid==689:need(len(args)==2 and 3<=len(args[0])<=20000 and all(1<=v<65536 for v in args[0]) and 1<=args[1]<=len(args[0])//3)
    elif pid==690:
        need(len(args)==2);es,target=args;ids=[e[0] for e in es];need(1<=len(es)<=2000 and len(set(ids))==len(ids) and target in ids and all(1<=i<=2000 for i in ids) and all(len(e)==3 and -100<=e[1]<=100 and all(s in ids for s in e[2]) for e in es));graph={i:subs for i,_,subs in es};indeg=Counter(s for _,_,subs in es for s in subs);need(all(v<=1 for v in indeg.values()));q=deque(i for i in ids if not indeg[i]);seen=0
        while q:
            i=q.popleft();seen+=1
            for j in graph[i]:indeg[j]-=1;q.append(j) if indeg[j]==0 else None
        need(seen==len(es))
    elif pid==699:need(len(args)==1 and 1<=len(args[0])<=1000 and all(len(r)==2 and 1<=r[0]<=10**8 and 1<=r[1]<=10**6 for r in args[0]))
    elif pid==719:need(len(args)==2 and 2<=len(args[0])<=10000 and all(0<=v<=10**6 for v in args[0]) and 1<=args[1]<=len(args[0])*(len(args[0])-1)//2)
    elif pid==721:need(len(args)==1 and 1<=len(args[0])<=1000 and all(2<=len(r)<=10 and all(1<=len(s)<=30 for s in r) and r[0].isascii() and r[0].isalpha() and all('@' in s for s in r[1:]) for r in args[0]))
    elif pid==725:need(len(args)==2 and len(args[0])<=1000 and all(0<=v<=1000 for v in args[0]) and 1<=args[1]<=50)


@lru_cache(None)
def histogram(n):
    c=Counter()
    for p in permutations(range(n)):c[sum(a>b for i,a in enumerate(p) for b in p[i+1:])]+=1
    return c


def reference(pid,args):
    validate_domain(pid,args)
    if pid in CLASSES:return trace_reference(pid,*args)
    if pid in TREE_IDS:return tree_reference(pid,args)
    if pid in (589,590):
        r=args[0]
        def visit(i):
            cs=[v for j in r['children'][i] for v in visit(j)]
            return [r['values'][i]]+cs if pid==589 else cs+[r['values'][i]]
        return visit(0) if r['values'] else []
    if pid==600:
        total=1;stack=[1]
        while stack:
            x=stack.pop()
            if x>args[0]:continue
            total+=1;stack.append(2*x)
            if not x%2:stack.append(2*x+1)
        return total
    if pid==629:
        n,k=args
        if n<=7:return histogram(n)[k]%MOD
        if not k:return 1
        if n<k:raise ValueError('bounded permutation oracle')
        answer=math.comb(n+k-1,k);j=1
        while j*(3*j-1)//2<=k:
            for v in (j*(3*j-1)//2,j*(3*j+1)//2):
                if v<=k:answer+=(-1 if j%2 else 1)*math.comb(n+k-v-1,k-v)
            j+=1
        return answer%MOD
    if pid==630:
        rows=args[0];best=0
        for mask in range(1<<len(rows)):
            chosen=sorted((r for i,r in enumerate(rows) if mask>>i&1),key=lambda r:r[1]);time=0
            for duration,end in chosen:
                time+=duration
                if time>end:break
            else:best=max(best,len(chosen))
        return best
    if pid==632:
        key=min((max(xs)-min(xs),min(xs),max(xs)) for xs in product(*args[0]));return list(key[1:])
    if pid==639:
        s=args[0]
        @lru_cache(None)
        def count(i):
            if i==len(s):return 1
            result=0
            for v in range(1,27):
                word=str(v)
                if i+len(word)<=len(s) and all(s[i+j]==c or s[i+j]=='*' and c!='0' for j,c in enumerate(word)):result+=count(i+len(word))
            return result%MOD
        return count(0)
    if pid==654:
        xs=args[0];nodes=[]
        def make(lo,hi):
            if lo==hi:return None
            m=max(range(lo,hi),key=xs.__getitem__);i=len(nodes);nodes.append([xs[m],None,None]);nodes[i][1]=make(lo,m);nodes[i][2]=make(m+1,hi);return i
        return serialized(nodes,make(0,len(xs)))
    if pid==664:
        s=args[0];q=deque([('?'*len(s),0)]);seen={'?'*len(s)}
        while q:
            word,steps=q.popleft()
            if word==s:return steps
            for lo in range(len(s)):
                for hi in range(lo+1,len(s)+1):
                    for c in set(s):
                        nxt=word[:lo]+c*(hi-lo)+word[hi:]
                        if nxt not in seen:seen.add(nxt);q.append((nxt,steps+1))
    if pid==675:
        g=args[0];vs=[(i,j) for i in range(len(g)) for j in range(len(g[0])) if g[i][j]];dist={(v,w):0 if v==w else 1 if abs(v[0]-w[0])+abs(v[1]-w[1])==1 else math.inf for v in vs for w in vs}
        for k in vs:
            for i in vs:
                for j in vs:dist[i,j]=min(dist[i,j],dist[i,k]+dist[k,j])
        prev=(0,0);answer=0
        for _,nxt in sorted((g[i][j],(i,j)) for i,j in vs if g[i][j]>1):
            step=dist.get((prev,nxt),math.inf)
            if step==math.inf:return -1
            answer+=step;prev=nxt
        return answer
    if pid==679:
        def values(xs):
            if len(xs)==1:return {Fraction(xs[0])}
            out=set()
            for k in range(1,len(xs)):
                for a in values(xs[:k]):
                    for b in values(xs[k:]):
                        out.update((a+b,a-b,a*b))
                        if b:out.add(a/b)
            return out
        return any(Fraction(24) in values(xs) for xs in set(permutations(args[0])))
    if pid==689:
        xs,k=args;ts=(t for t in combinations(range(len(xs)-k+1),3) if t[0]+k<=t[1] and t[1]+k<=t[2]);return list(min(ts,key=lambda t:(-sum(sum(xs[i:i+k]) for i in t),t)))
    if pid==690:
        es,target=args;reachable={target}
        while True:
            added={j for i,_,subs in es if i in reachable for j in subs}-reachable
            if not added:return sum(v for i,v,_ in es if i in reachable)
            reachable|=added
    if pid==699:
        coords=sorted({x for l,s in args[0] for x in (l,l+s)});heights=[0]*(len(coords)-1);out=[]
        for l,s in args[0]:
            cells=[i for i in range(len(heights)) if l<=coords[i] and coords[i+1]<=l+s];h=max(heights[i] for i in cells)+s
            for i in cells:heights[i]=h
            out.append(max(heights))
        return out
    if pid==719:return sorted(abs(a-b) for a,b in combinations(args[0],2))[args[1]-1]
    if pid==721:
        rows=args[0];left=set(range(len(rows)));out=[]
        while left:
            i=min(left);group={i};emails=set(rows[i][1:])
            while True:
                added={j for j in left-group if emails.intersection(rows[j][1:])}
                if not added:break
                group|=added
                for j in added:emails.update(rows[j][1:])
            left-=group;out.append([rows[i][0]]+sorted(emails))
        return sorted(out)
    if pid==725:
        xs,k=args;q,r=divmod(len(xs),k);at=0;out=[]
        for i in range(k):n=q+(i<r);out.append(xs[at:at+n]);at+=n
        return out
    raise ValueError(pid)


def tree_reference(pid,args):
    t=tree(args[0]);vals=[r[0] for r in t]
    def shape(i):return None if i is None else (t[i][0],shape(t[i][1]),shape(t[i][2]))
    def fromshape(s):
        out=[]
        def make(k):
            if k is None:return None
            i=len(out);out.append([k[0],None,None]);out[i][1]=make(k[1]);out[i][2]=make(k[2]);return i
        return serialized(out,make(s))
    if pid==606:
        def fmt(i):
            v,l,r=t[i];return str(v)+('('+(fmt(l) if l is not None else '')+')' if l is not None or r is not None else '')+('('+fmt(r)+')' if r is not None else '')
        return fmt(0)
    if pid==617:
        u=tree(args[1])
        def merge(i,j):
            if i is None and j is None:return None
            return ((t[i][0] if i is not None else 0)+(u[j][0] if j is not None else 0),merge(t[i][1] if i is not None else None,u[j][1] if j is not None else None),merge(t[i][2] if i is not None else None,u[j][2] if j is not None else None))
        return fromshape(merge(0 if t else None,0 if u else None))
    if pid==623:
        value,depth=args[1:]
        def visit(s,level):
            if level==depth:return (value,s,None)
            if s is None:return None
            if level==depth-1:return (s[0],(value,s[1],None),(value,None,s[2]))
            return (s[0],visit(s[1],level+1),visit(s[2],level+1))
        return fromshape(visit(shape(0),1))
    if pid==637:
        levels={}
        def visit(i,d):
            if i is None:return
            levels.setdefault(d,[]).append(t[i][0]);visit(t[i][1],d+1);visit(t[i][2],d+1)
        visit(0,0);return [sum(v)/len(v) for _,v in sorted(levels.items())]
    if pid==652:return sorted([fromshape(k) for k,v in Counter(shape(i) for i in range(len(t))).items() if v>1],key=repr)
    if pid==653:return any(a+b==args[1] for a,b in combinations(vals,2))
    if pid==655:
        def height(i):return 0 if i is None else 1+max(height(t[i][1]),height(t[i][2]))
        h=height(0);out=[['']*(2**h-1) for _ in range(h)]
        def visit(i,d,left,right):
            if i is None:return
            mid=(left+right)//2;out[d][mid]=str(t[i][0]);visit(t[i][1],d+1,left,mid-1);visit(t[i][2],d+1,mid+1,right)
        visit(0,0,0,len(out[0])-1);return out
    if pid==662:
        levels={};q=[(0,'')]
        while q:
            i,bits=q.pop();levels.setdefault(len(bits),[]).append(int('1'+bits,2));q.extend((j,bits+str(side-1)) for side,j in enumerate(t[i][1:],1) if j is not None)
        return max(max(v)-min(v)+1 for v in levels.values())
    if pid==671:return min((v for v in set(vals) if v>min(vals)),default=-1)
    if pid==687:
        adj=[[] for _ in t];best=0
        for i,(v,l,r) in enumerate(t):
            for j in (l,r):
                if j is not None and t[j][0]==v:adj[i].append(j);adj[j].append(i)
        for start in range(len(t)):
            stack=[(start,-1,0)]
            while stack:
                i,parent,d=stack.pop();best=max(best,d);stack.extend((j,i,d+1) for j in adj[i] if j!=parent)
        return best
    if pid==700:return next((serialized(t,i) for i,v in enumerate(vals) if v==args[1]),[])
    if pid==701:return sorted(vals+[args[1]])
    raise ValueError(pid)


def trace_reference(pid,ops,argv):
    state=[];mapping={};covered=set();out=[None];k=argv[0][0] if pid in (622,641,703) else None
    if pid==703:state=list(argv[0][1])
    if pid==710:return {'kind':'uniform-support','n':argv[0][0],'blacklist':argv[0][1],'draws':len(ops)-1}
    for op,a in zip(ops[1:],argv[1:]):
        result=None
        if pid in (622,641):
            if op in ('enQueue','insertFront','insertLast'):
                result=len(state)<k
                if result:state.insert(0,a[0]) if op=='insertFront' else state.append(a[0])
            elif op in ('deQueue','deleteFront','deleteLast'):
                result=bool(state)
                if result:state.pop(-1 if op=='deleteLast' else 0)
            elif op in ('Front','getFront'):result=state[0] if state else -1
            elif op in ('Rear','getRear'):result=state[-1] if state else -1
            elif op=='isEmpty':result=not state
            else:result=len(state)==k
        elif pid==676:
            if op=='buildDict':state=list(a[0])
            else:result=any(len(w)==len(a[0]) and sum(x!=y for x,y in zip(w,a[0]))==1 for w in state)
        elif pid==677:
            if op=='insert':mapping[a[0]]=a[1]
            else:result=sum(v for key,v in mapping.items() if key.startswith(a[0]))
        elif pid==703:state.append(a[0]);result=sorted(state,reverse=True)[k-1]
        elif pid==705:
            if op=='add':covered.add(a[0])
            elif op=='remove':covered.discard(a[0])
            else:result=a[0] in covered
        elif pid==706:
            if op=='put':mapping[a[0]]=a[1]
            elif op=='remove':mapping.pop(a[0],None)
            else:result=mapping.get(a[0],-1)
        elif pid==707:
            if op=='get':result=state[a[0]] if a[0]<len(state) else -1
            elif op=='addAtHead':state.insert(0,a[0])
            elif op=='addAtTail':state.append(a[0])
            elif op=='addAtIndex':
                if a[0]<=len(state):state.insert(a[0],a[1])
            elif a[0]<len(state):state.pop(a[0])
        elif pid==715:
            if a[1]-a[0]>10000:raise ValueError('unit-cell oracle is bounded')
            cells=set(range(*a))
            if op=='addRange':covered|=cells
            elif op=='removeRange':covered-=cells
            else:result=cells<=covered
        out.append(result)
    return out
