"""Definition-derived host references; never imports supplied implementations."""
from collections import Counter,deque
from functools import lru_cache
from fractions import Fraction
from itertools import combinations,combinations_with_replacement,permutations,product
import math,re,string


def subs(s):
    return {''.join(c for i,c in enumerate(s) if mask>>i&1) for mask in range(1<<len(s))}


def chunks(xs):
    best=0
    for cuts in range(1<<(len(xs)-1)):
        parts=[];start=0
        for i in range(len(xs)-1):
            if cuts>>i&1:parts.append(sorted(xs[start:i+1]));start=i+1
        parts.append(sorted(xs[start:]))
        if sum(parts,[])==sorted(xs):best=max(best,len(parts))
    return best


@lru_cache(None)
def ttt_states():
    valid=set();lines=[(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]
    def play(board,turn):
        if board in valid:return
        valid.add(board)
        if any(board[a]!=' ' and board[a]==board[b]==board[c] for a,b,c in lines):return
        for i,c in enumerate(board):
            if c==' ':play(board[:i]+turn+board[i+1:],'O' if turn=='X' else 'X')
    play(' '*9,'X');return valid


@lru_cache(None)
def puzzle_distances():
    start=(1,2,3,4,5,0);dist={start:0};queue=deque([start])
    while queue:
        state=queue.popleft();i=state.index(0);r,c=divmod(i,3)
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr,nc=r+dr,c+dc
            if 0<=nr<2 and 0<=nc<3:
                j=nr*3+nc;a=list(state);a[i],a[j]=a[j],a[i];nxt=tuple(a)
                if nxt not in dist:dist[nxt]=dist[state]+1;queue.append(nxt)
    return dist


@lru_cache(None)
def monotones():
    return sorted({int(''.join(d)) for n in range(1,11) for d in combinations_with_replacement('0123456789',n) if int(''.join(d))<=10**9})


def tilings(n):
    # Enumerate local exact covers, then transfer the two frontier occupancy bits.
    transitions={}
    for initial in range(4):
        end=Counter()
        def fill(mask):
            if mask&3==3:end[mask>>2]+=1;return
            first=1 if not(mask&1) else 2
            for tile in (3,5,10,7,11,13,14):
                if tile&first and not(tile&mask):fill(tile|mask)
        fill(initial);transitions[initial]=end
    states={0:1}
    for _ in range(n):
        nxt=Counter()
        for before,count in states.items():
            for after,ways in transitions[before].items():nxt[after]=(nxt[after]+count*ways)%1000000007
        states=nxt
    return states.get(0,0)


def expected(pid,a):
    x=a[0]
    if pid==712:
        common=subs(x)&subs(a[1]);return sum(map(ord,x+a[1]))-2*max(map(lambda s:sum(map(ord,s)),common))
    if pid==713:return sum(math.prod(x[i:j])<a[1] for i in range(len(x)) for j in range(i+1,len(x)+1))
    if pid==714:
        @lru_cache(None)
        def f(day,held):
            if day==len(x):return 0 if not held else -10**9
            return max(f(day+1,held),x[day]-a[1]+f(day+1,False) if held else -x[day]+f(day+1,True))
        return f(0,False)
    if pid==717:
        bits=''.join(map(str,x));return bool(re.fullmatch(r'(?:0|10|11)*',bits[:-1]))
    if pid==718:
        left={tuple(x[i:j]) for i in range(len(x)) for j in range(i+1,len(x)+1)}
        return max([0]+[j-i for i in range(len(a[1])) for j in range(i+1,len(a[1])+1) if tuple(a[1][i:j])in left])
    if pid==720:
        valid=[w for w in x if all(w[:i]in x for i in range(1,len(w)+1))]
        return min(valid,key=lambda w:(-len(w),w)) if valid else ''
    if pid==722:
        # One whole-stream lexer; regex alternation gives the earliest opening marker.
        text='\n'.join(x)
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
        return [line for line in text.split('\n') if line]
    if pid==735:
        values=x[:]
        while True:
            pair=next((i for i in range(len(values)-1) if values[i]>0>values[i+1]),None)
            if pair is None:return values
            left,right=values[pair:pair+2]
            replacement=[] if left==-right else [left if left>-right else right]
            values[pair:pair+2]=replacement
    if pid==738:
        import bisect
        return monotones()[bisect.bisect_right(monotones(),x)-1]
    if pid==740:
        counts=Counter(x);vals=list(counts)
        return max(sum(v*counts[v] for i,v in enumerate(vals) if mask>>i&1) for mask in range(1<<len(vals)) if all(not(mask>>i&1 and mask>>j&1) or abs(l-r)!=1 for i,l in enumerate(vals) for j,r in enumerate(vals) if i<j))
    if pid==743:
        edges,n,start=a;dist=[[10**9]*n for _ in range(n)]
        for i in range(n):dist[i][i]=0
        for u,v,w in edges:dist[u-1][v-1]=w
        for k in range(n):
            for i in range(n):
                for j in range(n):dist[i][j]=min(dist[i][j],dist[i][k]+dist[k][j])
        return -1 if max(dist[start-1])>=10**9 else max(dist[start-1])
    if pid==746:
        @lru_cache(None)
        def f(i):return 0 if i>=len(x) else x[i]+min(f(i+1),f(i+2))
        return min(f(0),f(1))
    if pid==748:
        need=Counter(c.lower() for c in x if c in string.ascii_letters)
        candidates=[(len(w),i,w) for i,w in enumerate(a[1]) if not(need-Counter(w))]
        return min(candidates)[2]
    if pid==752:
        dead={int(s)for s in x};target=int(a[1]);start=0
        if start in dead:return -1
        dist={start:0};q=deque([start])
        while q:
            cur=q.popleft()
            if cur==target:return dist[cur]
            for place in (1,10,100,1000):
                digit=(cur//place)%10
                for delta in (-1,1):
                    nxt=cur-digit*place+((digit+delta)%10)*place
                    if nxt not in dead and nxt not in dist:dist[nxt]=dist[cur]+1;q.append(nxt)
        return -1
    if pid==754:
        goal=abs(x);steps=(math.isqrt(8*goal+1)-1)//2
        while steps*(steps+1)//2<goal or (steps*(steps+1)//2-goal)%2:steps+=1
        return steps
    if pid==760:return None
    if pid==763:
        cuts=[i for i in range(1,len(x)+1)if not(set(x[:i])&set(x[i:]))]
        return [r-l for l,r in zip([0]+cuts,cuts)]
    if pid==764:
        n,mines=a;blocked=set(map(tuple,mines));best=0
        for r,c in product(range(n),repeat=2):
            for order in range(1,n+1):
                cells={(r,c)}|{(r+dr*d,c+dc*d) for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)) for d in range(1,order)}
                if all(0<=i<n and 0<=j<n and (i,j)not in blocked for i,j in cells):best=max(best,order)
        return best
    if pid==766:
        diagonals={}
        for r,row in enumerate(x):
            for c,v in enumerate(row):diagonals.setdefault(r-c,set()).add(v)
        return all(len(v)==1 for v in diagonals.values())
    if pid in (768,769):return chunks(x)
    if pid==773:return puzzle_distances().get(tuple(sum(x,[])),-1)
    if pid==775:return sum(x[i]>x[j]for i,j in combinations(range(len(x)),2))==sum(l>r for l,r in zip(x,x[1:]))
    if pid==777:
        target=a[1];seen={x};q=deque([x])
        while q:
            state=q.popleft()
            if state==target:return True
            for i in range(len(state)-1):
                if state[i:i+2]in ('XL','RX'):
                    nxt=state[:i]+state[i:i+2][::-1]+state[i+2:]
                    if nxt not in seen:seen.add(nxt);q.append(nxt)
        return False
    if pid==778:
        n=len(x)
        for height in sorted(sum(x,[])):
            if x[0][0]>height:continue
            seen={(0,0)};q=deque(seen)
            while q:
                r,c=q.popleft()
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr,nc=r+dr,c+dc
                    if 0<=nr<n and 0<=nc<n and (nr,nc)not in seen and x[nr][nc]<=height:seen.add((nr,nc));q.append((nr,nc))
            if (n-1,n-1)in seen:return height
    if pid==779:
        # The symbol is the side parity along its explicit binary ancestor path.
        n,k=a
        if n==1:return 0
        half=1<<(n-2)
        return expected(pid,[n-1,k]) if k<=half else 1-expected(pid,[n-1,k-half])
    if pid==780:
        sx,sy,tx,ty=a;seen={(sx,sy)};q=deque(seen)
        while q:
            p=q.popleft()
            if p==(tx,ty):return True
            l,r=p
            for nxt in ((l+r,r),(l,l+r)):
                if nxt[0]<=tx and nxt[1]<=ty and nxt not in seen:seen.add(nxt);q.append(nxt)
        return False
    if pid==781:
        return sum((value+1)*math.ceil(count/(value+1))for value,count in Counter(x).items())
    if pid==785:return any(all((mask>>i&1)!=(mask>>j&1)for i,row in enumerate(x)for j in row) for mask in range(1<<len(x)))
    if pid==786:return list(sorted(((Fraction(l,r),l,r)for l,r in combinations(x,2)))[a[1]-1][1:])
    if pid==787:
        n,flights,src,dst,k=a
        @lru_cache(None)
        def f(node,edges):
            answer=0 if node==dst else 10**9
            if edges:
                for u,v,cost in flights:
                    if u==node:answer=min(answer,cost+f(v,edges-1))
            return answer
        value=f(src,k+1);return -1 if value>=10**9 else value
    if pid==788:
        rotated=str.maketrans('0125689','0152986');return sum(set(str(n))<=set('0125689') and str(n).translate(rotated)!=str(n) for n in range(1,x+1))
    if pid==789:
        target=a[1];time=abs(target[0])+abs(target[1]);return all(abs(p[0]-target[0])+abs(p[1]-target[1])>time for p in x)
    if pid==790:return tilings(x)
    if pid==791:return None
    if pid==792:
        available=subs(x);return sum(w in available for w in a[1])
    if pid==793:
        def f(n):return sum(n//(5**p)for p in range(1,16))
        def lower(k):
            lo,hi=0,5*(k+1)
            while lo<hi:
                mid=(lo+hi)//2
                if f(mid)<k:lo=mid+1
                else:hi=mid
            return lo
        return lower(x+1)-lower(x)
    if pid==794:return ''.join(x)in ttt_states()
    if pid==795:return sum(a[1]<=max(x[i:j])<=a[2]for i in range(len(x))for j in range(i+1,len(x)+1))
    if pid==797:
        n=len(x);answer=[]
        for length in range(n-1):
            for inside in permutations(range(1,n-1),length):
                path=[0,*inside,n-1]
                if all(v in x[u]for u,v in zip(path,path[1:])):answer.append(path)
        return sorted(answer)
    if pid==807:
        return sum(min(max(row),max(x[i][c]for i in range(len(x))))-v for row in x for c,v in enumerate(row))
    if pid==810:
        @lru_cache(None)
        def win(state):
            xor=0
            for value in state:xor^=value
            if xor==0:return True
            return any((xor^v)!=0 and not win(state[:i]+state[i+1:])for i,v in enumerate(state))
        return win(tuple(sorted(x)))
    if pid==811:
        counts=Counter()
        for entry in x:
            count,domain=entry.split();parts=domain.split('.')
            for i in range(len(parts)):counts['.'.join(parts[i:])]+=int(count)
        return sorted(str(n)+' '+domain for domain,n in counts.items())
    if pid==819:
        words=[];word=''
        for ch in x+' ':
            if ch in string.ascii_letters:word+=ch.lower()
            elif word:words.append(word);word=''
        counts=Counter(w for w in words if w not in a[1]);best=max(counts.values());answer=[w for w,n in counts.items()if n==best];assert len(answer)==1
        return answer[0]
    if pid==820:
        words=list(set(x));answer=10**9
        for mask in range(1,1<<len(words)):
            chosen=[w for i,w in enumerate(words)if mask>>i&1]
            if all(any(c.endswith(w)for c in chosen)for w in words):answer=min(answer,sum(len(c)+1 for c in chosen))
        return answer
    if pid==822:
        best=10**9
        for mask in range(1<<len(x)):
            fronts=[a[(mask>>i)&1][i]for i in range(len(x))];backs=[a[1-((mask>>i)&1)][i]for i in range(len(x))]
            best=min([best]+[v for v in backs if v not in fronts])
        return 0 if best==10**9 else best
    if pid==825:return sum(j!=i and not(b<=l/2+7 or b>l or (b>100 and l<100))for i,l in enumerate(x)for j,b in enumerate(x))
    if pid==826:return sum(max([0]+[p for d,p in zip(x,a[1])if d<=w])for w in a[2])
    if pid==829:
        value=x
        while value%2==0:value//=2
        divisors=1;p=3
        while p*p<=value:
            count=0
            while value%p==0:value//=p;count+=1
            divisors*=count+1;p+=2
        return divisors*(2 if value>1 else 1)
    if pid==831:
        if '@'in x:
            name,domain=x.lower().split('@');return name[0]+'*****'+name[-1]+'@'+domain
        digits=''.join(c for c in x if c in string.digits);country=len(digits)-10
        return ('+'+'*'*country+'-'if country else '')+'***-***-'+digits[-4:]
    if pid==833:
        matches={i:(s,t)for i,s,t in zip(*a[1:])if x.startswith(s,i)};answer='';i=0
        while i<len(x):
            if i in matches:s,t=matches[i];answer+=t;i+=len(s)
            else:answer+=x[i];i+=1
        return answer
    if pid==835:
        n=len(x);return max(sum(x[r][c]*a[1][r+dr][c+dc]for r,c in product(range(n),repeat=2)if 0<=r+dr<n and 0<=c+dc<n)for dr,dc in product(range(-n+1,n),repeat=2))
    if pid==838:
        state=x
        while True:
            out=list(state)
            for i,c in enumerate(state):
                if c!='.':continue
                left=i>0 and state[i-1]=='R';right=i+1<len(state)and state[i+1]=='L'
                if left!=right:out[i]='R'if left else'L'
            nxt=''.join(out)
            if nxt==state:return state
            state=nxt
    if pid==839:
        words=set(x);groups=0
        while words:
            groups+=1;word=words.pop();queue=[word]
            for w in queue:
                for i,j in combinations(range(len(w)),2):
                    t=list(w);t[i],t[j]=t[j],t[i];nxt=''.join(t)
                    if nxt in words:words.remove(nxt);queue.append(nxt)
        return groups
    if pid==840:
        count=0
        for r in range(len(x)-2):
            for c in range(len(x[0])-2):
                square=[row[c:c+3]for row in x[r:r+3]]
                if set(sum(square,[]))!=set(range(1,10)):continue
                totals=list(map(sum,square))+[sum(row[j]for row in square)for j in range(3)]+[sum(square[i][i]for i in range(3)),sum(square[i][2-i]for i in range(3))]
                count+=len(set(totals))==1
        return count
    if pid==841:
        reach=[set(row)|{i}for i,row in enumerate(x)]
        for k in range(len(x)):
            for i in range(len(x)):
                if k in reach[i]:reach[i]|=reach[k]
        return len(reach[0])==len(x)
    if pid==845:
        best=0
        for i in range(len(x)):
            for j in range(i+3,len(x)+1):
                s=x[i:j]
                if any(all(l<r for l,r in zip(s[:k],s[1:k+1]))and all(l>r for l,r in zip(s[k:],s[k+1:]))for k in range(1,len(s)-1)):best=max(best,len(s))
        return best
    if pid==846:
        g=a[1]
        @lru_cache(None)
        def cover(remaining):
            if not remaining:return True
            if len(remaining)<g:return False
            for indices in combinations(range(len(remaining)),g):
                selected=[remaining[i]for i in indices]
                if all(r==l+1 for l,r in zip(selected,selected[1:])) and cover(tuple(v for i,v in enumerate(remaining)if i not in indices)):return True
            return False
        return len(x)%g==0 and cover(tuple(sorted(x)))
    if pid==848:return ''.join(chr(97+(ord(c)-97+sum(a[1][i:]))%26)for i,c in enumerate(x))
    if pid==849:return max(min(abs(i-j)for j,v in enumerate(x)if v)for i,v in enumerate(x)if not v)
    raise ValueError(pid)


def exact(x,y):
    if type(x)is not type(y):return False
    if type(x)is list:return len(x)==len(y)and all(exact(l,r)for l,r in zip(x,y))
    return x==y


def matches(pid,args,value,want):
    if pid==760:return type(value)is list and len(value)==len(args[0])and all(type(j)is int and 0<=j<len(args[1])and args[0][i]==args[1][j]for i,j in enumerate(value))
    if pid==791:
        if type(value)is not str or Counter(value)!=Counter(args[1]):return False
        rank={c:i for i,c in enumerate(args[0])};relevant=[rank[c]for c in value if c in rank]
        return relevant==sorted(relevant)
    if pid in (797,811):
        if type(value)is not list:return False
        try:return exact(sorted(value),want)
        except TypeError:return False
    return exact(value,want)


def compare(pid,args,want,record,language):
    if 'error'in record:return False,'candidate_error'
    kind=list if pid==760 else str if pid==791 else type(want)
    types={'python':{list:'list',int:'int',bool:'bool',str:'str'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string'}}
    if record.get('result_type')!=types[language][kind]:return False,'result_type'
    if not matches(pid,args,record.get('result'),want):return False,'result_value'
    if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
    if record.get('alias_edges')!=[]:return False,'mutable_alias'
    return True,None

MANDATORY_FAILURES={}
