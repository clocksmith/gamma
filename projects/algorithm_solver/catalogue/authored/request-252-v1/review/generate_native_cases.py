"""Independently generated bounded native design-class oracle cases."""
import json,random,pathlib,sys
R=random.Random(25220261027); out=[]
def add(pid,constructor,steps): out.append(dict(problem_id=pid,constructor=constructor,steps=steps))
# All queries of independently shuffled grids; coordinate oracle, not a lookup table.
for n in range(3,11):
 for _ in range(2):
  values=list(range(n*n));R.shuffle(values);grid=[values[i:i+n] for i in range(0,n*n,n)];steps=[]
  for x in range(n):
   for y in range(n):
    for method,dirs in [('adjacentSum',[(1,0),(-1,0),(0,1),(0,-1)]),('diagonalSum',[(1,1),(1,-1),(-1,1),(-1,-1)])]:
     expect=sum(grid[x+dx][y+dy] for dx,dy in dirs if 0<=x+dx<n and 0<=y+dy<n)
     steps.append([method,[grid[x][y]],expect])
  add(3242,[grid],steps)
# Every live task is explicitly sorted to select the oracle winner.
for trial in range(48):
 task=R.randrange(40);user=R.randrange(100001);priority=R.choice([0,1,10**9]);initial=[[user,task,priority]];live={task:(user,priority)};steps=[]
 for _ in range(180):
  op=R.choice(['add','edit','rmv','execTop'])
  free=[x for x in range(40) if x not in live]
  if op=='add' and free:
   t=R.choice(free);u=R.randrange(100001);p=R.choice([0,1,2,10**9,R.randrange(10**9+1)]);live[t]=(u,p);steps.append(['add',[u,t,p],None])
  elif op=='edit' and live:
   t=R.choice(list(live));p=R.choice([0,1,2,10**9]);live[t]=(live[t][0],p);steps.append(['edit',[t,p],None])
  elif op=='rmv' and live:
   t=R.choice(list(live));del live[t];steps.append(['rmv',[t],None])
  else:
   ans=-1
   if live:
    t=max(live,key=lambda x:(live[x][1],x));ans=live.pop(t)[0]
   steps.append(['execTop',[],ans])
 add(3408,[initial],steps)
add(3408,[[[9,7,100]]],[['edit',[7,1],None],['rmv',[7],None],['add',[8,7,100],None],['execTop',[],8],['execTop',[],-1],['add',[5,7,100],None],['edit',[7,100],None],['execTop',[],5],['execTop',[],-1]])
# Formulas use plain map oracle, preserving independently tracked zero defaults.
for trial in range(32):
 rows=R.choice([1,2,10,1000]);cells={};steps=[]
 refs=[c+str(r) for c in ['A','B','M','Z'] for r in {1,rows}]
 for _ in range(180):
  op=R.choice(['setCell','resetCell','getValue','getValue'])
  if op=='setCell':
   c=R.choice(refs);v=R.choice([0,1,100000,R.randrange(100001)]);cells[c]=v;steps.append([op,[c,v],None])
  elif op=='resetCell':
   c=R.choice(refs);cells[c]=0;steps.append([op,[c],None])
  else:
   a=R.choice(refs+['0','100000',str(R.randrange(100001))]);b=R.choice(refs+['0','100000',str(R.randrange(100001))]);value=lambda s:int(s) if s.isdecimal() else cells.get(s,0);steps.append([op,['='+a+'+'+b],value(a)+value(b)])
 add(3484,[rows],steps)
# List oracle deliberately uses no binary search or per-destination index.
for trial in range(48):
 limit=R.choice([2,3,7,32]);q=[];now=1;steps=[]
 for _ in range(180):
  op=R.choice(['addPacket','addPacket','forwardPacket','getCount'])
  if op=='addPacket':
   now+=R.choice([0,0,1,3]);p=[R.randrange(1,11),R.randrange(1,11),now]
   same=[v for v in q if v[2]==now]
   if same and R.randrange(3)==0:p=R.choice(same)[:]
   ok=p not in q
   if ok:
    if len(q)==limit:q.pop(0)
    q.append(p[:])
   steps.append([op,p,ok])
  elif op=='forwardPacket':steps.append([op,[],q.pop(0) if q else []])
  else:
   dest=R.randrange(1,11);a,b=sorted([R.randrange(1,now+4),R.randrange(1,now+4)]);steps.append([op,[dest,a,b],sum(p[1]==dest and a<=p[2]<=b for p in q)])
 add(3508,[limit],steps)
add(3508,[2],[['addPacket',[1,2,5],True],['addPacket',[2,2,5],True],['addPacket',[1,2,5],False],['forwardPacket',[],[1,2,5]],['addPacket',[1,2,5],True],['getCount',[2,5,5],2],['addPacket',[3,3,5],True],['forwardPacket',[],[1,2,5]],['getCount',[2,5,5],0],['forwardPacket',[],[3,3,5]],['forwardPacket',[],[]]])
p=pathlib.Path(sys.argv[1]);p.write_text(json.dumps(out,separators=(',',':'))+'\n');print(len(out),'instances',sum(len(x['steps']) for x in out),'native calls')
