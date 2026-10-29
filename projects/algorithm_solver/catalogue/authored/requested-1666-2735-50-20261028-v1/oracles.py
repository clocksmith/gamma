"""Independent bounded models for public-statement candidates; no candidate imports."""
from collections import Counter,deque,defaultdict
from fractions import Fraction
from functools import lru_cache
from itertools import combinations,permutations,product
from pathlib import Path
import heapq,json,math
IDS=tuple(r['id'] for r in json.loads(Path(__file__).with_name('contracts.json').read_text())['problems'] if r['statement_available'])
CLASSES={981:'TimeMap',1032:'StreamChecker',1146:'SnapshotArray',1157:'MajorityChecker',1172:'DinnerPlates',1206:'Skiplist',1670:'FrontMiddleBackQueue',1797:'AuthenticationManager',1825:'MKAverage',1845:'SeatManager',1865:'FindSumPairs',1912:'MovieRentingSystem'}
TREE_IDS={968,979,987,993,1022,1038,1110};MOD=1000000007
LIMITS={963:{'points':50,'coordinate':40000},964:{'x':100,'target':200000000},968:{'nodes':1000,'value':0},969:{'length':100},975:{'length':20000,'valueExclusive':100000},979:{'nodes':100,'coinsTotal':'node count'},980:{'cells':20,'dimension':20},981:{'calls':200000,'textLength':100,'timestamp':10000000},982:{'length':1000,'valueExclusive':65536},984:{'a':100,'b':100},985:{'length':10000,'queries':10000,'absoluteInitialValue':10000,'absoluteDelta':10000},987:{'nodes':1000,'value':1000},993:{'nodes':100,'value':100},994:{'rows':10,'columns':10},996:{'length':12,'value':1000000000},999:{'rows':8,'columns':8},1000:{'length':30,'k':30,'value':100},1012:{'n':1000000000},1019:{'nodes':10000,'value':1000000000},1022:{'nodes':1000,'sum':2147483647},1028:{'nodes':1000,'value':1000000000},1032:{'words':2000,'wordLength':200,'calls':40000},1038:{'nodes':100,'value':100},1040:{'length':10000,'coordinate':1000000000},1054:{'length':10000,'value':10000},1095:{'length':10000,'getCalls':100,'value':1000000000},1096:{'length':60},1110:{'nodes':1000,'deleteCount':1000,'value':1000},1138:{'length':100},1146:{'length':50000,'calls':50000,'value':1000000000},1147:{'length':1000},1157:{'length':20000,'calls':10000,'value':20000},1172:{'capacity':20000,'calls':200000,'value':20000,'index':100000},1191:{'length':100000,'k':100000,'absoluteValue':10000},1206:{'calls':50000,'value':20000},1669:{'list1Length':10000,'list2Length':10000},1670:{'calls':1000,'value':1000000000},1674:{'length':100000,'limit':100000},1712:{'length':100000,'value':10000},1718:{'n':20},1728:{'rows':8,'columns':8,'jump':8,'turnLimit':1000},1786:{'nodes':20000,'edges':40000,'weight':100000},1797:{'calls':2000,'ttl':100000000,'time':100000000,'tokenLength':5},1825:{'m':100000,'calls':100000,'value':100000},1840:{'n':1000000000,'restrictions':100000,'height':1000000000},1845:{'n':100000,'calls':100000},1865:{'nums1Length':1000,'nums2Length':100000,'addCalls':1000,'countCalls':1000,'nums1Value':1000000000,'nums2Value':100000,'delta':100000,'total':1000000000},1912:{'shops':300000,'entries':100000,'calls':100000,'movie':10000,'price':10000},2025:{'length':100000,'absoluteValue':100000},2060:{'length':40,'digitRun':3},2735:{'length':1000,'value':1000000000,'x':1000000000}}


def tree(values):
    if not values:return []
    rows=[[values[0],None,None]];q=deque([0]);at=1
    while q and at<len(values):
        i=q.popleft()
        for side in (1,2):
            if at==len(values):break
            v=values[at];at+=1
            if v is not None:rows[i][side]=len(rows);rows.append([v,None,None]);q.append(len(rows)-1)
    if at!=len(values):raise ValueError('unreachable tree entries')
    return rows


