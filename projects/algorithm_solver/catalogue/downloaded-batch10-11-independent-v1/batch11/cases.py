"""Independent definition-derived small cases and analytic legal boundary fixtures."""
import ast,html,json,re,random,datetime
from pathlib import Path
from itertools import product,combinations,permutations
import oracles as o
ROOT=Path(__file__).resolve().parents[5]
IMPORT=ROOT/'projects/algorithm_solver/catalogue/authored/downloaded-general31-v1'
ROWS=json.loads((IMPORT/'assignment.public-safe.json').read_text())['problems']
IDS=tuple(r['id']for r in ROWS)

def official(path,pid):
 q=json.loads(path.read_bytes())['data']['question'];assert q and q['questionFrontendId']==str(pid)
 if not q['content']:return []
 body=html.unescape(re.sub('<[^>]+>',' ',q['content'])).replace('\u200b','').replace('\ufeff','');result=[]
 for match in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*\d+:|Constraints:|$)',body,re.S):
  node=ast.parse('f('+match[1].strip()+')',mode='eval').body
  assert isinstance(node,ast.Call)and not node.args and node.keywords
  args=[ast.literal_eval(k.value)for k in node.keywords];value,_=json.JSONDecoder().raw_decode(match[2].strip());result.append((args,value))
 assert result,pid
 return result

def debruijn(k):
 a=[0]*(2*k);out=[]
 def visit(t,p):
  if t>k:
   if k%p==0:out.extend(a[1:p+1])
  else:
   a[t]=a[t-p];visit(t+1,p)
   for j in range(a[t-p]+1,2):a[t]=j;visit(t+1,t)
 visit(1,1);s=''.join(map(str,out));return s+s[:k-1]
