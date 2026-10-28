"""Definition-based batch05 references; no supplied solution is imported.

These are host references and predicates, not an execution engine. Full public
input bounds and practical reference budgets are separate. Seven unavailable
official definitions fail closed rather than inheriting a guessed contract.
"""
from collections import Counter, deque
from fractions import Fraction
from functools import lru_cache
from itertools import combinations, permutations, product
import heapq
import math
import re

IDS = (553,554,556,560,562,565,567,576,581,583,592,593,598,609,611,616,
       621,624,625,633,634,636,638,640,646,647,648,649,650,651,658,659,
       665,668,670,672,673,678,680,681,684,686,688,692,694,695,698)
BLOCKED_IDS = (562,616,625,634,651,681,694)
EXECUTABLE_IDS = tuple(i for i in IDS if i not in BLOCKED_IDS)
MOD = 10**9 + 7


def integer(x, low, high):
    return type(x) is int and low <= x <= high


def array(x, low, high, minimum=1, maximum=100000):
    return type(x) is list and minimum <= len(x) <= maximum and all(integer(v,low,high) for v in x)


def letters(x, alphabet, minimum=1, maximum=100000):
    return type(x) is str and minimum <= len(x) <= maximum and all(c in alphabet for c in x)


def grid(x, maximum=50):
    return (type(x) is list and 1 <= len(x) <= maximum and type(x[0]) is list
            and 1 <= len(x[0]) <= maximum and all(array(r,0,1,len(x[0]),len(x[0])) for r in x))


def log_spans(n, logs):
    stack, spans, last, starts, ends = [], [], 0, set(), set()
    for raw in logs:
        match = re.fullmatch(r'(0|[1-9][0-9]*):(start|end):(0|[1-9][0-9]*)',raw) if type(raw) is str else None
        if match is None: raise ValueError('invalid exclusive-time event')
        ident, kind, time = int(match[1]), match[2], int(match[3])
        if not 0 <= ident < n or not 0 <= time <= 10**9: raise ValueError('event domain')
        instant = time if kind == 'start' else time+1
        if instant < last: raise ValueError('events are not in execution order')
        last = instant
        if kind == 'start':
            if time in starts: raise ValueError('duplicate start timestamp')
            starts.add(time); stack.append((ident,time,len(stack)))
        else:
            if time in ends or not stack or stack[-1][0] != ident or stack[-1][1] > time:
                raise ValueError('unbalanced exclusive-time events')
            ends.add(time); ident,start,depth = stack.pop(); spans.append((ident,start,time+1,depth))
    if stack: raise ValueError('unfinished function call')
    return spans


def equation_terms(side):
    if not re.fullmatch(r'[+-]?(?:[0-9]+x?|x)(?:[+-](?:[0-9]+x?|x))*',side):
        raise ValueError('invalid equation syntax')
    coefficient = constant = 0
    for term in re.findall(r'[+-]?(?:[0-9]+x?|x)',side):
        variable = term.endswith('x'); number = term[:-1] if variable else term
        sign = -1 if number.startswith('-') else 1; number = number.lstrip('+-')
        if number and (len(number)>1 and number[0]=='0' or int(number)>100):
            raise ValueError('equation coefficient outside domain')
        value = sign*(int(number) if number else 1)
        if variable: coefficient += value
        else: constant += value
    return coefficient, constant


