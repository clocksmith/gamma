"""Fresh definition-derived finite cases, not delivered assertions."""
import ast,html,json,random,re
from pathlib import Path
from itertools import product,combinations
import oracles as o

def official_examples(path):
 q=json.loads(Path(path).read_bytes())['data']['question']
 body=re.sub(r'</?(?:p|pre|div|li|ul|ol|br)[^>]*>','\n',q['content']);body=html.unescape(re.sub(r'<[^>]*>','',body));examples=[]
 for m in re.finditer(r'Input:\s*(.*?)\s*Output:\s*(.*?)(?=Explanation:|Example\s*[0-9]+:|Constraints:|Follow up:|$)',body,re.S):
  node=ast.parse('f('+m[1].strip()+')',mode='eval').body
  assert isinstance(node,ast.Call)and not node.args and node.keywords
  args=[ast.literal_eval(k.value)for k in node.keywords];declared,_=json.JSONDecoder().raw_decode(m[2].strip());examples.append((args,declared))
 assert examples,q['questionFrontendId']
 return examples


def build(statements):
 rng=random.Random(2026102808);result={pid:[]for pid in o.FUNCTIONAL};seen={pid:set()for pid in o.FUNCTIONAL}
 def add(pid,args,category):
  o.validate(pid,args);key=json.dumps(args,separators=(',',':'))
  if key in seen[pid]:return
  want=o.expected(pid,args);result[pid].append({'args':args,'expected':want,'category':category});seen[pid].add(key)
 for pid in o.FUNCTIONAL:
  for args,declared in official_examples(Path(statements)/f'{pid}.json'):
   want=o.expected(pid,args);assert o.matches(pid,args,declared,want),(pid,args,declared,want)
   add(pid,args,'official-example-reference-crosscheck')
 def words(n,alphabet='abc',length=None):return[''.join(rng.choices(alphabet,k=length or rng.randint(1,8)))for _ in range(n)]
 for n in range(1,7):
  for v in product('abc',repeat=n):add(1003,[''.join(v)],'all-abc-strings-through-length-six')
 for n in range(1,7):
  for v in product((0,1),repeat=n):
   for k in(0,n//2,n):add(1004,[list(v),k],'exhaustive-small-binary-and-flip-strata')
 for n in range(1,101):add(1006,[n],'first100-clumsy-expression-groupings')
 for k in range(1,151):add(1015,[k],'small-repunit-multiplicative-orders')
 for n in range(151):add(1017,[n],'negative-radix-small-nonnegative-integers')
 for n in range(1,7):
  def visit(s,a,b):
   if a==b==n:yield s
   if a<n:yield from visit(s+'(',a+1,b)
   if b<a:yield from visit(s+')',a,b+1)
  for s in visit('',0,0):add(1111,[s],'all-balanced-up-to-six-pairs')
 for _ in range(40):
  n=rng.randint(1,10);add(1002,[words(n)],'character-multiplicity-intersection')
  add(1003,[''.join(rng.choices('abc',k=rng.randint(7,35)))],'rewrite-fixed-point-reference')
  n=rng.randint(2,8);add(1007,[[rng.randint(1,6)for _ in range(n)],[rng.randint(1,6)for _ in range(n)]],'exhaustive-rotation-subsets')
  add(1010,[[rng.randint(1,500)for _ in range(rng.randint(1,15))]],'all-song-index-pairs')
  n=rng.randint(1,10);add(1011,[[rng.randint(1,30)for _ in range(n)],rng.randint(1,n)],'minimax-contiguous-partitions')
  add(1013,[[rng.randint(-5,5)for _ in range(rng.randint(3,12))]],'all-two-cut-partitions')
  add(1014,[[rng.randint(1,1000)for _ in range(rng.randint(2,15))]],'all-sightseeing-pairs')
  s=''.join(rng.choices('01',k=rng.randint(1,50)));add(1016,[s,rng.randint(1,100)],'represented-substring-set')
  m,n=rng.randint(1,7),rng.randint(1,7);add(1020,[[[rng.randrange(2)for _ in range(n)]for _ in range(m)]],'outside-node-disjoint-set-components')
  add(1023,[words(rng.randint(1,8),'abcABC'),words(1,'abcABC')[0]],'regular-language-insertion-definition')
  clips=[sorted([rng.randint(0,12),rng.randint(0,12)])for _ in range(rng.randint(1,12))];add(1024,[clips,rng.randint(1,12)],'shortest-coverage-path')
  add(1027,[[rng.randint(0,8)for _ in range(rng.randint(2,10))]],'enumerated-arithmetic-subsequences')
  add(1029,[[[rng.randint(1,1000),rng.randint(1,1000)]for _ in range(2*rng.randint(1,5))]],'all-balanced-city-assignments')
  m,n=rng.randint(1,8),rng.randint(1,8);add(1030,[m,n,rng.randrange(m),rng.randrange(n)],'all-cells-distance-order-predicate')
  n=rng.randint(2,15);a=rng.randint(1,n-1);b=rng.randint(1,n-a);add(1031,[[rng.randint(0,1000)for _ in range(n)],a,b],'all-disjoint-window-pairs')
  add(1033,rng.sample(range(1,12),3),'endpoint-move-state-graph')
  m,n=rng.randint(1,6),rng.randint(1,6);add(1034,[[[rng.randint(1,3)for _ in range(n)]for _ in range(m)],rng.randrange(m),rng.randrange(n),rng.randint(1,4)],'component-membership-border-predicate')
  add(1035,[[rng.randint(1,6)for _ in range(rng.randint(1,10))],[rng.randint(1,6)for _ in range(rng.randint(1,10))]],'all-subsequences-and-embedding')
  add(1037,[[[rng.randint(0,100),rng.randint(0,100)]for _ in range(3)]],'shoelace-area')
  add(1041,[''.join(rng.choices('GLR',k=rng.randint(1,100)))],'literal-four-cycle-execution')
  n=rng.randint(1,12);edges=[];degree=[0]*n
  for a,b in rng.sample(list(combinations(range(n),2)),n*(n-1)//2):
   if rng.randrange(2)and degree[a]<3 and degree[b]<3:edges.append([a+1,b+1]);degree[a]+=1;degree[b]+=1
  add(1042,[n,edges],'full-legal-coloring-predicate')
  n=rng.randint(1,12);add(1043,[[rng.randint(0,100)for _ in range(n)],rng.randint(1,n)],'all-contiguous-partitions')
  add(1048,[words(rng.randint(1,15))],'insertion-subsequence-DAG')
  add(1049,[[rng.randint(1,100)for _ in range(rng.randint(1,12))]],'meet-in-middle-signed-partitions')
  n=rng.randint(1,15);add(1052,[[rng.randint(0,1000)for _ in range(n)],[rng.randrange(2)for _ in range(n)],rng.randint(1,n)],'all-bookstore-windows')
  add(1053,[[rng.randint(1,5)for _ in range(rng.randint(1,10))]],'all-at-most-one-transpositions')
  n=rng.randint(1,20);add(1061,[words(1,'abcdef',n)[0],words(1,'abcdef',n)[0],words(1,'abcdef',rng.randint(1,25))[0]],'equivalence-graph-reachability')
  m,n=rng.randint(1,8),rng.randint(1,7);add(1072,[[[rng.randrange(2)for _ in range(n)]for _ in range(m)]],'all-column-flip-subsets')
  arrays=[]
  for _ in range(2):
   n=rng.randint(1,35);arrays.append([rng.randrange(2)]if n==1 else[1]+[rng.randrange(2)for _ in range(n-1)])
  add(1073,arrays,'exact-integer-negative-radix-sum')
  m,n=rng.randint(1,4),rng.randint(1,4);add(1074,[[[rng.randint(-3,3)for _ in range(n)]for _ in range(m)],rng.randint(-8,8)],'all-canonical-ID1074-rectangles')
  add(1079,[words(1,'ABCD',rng.randint(1,7))[0]],'multiset-composition-multinomial-counts')
  add(1081,[words(1,'abcdef',rng.randint(1,25))[0]],'lexicographic-feasible-prefix-choice')
  add(1089,[[rng.randint(0,3)for _ in range(rng.randint(1,30))]],'explicit-pure-transform-not-native-mutation')
  n=rng.randint(1,12);add(1090,[[rng.randint(0,30)for _ in range(n)],[rng.randint(0,4)for _ in range(n)],rng.randint(1,n),rng.randint(1,n)],'all-labelled-subsets')
  n=rng.randint(1,7);add(1091,[[[rng.randrange(2)for _ in range(n)]for _ in range(n)]],'independent-grid-Dijkstra')
  count=[0]*256
  for i in rng.sample(range(256),rng.randint(1,15)):count[i]=rng.randint(1,30)
  count[rng.randrange(256)]=max(count)+1;add(1093,[count],'exact-rational-weighted-sample-statistics')
  trips=[]
  for _ in range(rng.randint(1,15)):
   a=rng.randint(0,20);b=rng.randint(a+1,25);trips.append([rng.randint(1,100),a,b])
  add(1094,[trips,rng.randint(1,500)],'per-segment-passenger-occupancy')
  add(1104,[rng.randint(1,10**6)],'heap-index-prefix-path')
  width=rng.randint(1,12);add(1105,[[[rng.randint(1,width),rng.randint(1,1000)]for _ in range(rng.randint(1,12))],width],'all-legal-shelf-cuts')
  n=rng.randint(1,20);bookings=[]
  for _ in range(rng.randint(1,15)):
   a=rng.randint(1,n);bookings.append([a,rng.randint(a,n),rng.randint(1,10000)])
  add(1109,[bookings,n],'per-flight-direct-booking-sums')
 # Exact public-boundary and adversarial families, independent analytic expectations.
 boundary={1002:[[['a'*100]*100]],1003:[['abc'*6666],['a'*20000]],1004:[[[1]*100000,0],[[0]*100000,100000],[[0]*100000,49999]],1006:[[10000]],1007:[[[1]*20000,[2]*20000],[[1,2]*10000,[2,1]*10000]],1010:[[[60]*60000],[[1]*60000]],1011:[[[500]*50000,1],[[500]*50000,100],[[500]*50000,50000]],1013:[[[0]*50000],[[1]*49998]],1014:[[[1000]*50000],[[1]*50000]],1015:[[99991],[100000],[99999]],1016:[['1'*1000,10**9],[''.join(bin(i)[2:]for i in range(1,101)),100]],1017:[[10**9],[2**29-1],[2**29]],1020:[[[[1]*500 for _ in range(500)]],[[[0]*500 for _ in range(500)]]],1023:[[['A'*100,'a'*100],'A'*100]],1024:[[[[i,i+1]for i in range(100)],100]],1027:[[[7]*1500]],1029:[[[[1000,1]]*100]],1030:[[100,100,0,0],[100,100,50,50]],1031:[[[1000]*1000,499,500],[[0]*1000,1,1]],1033:[[1,2,100],[1,50,100]],1034:[[[[1]*50 for _ in range(50)],25,25,1000]],1035:[[[1]*500,[1]*500],[[1]*500,[2]*500]],1037:[[[[0,0],[100,100],[0,100]]]],1041:[['G'*100],['L'*100]],1042:[[10000,[[i,i+1]for i in range(1,10000)]]],1043:[[[4000000]*500,500],[[10**9],1]],1048:[[['aconstructor']],[['bconstructor','aconstructor']],[['constructor','aconstructor']],[['a'*i for i in range(1,17)]*62]],1049:[[[100]*30],[[1]*29+[100]]],1052:[[[1000]*20000,[1]*20000,10000],[[1000]*20000,[0]*20000,1]],1053:[[list(range(1,10001))],[list(range(10000,0,-1))]],1061:[['a'*1000,'z'*1000,'z'*1000]],1072:[[[[0]*300 for _ in range(300)]]],1073:[[[1]*1000,[1]*1000],[[1]+[0]*999,[1]*1000]],1074:[[[[0]*100 for _ in range(100)],0],[[[1]*100 for _ in range(100)],100],[[[1000]],10**8]],1079:[['ABCDEFG'],['AAAAAAA']],1081:[['abcdefghijklmnopqrstuvwxyz'*38],['zyxwvutsrqponmlkjihgfedcba'*38]],1089:[[[0]*10000],[list(range(10))*1000]],1090:[[[20000]*20000,[1]*20000,20000,10000],[[20000]*20000,list(range(20000)),20000,1]],1091:[[[[0]*100 for _ in range(100)]]],1093:[[[10**9]+[0]*255],[[0]*255+[10**9]],[[499999999,500000001]+[0]*254]],1094:[[[[100,0,1000]]*1000,100000],[[[100,0,1000]]*1000,99999]],1104:[[1],[10**6]],1105:[[[[1,1000]]*1000,1000],[[[1,1]]*1000,1]],1109:[[[[1,20000,10000]]*20000,20000]],1111:[['('*5000+')'*5000],['()'*5000]]}
 for pid,rows in boundary.items():
  for args in rows:add(pid,args,'legal-maximum-adversarial-or-analytic-family')
 return result
