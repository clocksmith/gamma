"""Independent definitions, enumerations and exact host references for batch09."""
from collections import Counter,deque
from functools import lru_cache
from fractions import Fraction
from itertools import combinations,product
import datetime,math,re

DEFINITION_BLOCKED={1151,1167,1182,1183,1196,1197,1198,1228,1243,1271,1272}
MANDATORY_FAILURES={(1219,lang):'Original temporarily writes caller grid cells, then restores; violates strict immutable-input contract'for lang in ('python','javascript')}


def subsequences(xs):
    for mask in range(1<<len(xs)):yield [v for i,v in enumerate(xs)if mask>>i&1]


@lru_cache(None)
def merge_cost(sticks):
    if len(sticks)<2:return 0
    return min(sticks[i]+sticks[j]+merge_cost(tuple(sorted([v for k,v in enumerate(sticks)if k not in (i,j)]+[sticks[i]+sticks[j]])))for i,j in combinations(range(len(sticks)),2))


@lru_cache(None)
def knight_distances():
    q=deque([(0,0)]);distance={(0,0):0}
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,2),(2,1),(1,-2),(2,-1),(-1,2),(-2,1),(-1,-2),(-2,-1)):
            p=x+dx,y+dy
            if max(map(abs,p))<=32 and p not in distance:distance[p]=distance[x,y]+1;q.append(p)
    return distance