def validate_generated(pid, args):
    if type(pid) is not int or pid not in EXECUTABLE_IDS:
        raise ValueError('no verified public definition for this assigned identity')
    arity = {560:2,567:2,576:5,583:2,593:4,598:3,621:2,636:2,638:3,648:2,
             658:3,668:3,672:2,686:2,688:4,692:2,698:2}
    if type(args) is not list or len(args) != arity.get(pid,1): raise ValueError('ordered argument shape')
    x=args[0]; good=False
    if pid==553: good=array(x,2,1000,1,10)
    elif pid==554:
        good=(type(x) is list and 1<=len(x)<=10000 and all(array(r,1,2**31-1,1,10000) for r in x)
              and sum(map(len,x))<=20000 and len({sum(r) for r in x})==1)
    elif pid==556: good=integer(x,1,2**31-1)
    elif pid==560: good=array(x,-1000,1000,1,20000) and integer(args[1],-10**7,10**7)
    elif pid==565: good=array(x,0,len(x)-1,1,100000) and len(set(x))==len(x) if type(x) is list else False
    elif pid==567: good=all(letters(s,'abcdefghijklmnopqrstuvwxyz',1,10000) for s in args)
    elif pid==576:
        m,n,moves,r,c=args;good=integer(m,1,50) and integer(n,1,50) and integer(moves,0,50) and integer(r,0,m-1) and integer(c,0,n-1)
    elif pid in (581,665): good=array(x,-100000,100000,1,10000)
    elif pid==583: good=all(letters(s,'abcdefghijklmnopqrstuvwxyz',1,500) for s in args)
    elif pid==592:
        terms=re.findall(r'[+-]?[0-9]+/[0-9]+',x) if type(x) is str else []
        good=1<=len(terms)<=10 and ''.join(terms)==x
        if good:
            values=[tuple(map(int,t.split('/'))) for t in terms]
            good=all(1<=abs(n)<=10 and 1<=d<=10 and math.gcd(n,d)==1 for n,d in values)
    elif pid==593: good=all(array(p,-10000,10000,2,2) for p in args)
    elif pid==598:
        m,n,ops=args;good=integer(m,1,40000) and integer(n,1,40000) and type(ops) is list and len(ops)<=10000 and all(type(p) is list and len(p)==2 and integer(p[0],1,m) and integer(p[1],1,n) for p in ops)
    elif pid==609:
        good=type(x) is list and 1<=len(x)<=20000 and all(type(s) is str and 1<=len(s)<=3000 and re.fullmatch(r'[A-Za-z0-9/.]+(?: [A-Za-z0-9.]+\([A-Za-z0-9.]+\))+',s) for s in x) and sum(map(len,x))<=500000
        if good:
            directories=[s.split()[0] for s in x]
            good=len(set(directories))==len(directories) and all(len({f.split('(')[0] for f in s.split()[1:]})==len(s.split())-1 for s in x)
    elif pid==611: good=array(x,0,1000,1,1000)
    elif pid==621: good=type(x) is list and 1<=len(x)<=10000 and all(letters(c,'ABCDEFGHIJKLMNOPQRSTUVWXYZ',1,1) for c in x) and integer(args[1],0,100)
    elif pid==624: good=type(x) is list and 2<=len(x)<=100000 and all(array(r,-10000,10000,1,500) and all(a<=b for a,b in zip(r,r[1:])) for r in x) and sum(map(len,x))<=100000
    elif pid==633: good=integer(x,0,2**31-1)
    elif pid==636:
        good=integer(x,1,100) and type(args[1]) is list and 2<=len(args[1])<=500
        if good: log_spans(x,args[1])
    elif pid==638:
        price,special,needs=args;n=len(price) if type(price) is list else 0
        good=array(price,0,10,1,6) and array(needs,0,10,n,n) and type(special) is list and 1<=len(special)<=100 and all(array(row,0,50,n+1,n+1) and any(row[:-1]) for row in special)
    elif pid==640:
        good=type(x) is str and 3<=len(x)<=1000 and x.count('=')==1
        if good:
            left,right=map(equation_terms,x.split('='));a=left[0]-right[0];b=right[1]-left[1]
            good=not a or b%a==0
    elif pid==646: good=type(x) is list and 1<=len(x)<=1000 and all(array(p,-1000,1000,2,2) and p[0]<p[1] for p in x)
    elif pid==647: good=letters(x,'abcdefghijklmnopqrstuvwxyz',1,1000)
    elif pid==648:
        dictionary,sentence=args;good=type(dictionary) is list and 1<=len(dictionary)<=1000 and all(letters(w,'abcdefghijklmnopqrstuvwxyz',1,100) for w in dictionary) and type(sentence) is str and 1<=len(sentence)<=10**6 and 1<=len(sentence.split(' '))<=1000 and all(letters(w,'abcdefghijklmnopqrstuvwxyz',1,1000) for w in sentence.split(' '))
    elif pid==649: good=letters(x,'RD',1,10000)
    elif pid==650: good=integer(x,1,1000)
    elif pid==658: good=array(x,-10000,10000,1,10000) and all(a<=b for a,b in zip(x,x[1:])) and integer(args[1],1,len(x)) and integer(args[2],-10000,10000)
    elif pid==659: good=array(x,-1000,1000,1,10000) and all(a<=b for a,b in zip(x,x[1:]))
    elif pid==668: good=integer(x,1,30000) and integer(args[1],1,30000) and integer(args[2],1,x*args[1])
    elif pid==670: good=integer(x,0,10**8)
    elif pid==672: good=integer(x,1,1000) and integer(args[1],0,1000)
    elif pid==673: good=array(x,-10**6,10**6,1,2000)
    elif pid==678: good=letters(x,'()*',1,100)
    elif pid==680: good=letters(x,'abcdefghijklmnopqrstuvwxyz',1,100000)
    elif pid==684:
        n=len(x) if type(x) is list else 0
        good=type(x) is list and 3<=n<=1000 and all(array(e,1,n,2,2) and e[0]<e[1] for e in x) and len(set(map(tuple,x)))==n
        if good:
            adjacency=[[] for _ in range(n+1)]
            for a,b in x: adjacency[a].append(b);adjacency[b].append(a)
            seen={1};todo=[1]
            for a in todo:
                for b in adjacency[a]:
                    if b not in seen:seen.add(b);todo.append(b)
            good=len(seen)==n
    elif pid==686: good=all(letters(s,'abcdefghijklmnopqrstuvwxyz',1,10000) for s in args)
    elif pid==688:
        n,k,r,c=args;good=integer(n,1,25) and integer(k,0,100) and integer(r,0,n-1) and integer(c,0,n-1)
    elif pid==692: good=type(x) is list and 1<=len(x)<=500 and all(letters(w,'abcdefghijklmnopqrstuvwxyz',1,10) for w in x) and integer(args[1],1,len(set(x)))
    elif pid==695: good=grid(x)
    elif pid==698: good=array(x,1,10000,1,16) and integer(args[1],1,len(x)) and max(Counter(x).values())<=4
    if not good: raise ValueError('outside pinned public input domain')