def serialized(rows,root=0):
    if not rows or root is None:return []
    q=deque([root]);out=[]
    while q:
        i=q.popleft()
        if i is None:out.append(None)
        else:out.append(rows[i][0]);q.extend(rows[i][1:])
    while out and out[-1] is None:out.pop()
    return out


def validate_domain(pid,args):
    def need(ok):
        if not ok:raise ValueError('outside official/transport domain: '+str(pid))
    need(pid in IDS and isinstance(args,list))
    if pid in CLASSES:
        need(len(args)==2);ops,argv=args;need(bool(ops) and ops[0]==CLASSES[pid] and len(ops)==len(argv));limit=LIMITS[pid].get('calls',2000);need(len(ops)-1<=limit)
        if pid==981:
            time=0
            for op,a in zip(ops[1:],argv[1:]):
                need(op in ('set','get') and len(a)==(3 if op=='set' else 2) and 1<=len(a[0])<=100 and a[0].isascii() and a[0].isalnum() and a[0].lower()==a[0] and 1<=a[-1]<=10**7)
                if op=='set':need(a[-1]>time and 1<=len(a[1])<=100);time=a[-1]
        elif pid==1032:need(len(argv[0])==1 and 1<=len(argv[0][0])<=2000 and all(1<=len(w)<=200 and all('a'<=c<='z' for c in w) for w in argv[0][0]) and all(op=='query' and len(a)==1 and len(a[0])==1 and 'a'<=a[0]<='z' for op,a in zip(ops[1:],argv[1:])))
        elif pid==1146:
            length=argv[0][0];need(1<=length<=50000);snaps=0
            for op,a in zip(ops[1:],argv[1:]):
                need(op in ('set','get','snap'))
                if op=='snap':need(not a);snaps+=1
                else:need(len(a)==2 and 0<=a[0]<length and (0<=a[1]<=10**9 if op=='set' else 0<=a[1]<snaps))
        elif pid==1157:
            arr=argv[0][0];need(1<=len(arr)<=20000 and all(1<=v<=20000 for v in arr));need(all(op=='query' and len(a)==3 and 0<=a[0]<=a[1]<len(arr) and a[2]<=a[1]-a[0]+1 and 2*a[2]>a[1]-a[0]+1 for op,a in zip(ops[1:],argv[1:])))
        elif pid==1172:need(1<=argv[0][0]<=20000 and all(op in ('push','pop','popAtStack') and len(a)==(0 if op=='pop' else 1) and (not a or 1<=a[0]<=20000 if op=='push' else not a or 0<=a[0]<=100000) for op,a in zip(ops[1:],argv[1:])))
        elif pid==1206:need(argv[0]==[] and all(op in ('add','erase','search') and len(a)==1 and 0<=a[0]<=20000 for op,a in zip(ops[1:],argv[1:])))
        elif pid==1670:need(argv[0]==[] and all(op in ('pushFront','pushMiddle','pushBack','popFront','popMiddle','popBack') and len(a)==(1 if op.startswith('push') else 0) and (not a or 1<=a[0]<=10**9) for op,a in zip(ops[1:],argv[1:])))
        elif pid==1797:
            need(1<=argv[0][0]<=10**8);last=0;generated=set()
            for op,a in zip(ops[1:],argv[1:]):
                need(op in ('generate','renew','countUnexpiredTokens') and len(a)==(1 if op=='countUnexpiredTokens' else 2) and last<a[-1]<=10**8);last=a[-1]
                if len(a)==2:need(1<=len(a[0])<=5 and all('a'<=c<='z' for c in a[0]))
                if op=='generate':need(a[0] not in generated);generated.add(a[0])
        elif pid==1825:need(3<=argv[0][0]<=100000 and 1<2*argv[0][1]<argv[0][0] and all(op in ('addElement','calculateMKAverage') and len(a)==(1 if op=='addElement' else 0) and (not a or 1<=a[0]<=100000) for op,a in zip(ops[1:],argv[1:])))
        elif pid==1845:
            n=argv[0][0];need(1<=n<=100000);reserved=set();available=list(range(1,n+1));heapq.heapify(available)
            for op,a in zip(ops[1:],argv[1:]):
                if op=='reserve':need(not a and len(reserved)<n);seat=heapq.heappop(available);reserved.add(seat)
                else:need(op=='unreserve' and len(a)==1 and a[0] in reserved);reserved.remove(a[0]);heapq.heappush(available,a[0])
        elif pid==1865:
            a,b=argv[0];need(1<=len(a)<=1000 and 1<=len(b)<=100000 and all(1<=v<=10**9 for v in a) and all(1<=v<=100000 for v in b) and ops.count('add')<=1000 and ops.count('count')<=1000)
            need(all((op=='add' and len(v)==2 and 0<=v[0]<len(b) and 1<=v[1]<=100000) or (op=='count' and len(v)==1 and 1<=v[0]<=10**9) for op,v in zip(ops[1:],argv[1:])))
        elif pid==1912:
            n,entries=argv[0];need(1<=n<=300000 and 1<=len(entries)<=100000);status={}
            for shop,movie,price in entries:need(0<=shop<n and 1<=movie<=10000 and 1<=price<=10000 and (shop,movie) not in status);status[shop,movie]=False
            for op,a in zip(ops[1:],argv[1:]):
                if op in ('rent','drop'):need(len(a)==2 and tuple(a) in status and status[tuple(a)]==(op=='drop'));status[tuple(a)]=op=='rent'
                else:need(op=='report' and not a or op=='search' and len(a)==1 and 1<=a[0]<=10000)
        return
    if pid in TREE_IDS:
        need(len(args)==(3 if pid==993 else 2 if pid==1110 else 1));rows=tree(args[0]);cap=100 if pid in (979,993,1038) else 1000;need(1<=len(rows)<=cap)
        values=[r[0] for r in rows]
        if pid==968:need(all(v==0 for v in values))
        elif pid==979:need(sum(values)==len(rows) and all(0<=v<=len(rows) for v in values))
        elif pid==987:need(all(0<=v<=1000 for v in values))
        elif pid==993:need(len(rows)>=2 and len(set(values))==len(values) and all(1<=v<=100 for v in values) and args[1]!=args[2] and all(v in values for v in args[1:]))
        elif pid==1022:
            need(all(v in (0,1) for v in values));stack=[(0,0)];total=0
            while stack:
                i,v=stack.pop();v=2*v+rows[i][0]
                if rows[i][1] is None and rows[i][2] is None:total+=v
                stack.extend((j,v) for j in rows[i][1:] if j is not None)
            need(total<=2**31-1)
        elif pid==1038:
            need(len(set(values))==len(values) and all(0<=v<=100 for v in values));stack=[(0,-math.inf,math.inf)]
            while stack:
                i,lo,hi=stack.pop();v,l,r=rows[i];need(lo<v<hi)
                if l is not None:stack.append((l,lo,v))
                if r is not None:stack.append((r,v,hi))
        elif pid==1110:need(len(set(values))==len(values) and all(1<=v<=1000 for v in values) and len(args[1])<=1000 and len(set(args[1]))==len(args[1]) and all(1<=v<=1000 for v in args[1]))
        return
    if pid==963:need(len(args)==1 and 1<=len(args[0])<=50 and len({tuple(p) for p in args[0]})==len(args[0]) and all(len(p)==2 and all(0<=v<=40000 for v in p) for p in args[0]))
    elif pid==964:need(len(args)==2 and 2<=args[0]<=100 and 1<=args[1]<=200000000)
    elif pid==969:need(len(args)==1 and 1<=len(args[0])<=100 and sorted(args[0])==list(range(1,len(args[0])+1)))
    elif pid==975:need(len(args)==1 and 1<=len(args[0])<=20000 and all(0<=v<100000 for v in args[0]))
    elif pid==980:
        g=args[0];need(len(args)==1 and 1<=len(g)<=20 and 1<=len(g[0])<=20 and len(g)*len(g[0])<=20 and all(len(r)==len(g[0]) and all(v in (-1,0,1,2) for v in r) for r in g));need(sum(v==1 for r in g for v in r)==sum(v==2 for r in g for v in r)==1)
    elif pid==982:need(len(args)==1 and 1<=len(args[0])<=1000 and all(0<=v<65536 for v in args[0]))
    elif pid==984:need(len(args)==2 and all(0<=v<=100 for v in args) and max(args)<=2*(min(args)+1))
    elif pid==985:need(len(args)==2 and 1<=len(args[0])<=10000 and all(abs(v)<=10000 for v in args[0]) and 1<=len(args[1])<=10000 and all(len(q)==2 and abs(q[0])<=10000 and 0<=q[1]<len(args[0]) for q in args[1]))
    elif pid==994:need(len(args)==1 and 1<=len(args[0])<=10 and 1<=len(args[0][0])<=10 and all(len(r)==len(args[0][0]) and all(v in (0,1,2) for v in r) for r in args[0]))
    elif pid==996:need(len(args)==1 and 1<=len(args[0])<=12 and all(0<=v<=10**9 for v in args[0]))
    elif pid==999:need(len(args)==1 and len(args[0])==8 and all(len(r)==8 and all(c in 'R.Bp' for c in r) for r in args[0]) and sum(c=='R' for r in args[0] for c in r)==1)
    elif pid==1000:need(len(args)==2 and 1<=len(args[0])<=30 and all(1<=v<=100 for v in args[0]) and 2<=args[1]<=30)
    elif pid==1012:need(len(args)==1 and 1<=args[0]<=10**9)
    elif pid==1019:need(len(args)==1 and 1<=len(args[0])<=10000 and all(1<=v<=10**9 for v in args[0]))
    elif pid==1028:
        import re
        tokens=re.findall(r'(-*)([0-9]+)',args[0]);need(len(args)==1 and ''.join(a+b for a,b in tokens)==args[0] and 1<=len(tokens)<=1000 and tokens[0][0]=='' and all(1<=int(v)<=10**9 for _,v in tokens));slots=[]
        for ds,v in tokens:
            d=len(ds);need(d<=len(slots));slots=slots[:d]
            if slots:need(slots[-1]<2);slots[-1]+=1
            slots.append(0)
    elif pid==1040:need(len(args)==1 and 3<=len(args[0])<=10000 and len(set(args[0]))==len(args[0]) and all(1<=v<=10**9 for v in args[0]))
    elif pid==1054:need(len(args)==1 and 1<=len(args[0])<=10000 and all(1<=v<=10000 for v in args[0]) and max(Counter(args[0]).values())<=(len(args[0])+1)//2)
    elif pid==1095:
        need(len(args)==2 and 0<=args[0]<=10**9 and 3<=len(args[1])<=10000);a=args[1];peak=max(range(len(a)),key=a.__getitem__);need(0<peak<len(a)-1 and all(0<=v<=10**9 for v in a) and all(a[i]<a[i+1] for i in range(peak)) and all(a[i]>a[i+1] for i in range(peak,len(a)-1)))
    elif pid==1096:need(len(args)==1 and 1<=len(args[0])<=60 and all(c in '{},abcdefghijklmnopqrstuvwxyz' for c in args[0]))
    elif pid in (1138,1147):need(len(args)==1 and 1<=len(args[0])<=(100 if pid==1138 else 1000) and all('a'<=c<='z' for c in args[0]))
    elif pid==1191:need(len(args)==2 and 1<=len(args[0])<=100000 and all(abs(v)<=10000 for v in args[0]) and 1<=args[1]<=100000)
    elif pid==1669:need(len(args)==4 and 3<=len(args[0])<=10000 and 1<=len(args[3])<=10000 and 1<=args[1]<=args[2]<len(args[0])-1)
    elif pid==1674:need(len(args)==2 and 2<=len(args[0])<=100000 and len(args[0])%2==0 and 1<=args[1]<=100000 and all(1<=v<=args[1] for v in args[0]))
    elif pid==1712:need(len(args)==1 and 3<=len(args[0])<=100000 and all(0<=v<=10000 for v in args[0]))
    elif pid==1718:need(len(args)==1 and 1<=args[0]<=20)
    elif pid==1728:need(len(args)==3 and 1<=len(args[0])<=8 and 1<=len(args[0][0])<=8 and all(len(r)==len(args[0][0]) and all(c in 'CMF.#' for c in r) for r in args[0]) and all(sum(r.count(c) for r in args[0])==1 for c in 'CMF') and all(1<=v<=8 for v in args[1:]))
    elif pid==1786:
        n,es=args;need(1<=n<=20000 and n-1<=len(es)<=40000 and all(len(e)==3 and 1<=e[0]<=n and 1<=e[1]<=n and e[0]!=e[1] and 1<=e[2]<=100000 for e in es));need(len({tuple(sorted(e[:2])) for e in es})==len(es))
    elif pid==1840:need(len(args)==2 and 2<=args[0]<=10**9 and len(args[1])<=min(args[0]-1,100000) and len({r[0] for r in args[1]})==len(args[1]) and all(len(r)==2 and 2<=r[0]<=args[0] and 0<=r[1]<=10**9 for r in args[1]))
    elif pid==2025:need(len(args)==2 and 2<=len(args[0])<=100000 and all(abs(v)<=100000 for v in args[0]) and abs(args[1])<=100000)
    elif pid==2060:
        need(len(args)==2 and all(1<=len(s)<=40 and all(c in '123456789abcdefghijklmnopqrstuvwxyz' for c in s) for s in args));need(all(not any(all(c.isdigit() for c in s[i:i+4]) for i in range(len(s)-3)) for s in args))
    elif pid==2735:need(len(args)==2 and 1<=len(args[0])<=1000 and all(1<=v<=10**9 for v in args[0]) and 1<=args[1]<=10**9)


def reference(pid,args):
    validate_domain(pid,args)
    if pid in CLASSES:return trace_reference(pid,*args)
    if pid in TREE_IDS:return tree_reference(pid,args)
    if pid==963:
        points=args[0];pool={tuple(p) for p in points};best=math.inf
        for c,a,b in permutations(points,3):
            u=(a[0]-c[0],a[1]-c[1]);v=(b[0]-c[0],b[1]-c[1])
            if u[0]*v[0]+u[1]*v[1]==0 and (a[0]+b[0]-c[0],a[1]+b[1]-c[1]) in pool:best=min(best,abs(u[0]*v[1]-u[1]*v[0]))
        return 0 if best==math.inf else best
    if pid==964:
        x,target=args;bound=x
        while bound<=target:bound*=x
        coins=[(1,2)];power=x;cost=1
        while power<=bound:coins.append((power,cost));power*=x;cost+=1
        heap=[(0,0)];distance={0:0}
        while heap:
            d,v=heapq.heappop(heap)
            if v==target:return d-1
            if d!=distance[v]:continue
            for coin,cost in coins:
                for nxt in (v-coin,v+coin):
                    if -bound<=nxt<=bound and d+cost<distance.get(nxt,math.inf):distance[nxt]=d+cost;heapq.heappush(heap,(d+cost,nxt))
    if pid==969:return {'kind':'pancake','sorted':sorted(args[0])}
    if pid==975:
        a=args[0];answer=0
        for start in range(len(a)):
            at=start;odd=True
            while at<len(a)-1:
                choices=[i for i in range(at+1,len(a)) if a[i]>=a[at]] if odd else [i for i in range(at+1,len(a)) if a[i]<=a[at]]
                if not choices:break
                at=min(choices,key=lambda i:(a[i] if odd else -a[i],i));odd=not odd
            answer+=at==len(a)-1
        return answer
    if pid==980:
        g=args[0];cells=[(r,c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]!=-1];start=next(p for p in cells if g[p[0]][p[1]]==1);end=next(p for p in cells if g[p[0]][p[1]]==2);middle=[p for p in cells if p not in (start,end)];answer=0
        for order in permutations(middle):
            path=(start,)+order+(end,);answer+=all(abs(a[0]-b[0])+abs(a[1]-b[1])==1 for a,b in zip(path,path[1:]))
        return answer
    if pid==982:return sum(a&b&c==0 for a,b,c in product(args[0],repeat=3))
    if pid==984:return {'kind':'two-letter','a':args[0],'b':args[1]}
    if pid==985:
        a=list(args[0]);out=[]
        for v,i in args[1]:a[i]+=v;out.append(sum(v for v in a if v%2==0))
        return out
    if pid==994:
        g=args[0];fresh={(r,c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]==1};rotten={(r,c) for r in range(len(g)) for c in range(len(g[0])) if g[r][c]==2};minutes=0
        while fresh:
            new={p for p in fresh if any((p[0]+dr,p[1]+dc) in rotten for dr,dc in ((-1,0),(1,0),(0,-1),(0,1)))}
            if not new:return -1
            fresh-=new;rotten|=new;minutes+=1
        return minutes
    if pid==996:return sum(all(math.isqrt(a+b)**2==a+b for a,b in zip(p,p[1:])) for p in set(permutations(args[0])))
    if pid==999:
        g=args[0];r,c=next((r,c) for r in range(8) for c in range(8) if g[r][c]=='R');answer=0
        for pr,pc in ((i,j) for i in range(8) for j in range(8) if g[i][j]=='p' and (i==r or j==c)):
            dr=(pr>r)-(pr<r);dc=(pc>c)-(pc<c);steps=max(abs(pr-r),abs(pc-c));answer+=all(g[r+dr*k][c+dc*k]=='.' for k in range(1,steps))
        return answer
    if pid==1000:
        stones,k=args
        @lru_cache(None)
        def merge(xs):
            if len(xs)==1:return 0
            return min((sum(xs[i:i+k])+merge(xs[:i]+(sum(xs[i:i+k]),)+xs[i+k:]) for i in range(len(xs)-k+1)),default=math.inf)
        value=merge(tuple(stones));return -1 if value==math.inf else value
    if pid==1012:return sum(len(set(str(i)))<len(str(i)) for i in range(1,args[0]+1))
    if pid==1019:return [next((w for w in args[0][i+1:] if w>v),0) for i,v in enumerate(args[0])]
    if pid==1028:
        import re
        tokens=[(len(d),int(v)) for d,v in re.findall(r'(-*)(\d+)',args[0])];at=0;rows=[]
        def visit(depth):
            nonlocal at
            if at==len(tokens) or tokens[at][0]!=depth:return None
            i=len(rows);rows.append([tokens[at][1],None,None]);at+=1;rows[i][1]=visit(depth+1);rows[i][2]=visit(depth+1);return i
        return serialized(rows,visit(0))
    if pid==1040:
        @lru_cache(None)
        def moves(xs):
            if xs[-1]-xs[0]+1==len(xs):return (0,0)
            choices=[]
            for rest in (xs[1:],xs[:-1]):
                for value in range(rest[0]+1,rest[-1]):
                    if value not in rest:choices.append(moves(tuple(sorted(rest+(value,)))))
            return (1+min(c[0] for c in choices),1+max(c[1] for c in choices))
        return list(moves(tuple(sorted(args[0]))))
    if pid==1054:return {'kind':'barcodes','counts':sorted(Counter(args[0]).items())}
    if pid==1095:return next((i for i,v in enumerate(args[1]) if v==args[0]),-1)
    if pid==1096:
        pending=[args[0]];out=set()
        while pending:
            s=pending.pop()
            if '}' not in s:out.update(s.split(','));continue
            end=s.index('}');start=s.rfind('{',0,end);pending.extend(s[:start]+part+s[end+1:] for part in s[start+1:end].split(','))
        return sorted(out)
    if pid==1138:return {'kind':'board-path','target':args[0]}
    if pid==1147:
        @lru_cache(None)
        def chunks(text):
            best=1 if text else 0
            for length in range(1,len(text)//2+1):
                if text[:length]==text[-length:]:best=max(best,2+chunks(text[length:-length]))
            return best
        return chunks(args[0])
    if pid==1191:
        xs=args[0]*args[1];return max([0]+[sum(xs[i:j]) for i in range(len(xs)) for j in range(i+1,len(xs)+1)])%MOD
    if pid==1669:return args[0][:args[1]]+args[3]+args[0][args[2]+1:]
    if pid==1674:
        a,limit=args;return min(sum(0 if a[i]+a[-1-i]==s else 1 if 1<=s-a[i]<=limit or 1<=s-a[-1-i]<=limit else 2 for i in range(len(a)//2)) for s in range(2,2*limit+1))
    if pid==1712:
        a=args[0];return sum(sum(a[:i])<=sum(a[i:j])<=sum(a[j:]) for i in range(1,len(a)-1) for j in range(i+1,len(a)))%MOD
    if pid==1718:
        n=args[0];multiset=[1]+[v for v in range(2,n+1) for _ in range(2)];best=None
        for p in set(permutations(multiset)):
            if all(p.index(v)+v<len(p) and p[p.index(v)+v]==v for v in range(2,n+1)) and (best is None or p>best):best=p
        return list(best)
    if pid==1728:return mouse_reference(*args)
    if pid==1786:
        n,edges=args;d=[[math.inf]*n for _ in range(n)];adj=[[] for _ in range(n)]
        for i in range(n):d[i][i]=0
        for a,b,w in edges:d[a-1][b-1]=d[b-1][a-1]=w;adj[a-1].append(b-1);adj[b-1].append(a-1)
        for k in range(n):
            for i in range(n):
                for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
        def paths(i):return 1 if i==n-1 else sum(paths(j) for j in adj[i] if d[j][-1]<d[i][-1])
        return paths(0)%MOD
    if pid==1840:
        n,restrictions=args;limits=dict(restrictions);best=0
        def visit(values):
            nonlocal best
            if len(values)==n:best=max(best,max(values));return
            index=len(values)+1
            for height in range(max(0,values[-1]-1),values[-1]+2):
                if height<=limits.get(index,n):visit(values+[height])
        visit([0]);return best
    if pid==2025:
        a,k=args;choices=[a]+[a[:i]+[k]+a[i+1:] for i in range(len(a))];return max(sum(sum(xs[:i])==sum(xs[i:]) for i in range(1,len(xs))) for xs in choices)
    if pid==2060:
        def decode(s):
            @lru_cache(None)
            def suffix(i):
                if i==len(s):return {''}
                if s[i].isalpha():return {s[i]+r for r in suffix(i+1)}
                out=set();v=0
                for j in range(i,min(i+3,len(s))):
                    if not s[j].isdigit():break
                    v=v*10+int(s[j]);out.update('?'*v+r for r in suffix(j+1))
                return out
            return suffix(0)
        return any(len(a)==len(b) and all(x==y or '?' in (x,y) for x,y in zip(a,b)) for a in decode(args[0]) for b in decode(args[1]))
    if pid==2735:
        a,x=args;return min(r*x+sum(min(a[(i+j)%len(a)] for j in range(r+1)) for i in range(len(a))) for r in range(len(a)))
    raise ValueError(pid)


def tree_reference(pid,args):
    rows=tree(args[0]);n=len(rows);adj=[[] for _ in rows]
    for i,(_,l,r) in enumerate(rows):
        for j in (l,r):
            if j is not None:adj[i].append(j);adj[j].append(i)
    if pid==968:
        for count in range(n+1):
            for cameras in combinations(range(n),count):
                covered=set(cameras)
                for i in cameras:covered.update(adj[i])
                if len(covered)==n:return count
    if pid==979:
        start=tuple(r[0] for r in rows);goal=(1,)*n;q=deque([(start,0)]);seen={start}
        while q:
            state,steps=q.popleft()
            if state==goal:return steps
            for i,coins in enumerate(state):
                if coins:
                    for j in adj[i]:
                        values=list(state);values[i]-=1;values[j]+=1;nxt=tuple(values)
                        if nxt not in seen:seen.add(nxt);q.append((nxt,steps+1))
    if pid==987:
        columns=defaultdict(lambda:defaultdict(list));q=[(0,0,0)]
        while q:
            i,r,c=q.pop();columns[c][r].append(rows[i][0]);q.extend((j,r+1,c+offset) for j,offset in ((rows[i][1],-1),(rows[i][2],1)) if j is not None)
        return [[v for r in sorted(columns[c]) for v in sorted(columns[c][r])] for c in sorted(columns)]
    if pid==993:
        paths={};stack=[(0,())]
        while stack:
            i,p=stack.pop();paths[rows[i][0]]=p;stack.extend((j,p+(side,)) for side,j in enumerate(rows[i][1:]) if j is not None)
        a,b=paths[args[1]],paths[args[2]];return len(a)==len(b) and a[:-1]!=b[:-1]
    if pid==1022:
        def paths(i,bits):
            bits+=str(rows[i][0]);children=[j for j in rows[i][1:] if j is not None]
            return sum(paths(j,bits) for j in children) if children else int(bits,2)
        return paths(0,'')
    if pid==1038:
        values=[r[0] for r in rows];out=[[sum(v for v in values if v>=row[0]),row[1],row[2]] for row in rows];return serialized(out)
    if pid==1110:
        deleted=set(args[1]);kept={i for i,r in enumerate(rows) if r[0] not in deleted};parents={j:i for i,r in enumerate(rows) for j in r[1:] if j is not None};out=[]
        for i in kept:
            if parents.get(i) not in kept:
                copy=[[v,l if l in kept else None,r if r in kept else None] for v,l,r in rows];out.append(serialized(copy,i))
        return sorted(out,key=repr)
    raise ValueError(pid)


def mouse_reference(grid,cat_jump,mouse_jump):
    cells=[(r,c) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c]!='#'];index={p:i for i,p in enumerate(cells)};n=len(cells);m0=next(index[r,c] for r,c in cells if grid[r][c]=='M');c0=next(index[r,c] for r,c in cells if grid[r][c]=='C');food=next(index[r,c] for r,c in cells if grid[r][c]=='F')
    def moves(jump):
        result=[]
        for r,c in cells:
            choices=[index[r,c]]
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                for step in range(1,jump+1):
                    p=(r+dr*step,c+dc*step)
                    if p not in index:break
                    choices.append(index[p])
            result.append(choices)
        return result
    mm,cm=moves(mouse_jump),moves(cat_jump);previous=[False]*(2*n*n)
    for m in range(n):
        for c in range(n):
            if m==food and c!=food and m!=c:previous[2*(m*n+c)]=previous[2*(m*n+c)+1]=True
    for _ in range(1000):
        current=list(previous)
        for m in range(n):
            for c in range(n):
                if m==c or c==food or m==food:continue
                current[2*(m*n+c)]=any(previous[2*(nxt*n+c)+1] for nxt in mm[m]);current[2*(m*n+c)+1]=all(previous[2*(m*n+nxt)] for nxt in cm[c])
        if current==previous:break
        previous=current
    return previous[2*(m0*n+c0)]


def trace_reference(pid,ops,argv):
    out=[None];state=[];mapping={};snapshots=[];stream='';stacks=[]
    if pid==1032:words=list(argv[0][0])
    if pid in (1146,1157):state=list(argv[0][0]) if pid==1157 else [0]*argv[0][0]
    if pid==1797:ttl=argv[0][0]
    if pid==1825:m,k=argv[0]
    if pid==1845:free=set(range(1,argv[0][0]+1))
    if pid==1865:first,second=map(list,argv[0])
    if pid==1912:prices={(s,m):p for s,m,p in argv[0][1]};rented=set()
    for op,a in zip(ops[1:],argv[1:]):
        value=None
        if pid==981:
            if op=='set':mapping.setdefault(a[0],[]).append((a[2],a[1]))
            else:value=max(((t,v) for t,v in mapping.get(a[0],[]) if t<=a[1]),default=(0,''))[1]
        elif pid==1032:stream+=a[0];value=any(stream.endswith(w) for w in words)
        elif pid==1146:
            if op=='set':state[a[0]]=a[1]
            elif op=='snap':value=len(snapshots);snapshots.append(state.copy())
            else:value=snapshots[a[1]][a[0]]
        elif pid==1157:value=next((v for v,c in Counter(state[a[0]:a[1]+1]).items() if c>=a[2]),-1)
        elif pid==1172:
            cap=argv[0][0]
            if op=='push':
                index=next((i for i,s in enumerate(stacks) if len(s)<cap),len(stacks))
                if index==len(stacks):stacks.append([])
                stacks[index].append(a[0])
            else:
                index=next((i for i in range(len(stacks)-1,-1,-1) if stacks[i]),-1) if op=='pop' else a[0];value=stacks[index].pop() if 0<=index<len(stacks) and stacks[index] else -1
        elif pid==1206:
            if op=='add':state.append(a[0])
            elif op=='search':value=a[0] in state
            else:
                value=a[0] in state
                if value:state.remove(a[0])
        elif pid==1670:
            if op=='pushFront':state.insert(0,a[0])
            elif op=='pushBack':state.append(a[0])
            elif op=='pushMiddle':state.insert(len(state)//2,a[0])
            else:value=state.pop(0 if op=='popFront' else -1 if op=='popBack' else (len(state)-1)//2) if state else -1
        elif pid==1797:
            if op=='generate':mapping[a[0]]=a[1]+ttl
            elif op=='renew':
                if a[0] in mapping and a[1]<mapping[a[0]]:mapping[a[0]]=a[1]+ttl
            else:value=sum(t>a[0] for t in mapping.values())
        elif pid==1825:
            if op=='addElement':state.append(a[0]);state=state[-m:]
            else:value=-1 if len(state)<m else sum(sorted(state)[k:m-k])//(m-2*k)
        elif pid==1845:
            if op=='reserve':value=min(free);free.remove(value)
            else:free.add(a[0])
        elif pid==1865:
            if op=='add':second[a[0]]+=a[1]
            else:value=sum(x+y==a[0] for x in first for y in second)
        elif pid==1912:
            if op=='rent':rented.add(tuple(a))
            elif op=='drop':rented.remove(tuple(a))
            elif op=='search':value=[s for _,s in sorted((p,s) for (s,m),p in prices.items() if m==a[0] and (s,m) not in rented)[:5]]
            else:value=[[s,m] for _,s,m in sorted((prices[s,m],s,m) for s,m in rented)[:5]]
        out.append(value)
    return out
