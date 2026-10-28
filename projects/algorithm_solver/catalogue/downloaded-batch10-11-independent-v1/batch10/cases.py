"""Independent definition-derived small cases and analytic legal boundary fixtures."""
import ast,html,json,re,random,datetime
from pathlib import Path
from itertools import product,combinations,permutations
import oracles as o
ROOT=Path(__file__).resolve().parents[5]
IMPORT=ROOT/'projects/algorithm_solver/catalogue/authored/downloaded-general16-v1'
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
 rng=random.Random(2026102810);data={i:[]for i in IDS};seen={i:set()for i in IDS};unset=object()
 def add(pid,args,category='independent-seeded-small',want=unset):
  key=json.dumps(args,separators=(',',':'))
  if key in seen[pid]:return
  seen[pid].add(key);data[pid].append({'args':args,'expected':o.expected(pid,args)if want is unset else want,'category':category})
 if statements:
  for pid in IDS:
   for args,value in official(Path(statements)/f'{pid}.json',pid):
    want=o.expected(pid,args);assert o.matches(pid,args,value,want),(pid,args,value,want);add(pid,args,'official-example')
 for hour in range(1,13):
  for minutes in range(60):add(1344,[hour,minutes],'complete-clock-domain')
 for n in range(1,7):
  for xs in permutations(range(1,n+1)):add(1375,[list(xs)],'complete-short-permutations')
  for xs in product('ab',repeat=n):add(1332,[''.join(xs)],'exhaustive-binary-subsequence-domain')
 for mask in range(1,1024):add(1386,[1,[[1,j+1]for j in range(10)if mask>>j&1]],'complete-single-row-reservations')
 for _ in range(80):
  n=rng.randint(2,7);friends=[[]for _ in range(n)]
  for i,j in combinations(range(n),2):
   if rng.randrange(3)==0:friends[i].append(j);friends[j].append(i)
  watched=[[rng.choice(['A','B','AA','a','Film'])for _ in range(rng.randint(1,5))]for _ in range(n)];add(1311,[watched,friends,rng.randrange(n),rng.randint(1,n-1)])
  r,c=rng.randint(1,4),rng.randint(1,4);mat=[[rng.randint(1,100)for _ in range(c)]for _ in range(r)];add(1314,[mat,rng.randint(1,6)]);add(1329,[mat])
  half=''.join(rng.choices('abcxyz',k=rng.randrange(5)));s=half+(''if rng.randrange(2)else rng.choice('abc'))+half[::-1]
  if not s:s='a'
  add(1328,[s]);add(1394,[[rng.randint(1,8)for _ in range(rng.randint(1,12))]])
  add(1402,[[rng.randint(-10,10)for _ in range(rng.randint(1,6))]])
  atoms=['&quot;','&apos;','&amp;','&gt;','&lt;','&frasl;','&amp;lt;','&amp;amp;','&&lt;','&bogus;','hello','\x00','\xff'];add(1410,[''.join(rng.choices(atoms,k=rng.randint(1,10)))])
  orders=[[rng.choice(['Alice','Bob Smith']),str(rng.choice([1,2,10,500])),rng.choice(['Tea','AA','A','a','Hot Dog'])]for _ in range(rng.randint(1,12))];add(1418,[orders])
  add(1419,[''.join(rng.choices('croak',k=rng.randint(1,12)))])
  s=''.join(rng.choices('abc',k=rng.randint(1,6)));add(1427,[s,[[rng.randrange(2),rng.randint(0,20)]for _ in range(rng.randint(1,8))]])
  add(1433,[s,''.join(rng.choices('abc',k=len(s)))]);add(1442,[[rng.randint(1,7)for _ in range(rng.randint(1,9))]])
 for s in ['croak','croakcroak','crcoakroak','ccrrooaakk','croakc','croakcrook','crcroakoak']:add(1419,[s],'valid-and-incomplete-frog-assignments')
 add(1311,[[['A']*100 for _ in range(100)],[list(range(1,100))]+[[0]for _ in range(99)],0,1],'maximum-watched-population',['A'])
 add(1314,[[[100]*100 for _ in range(100)],100],'maximum-block-sum',[[1000000]*100 for _ in range(100)])
 add(1328,['a'*1000],'maximum-palindrome','a'*999+'b')
 add(1329,[[[100]*100 for _ in range(100)]],'maximum-diagonal-grid',[[100]*100 for _ in range(100)])
 add(1332,['ab'*500],'maximum-binary-nonpalindrome',2)
 add(1375,[list(range(1,50001))],'maximum-aligned-population',50000)
 add(1386,[10**9,[[1,1]]],'maximum-row-count',2*10**9)
 add(1394,[[500]*500],'maximum-lucky-frequency',500)
 add(1402,[[1000]*500],'maximum-satisfaction-total',125250000)
 add(1410,['&amp;'*20000],'maximum-entity-stream','&'*20000)
 add(1410,[''.join(chr(i)for i in range(256))],'all-byte-values-single-pass')
 add(1418,[[['Alice','500','Food']]*50000],'maximum-order-count',[['Table','Food'],['500','50000']])
 add(1419,['croak'*20000],'maximum-sequential-croaks',1)
 add(1419,['c'*20000+'r'*20000+'o'*20000+'a'*20000+'k'*20000],'maximum-concurrent-croaks',20000)
 add(1433,['a'*100000,'z'*100000],'maximum-break-strings',True)
 add(1442,[[100000000]*300],'maximum-triplet-count',sum((301-length)*(length-1)for length in range(2,301,2)))
 return data