@lru_cache(maxsize=512)
def divisions(values):
    if len(values)==1:return ((Fraction(values[0]),str(values[0])),)
    results={}
    for split in range(1,len(values)):
        for a,left in divisions(values[:split]):
            for b,right in divisions(values[split:]):
                value=a/b;expression=left+'/'+('('+right+')' if len(values[split:])>1 else right)
                results.setdefault(value,expression)
    return tuple(results.items())


def parse_division(expression):
    tokens=re.findall(r'[0-9]+|[()/]',expression) if type(expression) is str else []
    if not tokens or ''.join(tokens)!=expression: raise ValueError('division expression syntax')
    cursor=0;leaves=[]
    def atom():
        nonlocal cursor
        if cursor>=len(tokens):raise ValueError('missing division operand')
        t=tokens[cursor];cursor+=1
        if t=='(':
            value,text=sequence()
            if cursor>=len(tokens) or tokens[cursor]!=')':raise ValueError('unclosed division')
            cursor+=1;return value,text,'/' not in text
        if not t.isdecimal() or (len(t)>1 and t[0]=='0'):raise ValueError('invalid operand')
        leaves.append(int(t));return Fraction(int(t)),t,True
    def sequence():
        nonlocal cursor
        value,text,_=atom()
        while cursor<len(tokens) and tokens[cursor]=='/':
            cursor+=1;denom,right,single=atom();value/=denom;text+='/'+(right if single else '('+right+')')
        return value,text
    value,canonical=sequence()
    if cursor!=len(tokens):raise ValueError('trailing division tokens')
    return value,leaves,canonical


