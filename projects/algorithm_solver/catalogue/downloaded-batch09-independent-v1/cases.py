"""Independent definition-derived small cases and analytic legal boundary fixtures."""
import ast,html,json,re,random,datetime
from pathlib import Path
from itertools import product,combinations
import oracles as o
ROOT=Path(__file__).resolve().parents[4]
IMPORT=ROOT/'projects/algorithm_solver/catalogue/authored/downloaded-general40-v1'
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

def build(statements=None):
 rng=random.Random(2026102809);data={i:[]for i in IDS};seen={i:set()for i in IDS};unset=object()
 def add(pid,args,category='independent-seeded-small',want=unset):
  key=json.dumps(args,separators=(',',':'))
  if key in seen[pid]:return
  seen[pid].add(key);data[pid].append({'args':args,'expected':o.expected(pid,args)if want is unset else want,'category':category})
 if statements:
  for pid in IDS:
   for args,value in official(Path(statements)/f'{pid}.json',pid):
    want=o.expected(pid,args);assert o.matches(pid,args,value,want),(pid,args,value,want);add(pid,args,'official-example')
 for n in range(1,7):
  for xs in product((0,1),repeat=n):add(1151,[list(xs)],'exhaustive-short-binary')
  for xs in product((-1,0,1),repeat=n):add(1186,[list(xs)],'exhaustive-short-subarrays')
 for n in range(1,4):
  for k in range(1,7):
   for target in range(1,n*k+3):add(1155,[n,k,target],'small-dice-compositions')
 for s in product('QWER',repeat=4):add(1234,[''.join(s)],'complete-length-four-domain')
 for n in range(1,9):add(1227,[n],'exact-seat-outcomes')
 for n in range(1,1001):add(1281,[n],'short-decimal-domain')
 for n in range(1,5):
  for start in range(1<<n):add(1238,[n,start],'complete-small-cycle-starts')
 for _ in range(70):
  s=''.join(rng.choices('abc',k=rng.randint(1,8)))
  add(1156,[s]);add(1163,[s]);n=rng.randint(1,4);add(1162,[[[rng.randrange(2)for _ in range(n)]for _ in range(n)]])
  add(1167,[[rng.randint(1,20)for _ in range(rng.randint(1,6))]])
  tx=[f'{rng.choice(["alice","bob"])},{rng.randrange(121)},{rng.choice([1,1000,1001,2000])},{rng.choice(["rome","oslo"])}'for _ in range(rng.randint(1,8))];add(1169,[tx])
  qs=[]
  for _ in range(rng.randint(1,6)):
   l=rng.randrange(len(s));r=rng.randint(l,len(s)-1);qs.append([l,r,rng.randrange(5)])
  add(1177,[s,qs]);words=[''.join(rng.choices('abcdefghi',k=rng.randint(4,9)))for _ in range(rng.randint(1,8))];puzzles=[''.join(rng.sample('abcdefghi',7))for _ in range(rng.randint(1,5))];add(1178,[words,puzzles])
  colors=[rng.randint(1,3)for _ in range(rng.randint(1,10))];add(1182,[colors,[[rng.randrange(len(colors)),rng.randint(1,3)]for _ in range(rng.randint(1,6))]])
  w,h=rng.randint(1,3),rng.randint(1,3);side=rng.randint(1,min(w,h));add(1183,[w,h,side,rng.randrange(side*side+1)])
  date=datetime.date(1971,1,1)+datetime.timedelta(days=rng.randrange((datetime.date(2100,12,31)-datetime.date(1971,1,1)).days+1));add(1185,[date.day,date.month,date.year])
  add(1189,[''.join(rng.choices('balloonxyz',k=rng.randint(1,60)))])
  a,b,c=[''.join(rng.choices('abc',k=rng.randrange(4)))for _ in range(3)];add(1190,[a+'('+b+'('+c+'))'])
  add(1196,[[rng.randint(1,1000)for _ in range(rng.randint(1,8))]])
  add(1197,[rng.randint(-10,10),rng.randint(-10,10)])
  width=rng.randint(1,6);add(1198,[[sorted(rng.sample(range(1,21),width))for _ in range(rng.randint(1,4))]])
  add(1201,[rng.randint(1,40),rng.randint(1,10),rng.randint(1,10),rng.randint(1,10)])
  small=s[:6];pairs=[list(p)for p in combinations(range(len(small)),2)if rng.randrange(4)==0];add(1202,[small,pairs])
  add(1209,[s,rng.randint(2,5)]);add(1218,[[rng.randint(-5,5)for _ in range(rng.randint(1,9))],rng.randint(-3,3)])
  r,c=rng.randint(1,3),rng.randint(1,3);add(1219,[[[rng.randrange(5)for _ in range(c)]for _ in range(r)]])
  positions=rng.sample([(r,c)for r in range(8)for c in range(8)],rng.randint(2,20));add(1222,[[list(p)for p in positions[1:]],list(positions[0])])
  size=rng.randint(3,9);start=rng.randint(-10,10);step=rng.randint(-5,5);seq=[start+i*step for i in range(size)];del seq[rng.randint(1,size-2)];add(1228,[seq])
  add(1234,[''.join(rng.choices('QWER',k=rng.choice([4,8,12])))])
  add(1243,[[rng.randint(1,20)for _ in range(rng.randint(1,8))]])
  par=''.join(rng.choices('ab()',k=rng.randint(1,10)));add(1249,[par])
  col=[rng.randrange(3)for _ in range(rng.randint(1,7))];add(1253,[rng.randrange(len(col)+1),rng.randrange(len(col)+1),col])
  r,c=rng.randint(1,4),rng.randint(1,4);add(1254,[[[rng.randrange(2)for _ in range(c)]for _ in range(r)]])
  words=[''.join(rng.choices('abc',k=rng.randint(1,5)))for _ in range(rng.randint(1,7))];letters=rng.choices('abc',k=rng.randint(1,15));score=[rng.randrange(11)for _ in range(26)];add(1255,[words,letters,score])
  add(1262,[[rng.randint(1,20)for _ in range(rng.randint(1,10))]])
  products=sorted(set(''.join(rng.choices('abc',k=rng.randint(1,6)))for _ in range(rng.randint(1,10))));add(1268,[products,s[:5]])
  add(1271,[str(rng.randint(1,1000000))])
  starts=sorted(rng.sample(range(-10,11),rng.randint(1,7)));intervals=[[i,i+1]for i in starts];a=rng.randint(-12,10);add(1272,[intervals,[a,rng.randint(a+1,13)]])
  low=rng.randint(10,100000);add(1291,[low,rng.randint(low,10**9)])
  r,c=rng.randint(1,4),rng.randint(1,4);add(1292,[[[rng.randrange(10)for _ in range(c)]for _ in range(r)],rng.randrange(101)])
 for num in ['1','16','257','3','1000000000000','68719476736']:add(1271,[num],'canonical-decimal-string-interface')
 for year in (1971,2000,2100):
  for month,day in [(1,1),(2,28),(3,1),(12,31)]:add(1185,[day,month,year],'Gregorian-century-boundaries')
 add(1185,[29,2,2000],'Gregorian-leap-century')
 add(1169,[['alice,0,1000,rome','alice,60,1000,oslo','alice,61,1000,rome','alice,0,1000,rome']],'time-boundary-and-multiplicity')
 add(1155,[30,30,500],'maximum-dice-boundary')
 add(1156,['a'*20000],'maximum-uniform-text',20000)
 grid=[[0]*100 for _ in range(100)];grid[0][0]=1;add(1162,[grid],'maximum-corner-land',198)
 add(1163,['a'*400000],'maximum-equal-suffixes','a'*400000)
 add(1167,[[1]*10000],'maximum-unit-sticks',133616)
 add(1177,['a'*100000,[[0,99999,50000]]],'maximum-prefix-text',[True])
 add(1178,[['aaaa']*100000,['abcdefg']*10000],'maximum-word-puzzle-populations',[100000]*10000)
 add(1182,[[1]*50000,[[0,2]]],'maximum-color-array',[-1])
 add(1183,[100,100,100,10000],'maximum-full-grid',10000)
 add(1186,[[-1]*100000],'maximum-negative-array',-1)
 add(1189,['balloon'*1000],'maximum-balloon-count',1000)
 add(1190,['('*1000+')'*1000],'maximum-parenthesis-depth','')
 add(1196,[[1]*1000],'maximum-apple-count',1000)
 add(1197,[300,0],'maximum-coordinate-distance',150)
 add(1198,[[list(range(1,501))for _ in range(500)]],'maximum-matrix-population',1)
 add(1201,[10**9,2,2,2],'maximum-nth-answer',2*10**9)
 add(1201,[10**9,1,10**9,10**9],'maximum-LCM-numeric-boundary',10**9)
 add(1202,['a'*100000,[]],'maximum-string-singletons','a'*100000)
 add(1209,['a'*100000,10000],'maximum-cascade-input','')
 add(1218,[[7]*100000,0],'maximum-zero-difference',100000)
 add(1219,[[[1]*5 for _ in range(5)]],'maximum-positive-cell-count',25)
 add(1227,[100000],'maximum-seat-population',0.5)
 add(1234,['Q'*100000],'maximum-unbalanced-text',75000)
 add(1238,[16,65535],'maximum-cycle-population',None)
 add(1249,['('*100000],'maximum-unmatched-parentheses',100000)
 add(1253,[100000,100000,[2]*100000],'maximum-column-population',True)
 add(1254,[[[0]*100 for _ in range(100)]],'maximum-boundary-connected-component',0)
 grid=[[1]*100]+[[1]+[0]*98+[1]for _ in range(98)]+[[1]*100];add(1254,[grid],'maximum-closed-component',1)
 add(1255,[['a'*i for i in range(1,15)],['a']*100,[1]+[0]*25],'maximum-word-count',100)
 add(1262,[[9999]*40000],'maximum-sum-population',399960000)
 add(1272,[[[2*i,2*i+1]for i in range(10000)],[0,20000]],'maximum-interval-population',[])
 add(1281,[100000],'maximum-decimal-value',-1)
 add(1291,[10,10**9],'maximum-sequential-range')
 add(1292,[[[0]*300 for _ in range(300)],0],'maximum-square-grid',300)
 for pid in IDS:assert data[pid],pid
 return data
