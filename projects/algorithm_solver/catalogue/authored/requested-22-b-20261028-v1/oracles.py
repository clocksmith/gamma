"""Independent bounded reference algorithms; no candidate imports."""
from collections import deque
from itertools import combinations,product
IDS=(745,749,753,756,757,761,765)
LOWER='abcdefghijklmnopqrstuvwxyz'
def integer(v,lo,hi):
    if type(v) is not int or not lo<=v<=hi:raise ValueError('integer domain')
def word(v,alphabet,lo,hi):
    if type(v) is not str or not lo<=len(v)<=hi or set(v)-set(alphabet):raise ValueError('string domain')
def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    return a==b
def special(s):
    balance=0
    for ch in s:
        balance+=1 if ch=='1' else -1
        if balance<0:return False
    return len(s)>0 and balance==0
def validate_domain(pid,args):
    arity={745:2,749:1,753:2,756:2,757:1,761:1,765:1}
    if pid not in arity or type(args) is not list or len(args)!=arity[pid]:raise ValueError('argument envelope')
    if pid==745:
        operations,rows=args
        if type(operations) is not list or type(rows) is not list or not operations or len(operations)!=len(rows):raise ValueError('trace shape')
        if operations[0]!='WordFilter' or type(rows[0]) is not list or len(rows[0])!=1:raise ValueError('one initial WordFilter(words) required')
        words=rows[0][0]
        if type(words) is not list or not 1<=len(words)<=10000:raise ValueError('words size')
        for w in words:word(w,LOWER,1,7)
        if len(operations)-1>10000:raise ValueError('call budget')
        for name,row in zip(operations[1:],rows[1:]):
            if name!='f' or type(row) is not list or len(row)!=2:raise ValueError('declared method/arity')
            word(row[0],LOWER,1,7);word(row[1],LOWER,1,7)
    if pid==749:
        grid=args[0]
        if type(grid) is not list or not 1<=len(grid)<=50:raise ValueError('grid rows')
        for row in grid:
            if type(row) is not list or len(row)!=len(grid[0]) or not 1<=len(row)<=50:raise ValueError('grid width')
            for v in row:integer(v,0,1)
        virus_walls(grid)
    if pid==753:
        integer(args[0],1,4);integer(args[1],1,10)
        if args[1]**args[0]>4096:raise ValueError('k**n bound')
    if pid==756:
        bottom,allowed=args
        word(bottom,'ABCDEF',2,6)
        if type(allowed) is not list or len(allowed)>216:raise ValueError('allowed size')
        for pattern in allowed:word(pattern,'ABCDEF',3,3)
        if len(set(allowed))!=len(allowed):raise ValueError('allowed unique')
    if pid==757:
        intervals=args[0]
        if type(intervals) is not list or not 1<=len(intervals)<=3000:raise ValueError('intervals size')
        for interval in intervals:
            if type(interval) is not list or len(interval)!=2:raise ValueError('interval shape')
            integer(interval[0],0,10**8);integer(interval[1],interval[0]+1,10**8)
    if pid==761:
        word(args[0],'01',1,50)
        if not special(args[0]):raise ValueError('special string domain')
    if pid==765:
        row=args[0]
        if type(row) is not list or len(row)%2 or not 4<=len(row)<=60:raise ValueError('row size')
        for v in row:integer(v,0,len(row)-1)
        if len(set(row))!=len(row):raise ValueError('row unique')
def neighbours(cell,rows,cols):
    r,c=cell
    for x,y in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
        if 0<=x<rows and 0<=y<cols:yield (x,y)
def virus_walls(grid):
    """Explicit wall-edge simulation; raises when the public no-tie guarantee fails."""
    rows,cols=len(grid),len(grid[0])
    infected={(r,c) for r in range(rows) for c in range(cols) if grid[r][c]==1}
    walls=set();total=0
    while True:
        seen=set();regions=[]
        for cell in sorted(infected):
            if cell in seen:continue
            seen.add(cell);region=[cell];stack=[cell]
            while stack:
                x=stack.pop()
                for y in neighbours(x,rows,cols):
                    if y in infected and y not in seen and frozenset((x,y)) not in walls:seen.add(y);region.append(y);stack.append(y)
            regions.append(region)
        threats=[]
        for region in regions:
            edges=[(x,y) for x in region for y in neighbours(x,rows,cols) if y not in infected and frozenset((x,y)) not in walls]
            threats.append((len({y for _,y in edges}),edges))
        ranked=sorted(range(len(regions)),key=lambda i:-threats[i][0])
        if not ranked or threats[ranked[0]][0]==0:return total
        if len(ranked)>1 and threats[ranked[1]][0]==threats[ranked[0]][0]:raise ValueError('no-tie guarantee')
        best=ranked[0];total+=len(threats[best][1]);walls.update(frozenset(e) for e in threats[best][1])
        spread=set()
        for i,(_,edges) in enumerate(threats):
            if i!=best:spread.update(y for _,y in edges)
        infected|=spread