@lru_cache(maxsize=4096)
def task_schedule(counts, cooldowns, gap):
    if not any(counts): return 0
    choices=[i for i,c in enumerate(counts) if c and not cooldowns[i]]
    if not choices:
        skip=min(t for c,t in zip(counts,cooldowns) if c)
        return skip+task_schedule(counts,tuple(max(0,t-skip) for t in cooldowns),gap)
    answers=[]
    for i in choices:
        left=list(counts);left[i]-=1;times=[max(0,t-1) for t in cooldowns];times[i]=gap
        answers.append(1+task_schedule(tuple(left),tuple(times),gap))
    return min(answers)


@lru_cache(maxsize=4096)
def senate_winner(word, mask, turn):
    alive=[i for i in range(len(word)) if mask>>i&1]
    parties={word[i] for i in alive}
    if len(parties)==1:return next(iter(parties))
    actor=next((turn+d)%len(word) for d in range(len(word)) if mask>>((turn+d)%len(word))&1)
    party=word[actor];other='D' if party=='R' else 'R'
    for target in alive:
        if word[target]==party:continue
        if senate_winner(word,mask^(1<<target),(actor+1)%len(word))==party:return party
    return other


def expected(pid,args):
    validate_generated(pid,args);x=args[0]
    if pid==553:return max(divisions(tuple(x)),key=lambda row:row[0])[1]
    if pid==554:
        boundaries={sum(r[:i]) for r in x for i in range(1,len(r))}
        return min([len(x)]+[sum(p not in {sum(r[:i]) for i in range(1,len(r))} for r in x) for p in boundaries])
    if pid==556:
        digits=str(x)
        if len(digits)>8: # At most ten digits; count-multiset DFS skips impossible prefixes.
            count=Counter(digits);best=None
            def search(prefix):
                nonlocal best
                if best is not None:return
                if len(prefix)==len(digits):
                    value=int(prefix)
                    if x<value<2**31:best=value
                    return
                for d in sorted(count):
                    if not count[d] or not prefix and d=='0':continue
                    candidate=prefix+d
                    if candidate<digits[:len(candidate)]:continue
                    count[d]-=1;search(candidate);count[d]+=1
            search('');return -1 if best is None else best
        return min([int(''.join(p)) for p in set(permutations(digits)) if p[0]!='0' and x<int(''.join(p))<2**31] or [-1])
    if pid==560:
        if len(x)>200:raise ValueError('bounded contiguous-interval oracle')
        return sum(sum(x[i:j])==args[1] for i in range(len(x)) for j in range(i+1,len(x)+1))
    if pid==565:
        if len(x)>500:raise ValueError('bounded per-start orbit oracle')
        best=0
        for start in range(len(x)):
            seen=set();v=x[start]
            while v not in seen:seen.add(v);v=x[v]
            best=max(best,len(seen))
        return best
    if pid==567:
        if len(args[1])>1000:raise ValueError('bounded literal-window oracle')
        return any(sorted(args[1][i:i+len(x)])==sorted(x) for i in range(len(args[1])-len(x)+1))
    if pid==576:
        m,n,moves,r,c=args;states={(r,c):1};answer=0
        for _ in range(moves):
            nxt=Counter()
            for (r,c),count in states.items():
                for dr,dc in ((0,1),(0,-1),(1,0),(-1,0)):
                    rr,cc=r+dr,c+dc
                    if 0<=rr<m and 0<=cc<n:nxt[rr,cc]+=count
                    else:answer+=count
            states={p:v%MOD for p,v in nxt.items()};answer%=MOD
        return answer
    if pid==581:
        if len(x)>100:raise ValueError('bounded sorted-interval oracle')
        target=sorted(x)
        if x==target:return 0
        return min(j-i for i in range(len(x)) for j in range(i+1,len(x)+1) if x[:i]+sorted(x[i:j])+x[j:]==target)
    if pid==583:
        if max(map(len,args))>15:raise ValueError('bounded deletion-subsequence oracle')
        sets=[]
        for s in args:sets.append({''.join(s[i] for i in range(len(s)) if mask>>i&1) for mask in range(1<<len(s))})
        return len(x)+len(args[1])-2*max(map(len,sets[0]&sets[1]))
    if pid==592:
        value=sum((Fraction(t) for t in re.findall(r'[+-]?[0-9]+/[0-9]+',x)),Fraction())
        return str(value.numerator)+'/'+str(value.denominator)
    if pid==593:
        for p in permutations(args):
            vectors=[(p[(i+1)%4][0]-p[i][0],p[(i+1)%4][1]-p[i][1]) for i in range(4)]
            lengths=[a*a+b*b for a,b in vectors]
            if lengths[0]>0 and len(set(lengths))==1 and all(vectors[i][0]*vectors[(i+1)%4][0]+vectors[i][1]*vectors[(i+1)%4][1]==0 for i in range(4)):return True
        return False
    if pid==598:
        m,n,ops=args
        if m*n>10000:raise ValueError('bounded explicit matrix oracle')
        counts=[sum(r<a and c<b for a,b in ops) for r in range(m) for c in range(n)]
        return counts.count(max(counts))
    if pid==609:
        content={}
        for row in x:
            directory,*files=row.split()
            for value in files:
                name,body=value.split('(',1);content[directory+'/'+name]=body[:-1]
        return [sorted(path for path,value in content.items() if value==body) for body in sorted(set(content.values())) if sum(value==body for value in content.values())>1]
    if pid==611:
        if len(x)>100:raise ValueError('bounded triangle triple oracle')
        return sum(a+b>c and a+c>b and b+c>a for a,b,c in combinations(x,3))
    if pid==621:
        if len(x)>12 or len(set(x))>5:raise ValueError('bounded schedule state oracle')
        counts=tuple(Counter(x)[t] for t in sorted(set(x)))
        return task_schedule(counts,(0,)*len(counts),args[1])
    if pid==624:
        if sum(map(len,x))>500:raise ValueError('bounded cross-array pair oracle')
        return max(abs(a-b) for i in range(len(x)) for j in range(i+1,len(x)) for a in x[i] for b in x[j])
    if pid==633:return any(math.isqrt(x-a*a)**2==x-a*a for a in range(math.isqrt(x)+1))
    if pid==636:
        spans=log_spans(x,args[1]);points=sorted({p for _,s,e,_ in spans for p in (s,e)});out=[0]*x
        for a,b in zip(points,points[1:]):
            live=[(d,i) for i,s,e,d in spans if s<=a and b<=e]
            if live:out[max(live)[1]]+=b-a
        return out
    if pid==638:
        price,special,needs=args
        if math.prod(v+1 for v in needs)>50000:raise ValueError('bounded quantity-state shortest path oracle')
        target=tuple(needs);start=(0,)*len(price);dist={start:0};todo=[(0,start)]
        actions=[tuple(int(i==j) for i in range(len(price)))+(value,) for j,value in enumerate(price)]+[tuple(s) for s in special]
        while todo:
            cost,state=heapq.heappop(todo)
            if cost!=dist[state]:continue
            if state==target:return cost
            for action in actions:
                nxt=tuple(a+b for a,b in zip(state,action))
                if any(a>b for a,b in zip(nxt,target)):continue
                value=cost+action[-1]
                if value<dist.get(nxt,math.inf):dist[nxt]=value;heapq.heappush(todo,(value,nxt))
        raise AssertionError('individual purchases always reach needs')
    if pid==640:
        left,right=map(equation_terms,x.split('='));a=left[0]-right[0];b=right[1]-left[1]
        return ('Infinite solutions' if b==0 else 'No solution') if a==0 else 'x='+str(b//a)
    if pid==646:
        if len(x)>16:raise ValueError('bounded chain subset oracle')
        best=0
        for mask in range(1<<len(x)):
            chosen=sorted(x[i] for i in range(len(x)) if mask>>i&1)
            if all(a[1]<b[0] for a,b in zip(chosen,chosen[1:])):best=max(best,len(chosen))
        return best
    if pid==647:return sum(x[i:j]==x[i:j][::-1] for i in range(len(x)) for j in range(i+1,len(x)+1)) if len(x)<=300 else _budget()
    if pid==648:return ' '.join(min([r for r in x if w.startswith(r)]+[w],key=len) for w in args[1].split(' '))
    if pid==649:
        if len(x)>12:raise ValueError('bounded adversarial ban-tree oracle')
        return 'Radiant' if senate_winner(x,(1<<len(x))-1,0)=='R' else 'Dire'
    if pid==650:
        todo=deque([(1,0,0)]);seen={(1,0)}
        while todo:
            screen,clip,cost=todo.popleft()
            if screen==x:return cost
            for nxt in ((screen,screen),(screen+clip,clip)):
                if nxt[0]<=x and nxt not in seen:seen.add(nxt);todo.append((*nxt,cost+1))
    if pid==658:return sorted(sorted(x,key=lambda v:(abs(v-args[2]),v))[:args[1]])
    if pid==659:
        if len(x)>18:raise ValueError('bounded exact multiset cover oracle')
        keys=tuple(sorted(set(x)));initial=tuple(Counter(x)[k] for k in keys)
        @lru_cache(None)
        def cover(counts):
            if not any(counts):return True
            first=next(i for i,v in enumerate(counts) if v);left=list(counts);last=keys[first]-1
            for i in range(first,len(keys)):
                if keys[i]!=last+1 or not left[i]:break
                left[i]-=1;last=keys[i]
                if i-first+1>=3 and cover(tuple(left)):return True
            return False
        return cover(initial)
    if pid==665:
        prefix=[True]*len(x);suffix=[True]*len(x)
        for i in range(1,len(x)):prefix[i]=prefix[i-1] and x[i-1]<=x[i]
        for i in range(len(x)-2,-1,-1):suffix[i]=suffix[i+1] and x[i]<=x[i+1]
        return any((i==0 or prefix[i-1]) and (i==len(x)-1 or suffix[i+1]) and (i==0 or i==len(x)-1 or x[i-1]<=x[i+1]) for i in range(len(x)))
    if pid==668:
        m,n,k=args
        if m*n>20000:raise ValueError('bounded materialized multiplication table oracle')
        return sorted(i*j for i in range(1,m+1) for j in range(1,n+1))[k-1]
    if pid==670:
        digits=list(str(x));best=x
        for i,j in combinations(range(len(digits)),2):
            d=digits[:];d[i],d[j]=d[j],d[i];best=max(best,int(''.join(d)))
        return best
    if pid==672:
        n,presses=args;states=set()
        for mask in range(16):
            if mask.bit_count()>presses or (presses-mask.bit_count())%2:continue
            states.add(tuple(sum(bool(mask>>button&1) and condition for button,condition in enumerate((True,i%2==0,i%2==1,i%3==1)))%2 for i in range(1,n+1)))
        return len(states)
    if pid==673:
        if len(x)>18:raise ValueError('bounded index-subsequence oracle')
        best=count=0
        for mask in range(1,1<<len(x)):
            values=[x[i] for i in range(len(x)) if mask>>i&1]
            if all(a<b for a,b in zip(values,values[1:])):
                if len(values)>best:best,count=len(values),1
                elif len(values)==best:count+=1
        return count
    if pid==678:
        balances={0}
        for c in x:
            balances={v+step for v in balances for step in ((1,-1,0) if c=='*' else (1,) if c=='(' else (-1,)) if v+step>=0}
        return 0 in balances
    if pid==680:
        if len(x)>500:raise ValueError('bounded literal-deletion palindrome oracle')
        return x==x[::-1] or any((x[:i]+x[i+1:])==(x[:i]+x[i+1:])[::-1] for i in range(len(x)))
    if pid==684:
        n=len(x)
        for removed in range(n-1,-1,-1):
            adjacency=[[] for _ in range(n+1)]
            for i,(a,b) in enumerate(x):
                if i!=removed:adjacency[a].append(b);adjacency[b].append(a)
            seen={1};todo=[1]
            for v in todo:
                for w in adjacency[v]:
                    if w not in seen:seen.add(w);todo.append(w)
            if len(seen)==n:return x[removed][:]
    if pid==686:return next((i for i in range(1,(len(args[1])+len(x)-1)//len(x)+2) if args[1] in x*i),-1)
    if pid==688:
        n,k,r,c=args;counts={(r,c):1};moves=tuple((a,b) for a in (-2,-1,1,2) for b in (-2,-1,1,2) if abs(a)+abs(b)==3)
        for _ in range(k):
            nxt=Counter()
            for (r,c),count in counts.items():
                for dr,dc in moves:
                    if 0<=r+dr<n and 0<=c+dc<n:nxt[r+dr,c+dc]+=count
            counts=nxt
        return float(Fraction(sum(counts.values()),8**k))
    if pid==692:return sorted(set(x),key=lambda word:(-x.count(word),word))[:args[1]]
    if pid==695:
        land={(r,c) for r,row in enumerate(x) for c,v in enumerate(row) if v};best=0
        while land:
            start=land.pop();todo=[start]
            for r,c in todo:
                for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if p in land:land.remove(p);todo.append(p)
            best=max(best,len(todo))
        return best
    if pid==698:
        nums,k=args;total=sum(nums)
        if total%k:return False
        target=total//k
        if max(nums)>target:return False
        if len(nums)>12:raise ValueError('bounded exact subset-cover oracle')
        @lru_cache(None)
        def subtotal(mask):return sum(nums[i] for i in range(len(nums)) if mask>>i&1)
        @lru_cache(None)
        def cover(mask):
            if not mask:return True
            first=mask&-mask;subset=mask
            while subset:
                if subset&first and subtotal(subset)==target and cover(mask^subset):return True
                subset=(subset-1)&mask
            return False
        return cover((1<<len(nums))-1)
    raise ValueError('unhandled assigned identity')


def _budget():
    raise ValueError('bounded literal substring oracle')


def exact(a,b):
    if type(a) is not type(b):return False
    if type(a) is list:return len(a)==len(b) and all(exact(x,y) for x,y in zip(a,b))
    if type(a) is dict:return a.keys()==b.keys() and all(exact(a[k],b[k]) for k in a)
    return a==b


def matches(pid,args,got,want):
    if pid==553:
        try:
            value,leaves,canonical=parse_division(got)
            return leaves==args[0] and got==canonical and value==max(v for v,_ in divisions(tuple(args[0])))
        except (ValueError,ZeroDivisionError,RecursionError):return False
    if pid==609:
        if type(got) is not list or any(type(group) is not list or any(type(s) is not str for s in group) for group in got):return False
        return sorted(sorted(group) for group in got)==sorted(sorted(group) for group in want)
    if pid==688:return type(got) in (int,float) and math.isfinite(got) and math.isclose(got,want,rel_tol=1e-12,abs_tol=1e-12)
    return exact(got,want)


def compare(pid,args,want,record,language):
    if 'error' in record:return False,'candidate_error'
    if pid==688:
        valid_types=('int','float') if language=='python' else ('number',)
    else:
        kinds={list:'list',int:'int',bool:'bool',str:'str'} if language=='python' else {list:'object',int:'number',bool:'boolean',str:'string'}
        valid_types=(kinds[type(want)],)
    if record.get('result_type') not in valid_types:return False,'result_type'
    if not matches(pid,args,record.get('result'),want):return False,'result_value'
    if not exact(record.get('args_before'),args) or not exact(record.get('args_after'),args):return False,'input_effects'
    if record.get('alias_edges')!=[]:return False,'mutable_return_alias'
    return True,None