def build(statements=None):
 rng=random.Random(2026102811);data={i:[]for i in IDS};seen={i:set()for i in IDS};unset=object()
 def add(pid,args,category='independent-seeded-small',want=unset):
  key=json.dumps(args,separators=(',',':'))
  if key in seen[pid]:return
  seen[pid].add(key);data[pid].append({'args':args,'expected':o.expected(pid,args)if want is unset else want,'category':category})
 if statements:
  for pid in IDS:
   for args,value in official(Path(statements)/f'{pid}.json',pid):
    want=o.expected(pid,args);assert o.matches(pid,args,value,want),(pid,args,value,want);add(pid,args,'official-example')
 for n in range(1,9):
  for bits in product('01',repeat=n):
   s=''.join(bits);add(1493,[[int(c)for c in s]],'complete-short-delete-domain');add(1529,[s],'complete-short-suffix-flips')
   if n<=6:
    for k in range(1,5):add(1461,[s,k],'short-binary-code-coverage')
 for n in range(1,7):
  for k in range(1,(1<<n)):add(1545,[n,k],'complete-short-recursive-bit-rows')
 for n in range(1,61):
  for k in range(1,n+1):add(1492,[n,k],'complete-short-factor-domain')
 for n in range(1,101):
  for exchange in (2,3,10,100):add(1518,[n,exchange],'bottle-arithmetic-domain')
 for _ in range(75):
  x=[rng.randint(-5,5)for _ in range(rng.randint(1,6))];y=[rng.randint(-5,5)for _ in range(rng.randint(1,6))];add(1458,[x,y])
  arr=[rng.randint(1,6)for _ in range(rng.randint(1,8))];other=arr[:];rng.shuffle(other)
  if rng.randrange(2):other[0]=rng.randint(1,6)
  add(1460,[arr,other]);balls=[rng.randint(1,4)for _ in range(rng.randint(1,5))]
  if sum(balls)%2:balls[0]+=1
  add(1467,[balls]);add(1475,[[rng.randint(1,20)for _ in range(rng.randint(1,9))]])
  add(1477,[[rng.randint(1,8)for _ in range(rng.randint(1,10))],rng.randint(1,20)])
  add(1487,[[rng.choice(['a','a(1)','a(2)','b','b(1)','(1)','a(1)(1)'])for _ in range(rng.randint(1,14))]])
  add(1488,[[rng.randrange(4)for _ in range(rng.randint(1,11))]])
  add(1498,[[rng.randint(1,10)for _ in range(rng.randint(1,9))],rng.randint(1,20)])
  date=datetime.date(1900,1,1)+datetime.timedelta(days=rng.randrange(73414));day=date.day;suffix='th'if day%100 in (11,12,13)else{1:'st',2:'nd',3:'rd'}.get(day%10,'th');add(1507,[str(day)+suffix+' '+['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][date.month-1]+' '+str(date.year)])
  arr=[rng.randint(1,100)for _ in range(rng.randint(1,8))];n=len(arr);left=rng.randint(1,n*(n+1)//2);right=rng.randint(left,n*(n+1)//2);add(1508,[arr,n,left,right])
  add(1512,[[rng.randint(1,8)for _ in range(rng.randint(1,12))]])
  n=rng.randint(2,7);edges=[list(pair)for pair in combinations(range(n),2)if rng.randrange(3)==0];probs=[rng.choice([0.0,0.01,0.1,0.25,0.5,0.9,1.0])for _ in edges];start,end=rng.sample(range(n),2);add(1514,[n,edges,probs,start,end])
  s=''.join(rng.choices('abc',k=rng.randint(1,10)));add(1525,[s]);add(1526,[[rng.randint(1,5)for _ in range(rng.randint(1,8))]])
  add(1546,[[rng.randint(-4,4)for _ in range(rng.randint(1,10))],rng.randint(0,10)])
  position=rng.sample(range(1,25),rng.randint(2,8));add(1552,[position,rng.randint(2,len(position))]);add(1558,[[rng.randrange(32)for _ in range(rng.randint(1,6))]])
  add(1561,[[rng.randint(1,20)for _ in range(rng.choice([3,6]))]])
  add(1566,[[rng.randint(1,4)for _ in range(rng.randint(2,12))],rng.randint(1,6),rng.randint(2,6)])
  add(1574,[[rng.randrange(10)for _ in range(rng.randint(1,9))]])
  valid=[]
  for _ in range(rng.randint(1,10)):valid.append(rng.choice([c for c in 'abc'if not valid or c!=valid[-1]]))
  masked=''.join(c if rng.randrange(2)else'?'for c in valid);add(1576,[masked])
  add(1578,[s,[rng.randint(1,20)for _ in s]])
  words=[''.join(rng.choices('abc',k=rng.randint(1,5)))for _ in range(rng.randint(1,5))];text=' '*rng.randrange(4)+''.join(w+' '*rng.randint(1,4)for w in words);add(1592,[text])
  r,c=rng.randint(1,4),rng.randint(1,4);add(1594,[[[rng.randint(-4,4)for _ in range(c)]for _ in range(r)]])
  add(1599,[[rng.randint(0,12)for _ in range(rng.randint(1,8))],rng.randint(1,10),rng.randint(1,20)])
 add(1458,[[1000]*500,[1000]*500],'maximum-dot-product',500000000)
 add(1460,[[1]*1000,[1]*1000],'maximum-array-equality',True)
 add(1461,['0'*500000,20],'maximum-negative-code-coverage',False)
 add(1461,[debruijn(18),18],'maximum-positive-code-coverage',True)
 add(1467,[[6]*8],'maximum-balls-multiplicity')
 add(1475,[[1000]*500],'maximum-discount-prices',[0]*499+[1000])
 add(1477,[[1]*100000,1],'maximum-positive-window-pair',2)
 add(1477,[[1]*100000,100000000],'maximum-absent-window-pair',-1)
 add(1487,[['a']*50000],'maximum-duplicate-names',['a']+[f'a({i})'for i in range(1,50000)])
 add(1488,[[0]*50000+[1,0]*25000],'maximum-unusable-earlier-dry-days',True)
 add(1493,[[1]*100000],'maximum-delete-one-required',99999)
 add(1498,[[1]*100000,2],'maximum-subsequence-population',(pow(2,100000,1000000007)-1)%1000000007)
 add(1508,[[100]*1000,1000,1,500500],'maximum-subarray-sum-total',(100*1000*1001*1002//6)%1000000007)
 add(1512,[[100]*100],'maximum-good-pairs',4950)
 add(1514,[10000,[[i,i+1]for i in range(9999)],[1.0]*9999,0,9999],'maximum-unit-probability-chain',1.0)
 add(1525,['a'*100000],'maximum-split-count',99999)
 add(1526,[[1,40000]*50000],'maximum-legal-32-bit-operation-total',1+50000*39999)
 add(1529,['10'*50000],'maximum-suffix-flip-count',100000)
 for k in [1,1<<19,(1<<20)-1]:add(1545,[20,k],'maximum-recursive-bit-string')
 add(1546,[[0]*100000,0],'maximum-disjoint-zero-windows',100000)
 add(1552,[list(range(1,1000000000,10000)),100000],'maximum-ball-placement-population',10000)
 add(1558,[[1000000000]*100000],'maximum-bit-operation-count',100000*(1000000000).bit_count()+29)
 add(1561,[[10000]*99999],'maximum-pile-population',333330000)
 add(1566,[[1]*100,1,100],'maximum-repeated-pattern',True)
 add(1574,[list(range(99999,-1,-1))],'maximum-descending-removal',99999)
 add(1576,['?'*100],'maximum-question-replacements',None)
 add(1578,['a'*100000,[10000]*100000],'maximum-deletion-time',999990000)
 add(1578,['aaa',[9,2,1]],'descending-cost-mutation-control')
 add(1592,['a'+' '*99],'maximum-space-surplus','a'+' '*99)
 for value in [4,3,-4]:add(1594,[[[value]*15 for _ in range(15)]],'maximum-product-grid-'+str(value),-1 if value<0 else pow(value,29,1000000007))
 grid=[[4]*15 for _ in range(15)];grid[0][0]=3;add(1594,[grid],'maximum-mixed-significant-product',(3*4**28)%1000000007)
 add(1599,[[50]*100000,100,1],'maximum-wheel-backlog',1250000)
 for pid in IDS:assert data[pid],pid
 return data