def expected(pid,a):
    x=a[0]
    if pid==1151:
        n=sum(x);return min(sum(v==0 for v in x[i:i+n])for i in range(len(x)-n+1))
    if pid==1155:
        n,k,target=a
        if target<n or target>n*k:return 0
        return sum((-1)**j*math.comb(n,j)*math.comb(target-k*j-1,n-1)for j in range(min(n,(target-n)//k)+1))%1000000007
    if pid==1156:
        answer=0
        for i in range(len(x)):
            for j in range(i,len(x)):
                s=list(x);s[i],s[j]=s[j],s[i];current=0;previous=None
                for c in s:
                    current=current+1 if c==previous else 1;previous=c;answer=max(answer,current)
        return answer
    if pid==1162:
        land=[(r,c)for r,row in enumerate(x)for c,v in enumerate(row)if v];water=[(r,c)for r,row in enumerate(x)for c,v in enumerate(row)if not v]
        return -1 if not land or not water else max(min(abs(r-i)+abs(c-j)for i,j in land)for r,c in water)
    if pid==1163:return max(x[i:j]for i in range(len(x))for j in range(i+1,len(x)+1))
    if pid==1167:return merge_cost(tuple(sorted(x)))
    if pid==1169:
        fields=[t.split(',')for t in x];bad={i for i,f in enumerate(fields)if int(f[2])>1000}
        for i,j in combinations(range(len(fields)),2):
            l,r=fields[i],fields[j]
            if l[0]==r[0]and l[3]!=r[3]and abs(int(l[1])-int(r[1]))<=60:bad|={i,j}
        return sorted(x[i]for i in bad)
    if pid==1177:return [sum(n%2 for n in Counter(x[l:r+1]).values())//2<=k for l,r,k in a[1]]
    if pid==1178:return [sum(p[0]in w and set(w)<=set(p)for w in x)for p in a[1]]
    if pid==1182:return [min([abs(j-i)for j,v in enumerate(x)if v==c]or[-1])for i,c in a[1]]
    if pid==1183:
        width,height,side,limit=a;cells=width*height;windows=[]
        for r in range(height-side+1):
            for c in range(width-side+1):windows.append(sum(1<<(i*width+j)for i in range(r,r+side)for j in range(c,c+side)))
        return max(mask.bit_count()for mask in range(1<<cells)if all((mask&w).bit_count()<=limit for w in windows))
    if pid==1185:return ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][datetime.date(a[2],a[1],a[0]).weekday()]
    if pid==1186:return max(sum(x[i:j])-min(0,min(x[i:j]))if j-i>1 else x[i]for i in range(len(x))for j in range(i+1,len(x)+1))
    if pid==1189:
        counts=Counter(x);word=Counter('balloon');answer=0
        while not(word-counts):counts-=word;answer+=1
        return answer
    if pid==1190:
        while '('in x:x=re.sub(r'\(([a-z]*)\)',lambda m:m[1][::-1],x)
        return x
    if pid==1196:return max(len(s)for s in subsequences(x)if sum(s)<=5000)
    if pid==1197:return knight_distances()[x,a[1]]
    if pid==1198:
        common=set(x[0])
        for row in x:common&=set(row)
        return min(common)if common else-1
    if pid==1201:
        n,b,c,d=a;value=0
        while n:
            value+=1
            if value%b==0 or value%c==0 or value%d==0:n-=1
        return value
    if pid==1202:
        seen={x};queue=deque([x]);answer=x
        while queue:
            value=queue.popleft();answer=min(answer,value)
            for i,j in a[1]:
                t=list(value);t[i],t[j]=t[j],t[i];new=''.join(t)
                if new not in seen:seen.add(new);queue.append(new)
        return answer
    if pid==1209:
        pattern=r'(.)\1{'+str(a[1]-1)+'}'
        while True:
            value=re.sub(pattern,'',x)
            if value==x:return x
            x=value
    if pid==1218:return max(len(s)for s in subsequences(x)if all(r-l==a[1]for l,r in zip(s,s[1:])))
    if pid==1219:
        cells=[(r,c)for r,row in enumerate(x)for c,v in enumerate(row)if v];indices={p:i for i,p in enumerate(cells)};front=[(i,1<<i)for i in range(len(cells))];seen=set(front);best=0
        for last,mask in front:
            best=max(best,sum(x[r][c]for i,(r,c)in enumerate(cells)if mask>>i&1));r,c=cells[last]
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                j=indices.get(p)
                if j is not None and not(mask>>j&1):
                    state=j,mask|1<<j
                    if state not in seen:seen.add(state);front.append(state)
        return best
    if pid==1222:
        king=a[1];visible={}
        for r,c in x:
            dr,dc=r-king[0],c-king[1]
            if dr==0 or dc==0 or abs(dr)==abs(dc):
                direction=(0 if dr==0 else 1 if dr>0 else-1,0 if dc==0 else 1 if dc>0 else-1);distance=max(abs(dr),abs(dc))
                if direction not in visible or distance<visible[direction][0]:visible[direction]=(distance,[r,c])
        return sorted(v[1]for v in visible.values())
    if pid==1227:
        n=x
        @lru_cache(None)
        def probability(player,occupied):
            if player==n-1:return Fraction(int(not(occupied>>(n-1)&1)))
            choices=[player]if player and not(occupied>>player&1)else[j for j in range(n)if not(occupied>>j&1)]
            return sum((probability(player+1,occupied|1<<seat)for seat in choices),Fraction())/len(choices)
        return float(probability(0,0))
    if pid==1228:
        n=len(x);difference=Fraction(x[-1]-x[0],n)
        values={Fraction(v)for v in x};missing=[Fraction(x[0])+i*difference for i in range(n+1)if Fraction(x[0])+i*difference not in values]
        return int(missing[0])if missing else x[0]
    if pid==1234:
        target=len(x)//4
        return min(r-l for l in range(len(x)+1)for r in range(l,len(x)+1)if all(n<=target for n in Counter(x[:l]+x[r:]).values()))
    if pid==1238:return None
    if pid==1243:
        while True:
            value=[v+(int(v<min(x[i-1],x[i+1]))-int(v>max(x[i-1],x[i+1])))if 0<i<len(x)-1 else v for i,v in enumerate(x)]
            if value==x:return x
            x=value
    if pid==1249:
        parens=[i for i,c in enumerate(x)if c in'()'];best=0
        for mask in range(1<<len(parens)):
            keep={i for j,i in enumerate(parens)if mask>>j&1};balance=0;valid=True
            for i,c in enumerate(x):
                if i not in keep:continue
                balance+=1 if c=='('else-1
                if balance<0:valid=False;break
            if valid and balance==0:best=max(best,len(keep))
        return len(parens)-best
    if pid==1253:
        upper,lower,cols=a;twos=cols.count(2);ones=cols.count(1)
        return upper>=twos and lower>=twos and upper+lower==sum(cols)and upper-twos<=ones and lower-twos<=ones
    if pid==1254:
        unseen={(r,c)for r,row in enumerate(x)for c,v in enumerate(row)if v==0};answer=0
        while unseen:
            start=next(iter(unseen));unseen.remove(start);component={start};queue=[start]
            for r,c in queue:
                for nxt in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)):
                    if nxt in unseen:unseen.remove(nxt);component.add(nxt);queue.append(nxt)
            answer+=all(0<r<len(x)-1 and 0<c<len(x[0])-1 for r,c in component)
        return answer
    if pid==1255:
        words,letters,scores=a;available=Counter(letters);best=0
        for subset in subsequences(words):
            needed=Counter(''.join(subset))
            if not(needed-available):best=max(best,sum(scores[ord(c)-97]*n for c,n in needed.items()))
        return best
    if pid==1262:return max(sum(s)for s in subsequences(x)if sum(s)%3==0)
    if pid==1268:return [sorted(p for p in x if p.startswith(a[1][:i]))[:3]for i in range(1,len(a[1])+1)]
    if pid==1271:
        text=format(int(x),'X');return text.translate(str.maketrans('01','OI'))if not(set(text)&set('23456789'))else'ERROR'
    if pid==1272:
        remove=a[1];answer=[]
        for start,end in x:
            units=[i for i in range(start,end)if not(remove[0]<=i<remove[1])];groups=[]
            for v in units:
                if groups and groups[-1][-1]+1==v:groups[-1].append(v)
                else:groups.append([v])
            answer.extend([[g[0],g[-1]+1]for g in groups])
        return answer
    if pid==1281:
        digits=list(map(int,str(x)));return math.prod(digits)-sum(digits)
    if pid==1291:
        low,high=a;return sorted(int('123456789'[i:j])for i in range(9)for j in range(i+2,10)if low<=int('123456789'[i:j])<=high)
    if pid==1292:
        return max([0]+[k for k in range(1,min(len(x),len(x[0]))+1)for r in range(len(x)-k+1)for c in range(len(x[0])-k+1)if sum(x[i][j]for i in range(r,r+k)for j in range(c,c+k))<=a[1]])
    raise ValueError(pid)


def exact(a,b):
    if type(a)is not type(b):return False
    return len(a)==len(b)and all(exact(l,r)for l,r in zip(a,b))if type(a)is list else a==b


def matches(pid,args,value,want):
    if pid in (1169,1222):
        if type(value)is not list:return False
        try:return exact(sorted(value),want)
        except TypeError:return False
    if pid==1227:return type(value)in(int,float)and math.isfinite(value)and 0<=value<=1 and abs(value-want)<=1e-5
    if pid==1238:
        n,start=args
        return type(value)is list and len(value)==1<<n and all(type(v)is int and 0<=v<1<<n for v in value)and len(set(value))==len(value)and value[0]==start and all((l^r)>0 and ((l^r)&((l^r)-1))==0 for l,r in zip(value,value[1:]+value[:1]))
    if pid==1249:
        if type(value)is not str or len(value)!=len(args[0])-want:return False
        if re.sub('[()]','',value)!=re.sub('[()]','',args[0]):return False
        index=0
        for c in args[0]:
            if index<len(value)and c==value[index]:index+=1
        if index!=len(value):return False
        balance=0
        for c in value:
            if c in'()':balance+=1 if c=='('else-1
            if balance<0:return False
        return balance==0
    if pid==1253:
        if not want:return exact(value,[])
        return type(value)is list and len(value)==2 and all(type(row)is list and len(row)==len(args[2])and all(type(v)is int and v in(0,1)for v in row)for row in value)and sum(value[0])==args[0]and sum(value[1])==args[1]and all(l+r==c for l,r,c in zip(value[0],value[1],args[2]))
    return exact(value,want)


def compare(pid,args,want,record,language):
    if 'error'in record:return False,'candidate_error'
    kind=list if pid in (1238,1253)else str if pid==1249 else type(want)
    types={'python':{list:'list',int:'int',bool:'bool',str:'str',float:'float'},'javascript':{list:'object',int:'number',bool:'boolean',str:'string',float:'number'}}
    if pid==1227:
        allowed=('float','int')if language=='python'else('number',)
        if record.get('result_type')not in allowed:return False,'result_type'
    elif record.get('result_type')!=types[language][kind]:return False,'result_type'
    if not matches(pid,args,record.get('result'),want):return False,'result_value'
    if not exact(record.get('args_before'),args)or not exact(record.get('args_after'),args):return False,'input_effects'
    if record.get('alias_edges')!=[]:return False,'mutable_alias'
    return True,None