def lyndon_sequence(n,k):
    """Fredricksen-Kessler-Maiorana concatenation of Lyndon words, cyclically extended."""
    a=[0]*(n+1);sequence=[]
    def generate(t,p):
        if t>n:
            if n%p==0:sequence.extend(a[1:p+1])
        else:
            a[t]=a[t-p];generate(t+1,p)
            for j in range(a[t-p]+1,k):a[t]=j;generate(t+1,t)
    generate(1,1)
    return ''.join(map(str,sequence+(sequence*n)[:n-1]))
def safe_valid(n,k,s):
    if type(s) is not str or len(s)!=k**n+n-1 or set(s)-set('0123456789'[:k]):return False
    return len({s[i:i+n] for i in range(len(s)-n+1)})==k**n
def compare(pid,args,observed,expected):
    if pid==753:return safe_valid(args[0],args[1],observed)
    return exact(observed,expected)
def reference(pid,args):
    validate_domain(pid,args)
    if pid==745:
        operations,rows=args;words=rows[0][0]
        if len(words)*(len(operations)-1)>2000000:raise ValueError('reference budget')
        out=[None]
        for pref,suff in rows[1:]:
            out.append(next((i for i in range(len(words)-1,-1,-1) if words[i].startswith(pref) and words[i].endswith(suff)),-1))
        return out
    if pid==749:return virus_walls(args[0])
    if pid==753:
        s=lyndon_sequence(args[0],args[1])
        if not safe_valid(args[0],args[1],s):raise AssertionError('reference sequence invalid')
        return s
    if pid==756:
        bottom,allowed=args;tops={};known={};work=[0]
        for pattern in allowed:tops.setdefault(pattern[:2],[]).append(pattern[2])
        def buildable(row):
            if len(row)==1:return True
            if row not in known:
                known[row]=False
                for choice in product(*[tops.get(row[i:i+2],()) for i in range(len(row)-1)]):
                    work[0]+=1
                    if work[0]>3000000:raise ValueError('reference budget')
                    if buildable(''.join(choice)):known[row]=True;break
            return known[row]
        return buildable(bottom)
    if pid==757:
        intervals=args[0];low=min(a for a,_ in intervals);high=max(b for _,b in intervals)
        if high-low>11:raise ValueError('reference budget')
        for size in range(high-low+2):
            for chosen in combinations(range(low,high+1),size):
                if all(sum(a<=x<=b for x in chosen)>=2 for a,b in intervals):return size
        raise AssertionError('no containing set')
    if pid==761:
        s=args[0]
        if len(s)>14:raise ValueError('reference budget')
        if s not in _LARGEST:
            component={s};pending=deque([s])
            while pending:
                state=pending.popleft()
                for i in range(len(state)):
                    for j in range(i+1,len(state)):
                        if not special(state[i:j]):continue
                        for k in range(j+1,len(state)+1):
                            if special(state[j:k]):
                                other=state[:i]+state[j:k]+state[i:j]+state[k:]
                                if other not in component:component.add(other);pending.append(other)
            best=max(component)
            for state in component:_LARGEST[state]=best
        return _LARGEST[s]
    if pid==765:
        row=args[0]
        if len(row)>12:raise ValueError('reference budget')
        def canonical(seats):return tuple(sorted(tuple(sorted(seats[i:i+2])) for i in range(0,len(seats),2)))
        goal=tuple((i,i+1) for i in range(0,len(row),2));start=canonical(row);pending=deque([(start,0)]);seen={start}
        while pending:
            state,cost=pending.popleft()
            if state==goal:return cost
            flat=[v for pair in state for v in pair]
            for i in range(len(flat)):
                for j in range(i+1,len(flat)):
                    if i//2==j//2:continue
                    other=flat[:];other[i],other[j]=other[j],other[i];key=canonical(other)
                    if key not in seen:seen.add(key);pending.append((key,cost+1))
        raise AssertionError('unreachable seating')
_LARGEST={}
