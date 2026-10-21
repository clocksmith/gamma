"""Restricted, independently implemented literal activation/occurrence flow."""
import math,time,struct,hashlib,statistics,itertools,warnings
import numpy as np
from scipy.optimize import milp,linprog,Bounds,LinearConstraint
from scipy.sparse import coo_matrix

def graph(texts,pool):
 edges=[];by_program=[]
 for p,text in enumerate(texts):
  starts=[[] for _ in range(len(text)+1)]
  for start in range(len(text)):
   for t,word in enumerate(pool):
    if text.startswith(word,start):
     end=start+len(word);starts[start].append((end,t,len(edges)));edges.append((p,start,end,t))
  by_program.append(starts)
 return edges,by_program

def parse(starts,selected):
 n=len(starts)-1;dist=[n+1]*(n+1);choice=[None]*(n+1);dist[n]=0
 for pos in range(n-1,-1,-1):
  options=[(1+dist[end],t,end) for end,t,_ in starts[pos] if t in selected]
  if options:dist[pos],t,end=min(options);choice[pos]=(t,end)
 if dist[0]>n:raise ValueError('unreachable source')
 seq=[];pos=0
 while pos<n:t,pos=choice[pos];seq.append(t)
 return seq

def evaluate(texts,pool,graphs,selected,width):
 selected=set(selected);seqs=[parse(g,selected) for g in graphs];counts=[len(s) for s in seqs];chars=sum(len(pool[t])==1 for s in seqs for t in s);dictionary=8+sum(4+len(pool[t].encode()) for t in selected);packet=sum(41+math.ceil(width*n/8) for n in counts)
 return {'entries':len(selected),'selections':sum(counts),'median':statistics.median(counts),'p95':sorted(counts)[math.ceil(.95*len(counts))-1],'worst':max(counts),'character_fraction':chars/sum(counts),'dictionary_bytes':dictionary,'packet_bytes':packet,'package_bytes':dictionary+packet,'payload_bits':width*sum(counts),'framing_bytes':41*len(texts),'padding_bits':sum((-width*n)%8 for n in counts),'counts':counts,'sequences':seqs}

def build(texts,pool,cap,width,objective):
 edges,graphs=graph(texts,pool);nt=len(pool);ne=len(edges);n=nt+ne+len(texts);rows=[];cols=[];vals=[];lo=[];hi=[]
 def constraint(values,lower,upper):
  r=len(lo);lo.append(lower);hi.append(upper)
  for col,value in values:rows.append(r);cols.append(col);vals.append(value)
 incidence={}
 for e,(p,start,end,t) in enumerate(edges):
  incidence.setdefault((p,start),[]).append((nt+e,1));incidence.setdefault((p,end),[]).append((nt+e,-1));constraint([(nt+e,1),(t,-1)],-np.inf,0)
 for p,text in enumerate(texts):
  for pos in range(len(text)+1):
   rhs=1 if pos==0 else -1 if pos==len(text) else 0
   constraint(incidence.get((p,pos),[]),rhs,rhs)
 constraint([(t,1) for t in range(nt)],-np.inf,cap)
 for p in range(len(texts)):constraint([(nt+e,width) for e,row in enumerate(edges) if row[0]==p]+[(nt+ne+p,-8)],-np.inf,0)
 matrix=coo_matrix((vals,(rows,cols)),shape=(len(lo),n)).tocsc();lb=np.zeros(n);ub=np.ones(n);mandatory={t for t,s in enumerate(pool) if len(s)==1}
 for t in mandatory:lb[t]=1
 for p,text in enumerate(texts):ub[nt+ne+p]=math.ceil(width*len(text)/8)
 c=np.zeros(n)
 if objective=='selections':c[nt:nt+ne]=1;constant=0
 else:
  c[:nt]=[4+len(s.encode()) for s in pool];c[nt+ne:]=1;constant=8+41*len(texts)
 return {'texts':texts,'pool':pool,'cap':cap,'width':width,'objective':objective,'edges':edges,'graphs':graphs,'nt':nt,'ne':ne,'matrix':matrix,'lo':np.array(lo),'hi':np.array(hi),'lb':lb,'ub':ub,'cost':c,'constant':constant,'mandatory':mandatory}

def solve(m,integer,seconds):
 start=time.monotonic()
 with warnings.catch_warnings(record=True) as ws:
  if integer:
   r=milp(m['cost'],integrality=np.ones(len(m['cost'])),bounds=Bounds(m['lb'],m['ub']),constraints=LinearConstraint(m['matrix'],m['lo'],m['hi']),options={'time_limit':seconds,'mip_rel_gap':0.0,'threads':1,'random_seed':0,'mip_feasibility_tolerance':1e-8})
  else:
   eq=np.isfinite(m['lo'])&(m['lo']==m['hi']);ineq=~eq
   r=linprog(m['cost'],A_ub=m['matrix'][ineq],b_ub=m['hi'][ineq],A_eq=m['matrix'][eq],b_eq=m['hi'][eq],bounds=list(zip(m['lb'],m['ub'])),method='highs',options={'time_limit':seconds,'threads':1,'dual_feasibility_tolerance':1e-8,'primal_feasibility_tolerance':1e-8})
 rec={'status':int(r.status),'message':str(r.message),'success':bool(r.success),'elapsed_seconds':time.monotonic()-start,'warnings':[str(w.message) for w in ws],'time_limit':seconds,'objective':None if r.fun is None else float(r.fun)+m['constant'],'vector':None if r.x is None else r.x.tolist()}
 for k in ['mip_gap','mip_node_count','mip_dual_bound']:
  v=getattr(r,k,None)
  if v is not None:rec[k]=float(v)+(m['constant'] if k=='mip_dual_bound' else 0)
 if r.x is not None:
  ax=m['matrix']@r.x;rec['constraint_violation']=float(max(np.max(np.maximum(m['lo']-ax,0)),np.max(np.maximum(ax-m['hi'],0)),np.max(np.maximum(m['lb']-r.x,0)),np.max(np.maximum(r.x-m['ub'],0))))
  rec['integer_distance']=float(np.max(abs(r.x-np.round(r.x))))
 return rec

def rounded(m,lp,scheme):
 y=lp['vector'][:m['nt']];mandatory=m['mandatory'];optional=[i for i in range(m['nt']) if i not in mandatory]
 if scheme=='Int':return mandatory|{i for i in optional if y[i]>=.999}
 order=sorted(optional,key=lambda i:(-(y[i]/len(m['pool'][i].encode()) if scheme=='Bias' else y[i]),m['pool'][i]))
 return mandatory|set(order[:m['cap']-len(mandatory)])

def greedy(m,seconds):
 start=time.monotonic();selected=set(m['mandatory']);state=evaluate(m['texts'],m['pool'],m['graphs'],selected,m['width']);trace=[];probes=0;stop='no_improvement'
 key='selections' if m['objective']=='selections' else 'package_bytes'
 def cost(s):return(s[key],s['package_bytes'] if key=='selections' else s['selections'])
 while len(selected)<m['cap']:
  best=state;bestid=None;complete=True
  for i in range(m['nt']):
   if i in selected:continue
   if time.monotonic()-start>=seconds:complete=False;break
   candidate=evaluate(m['texts'],m['pool'],m['graphs'],selected|{i},m['width']);probes+=1
   if cost(candidate)<cost(best):best,bestid=candidate,i
  if bestid is None:
   if not complete:stop='time_limit'
   break
  selected.add(bestid);trace.append({'add':bestid,'before':state[key],'after':best[key]});state=best
  if not complete:stop='time_limit';break
 else:stop='capacity'
 return selected,{'elapsed_seconds':time.monotonic()-start,'probes':probes,'stop':stop,'trace':trace,'time_limit':seconds}

def dictionary_bytes(vocab):
 return b'LTD1'+struct.pack('>I',len(vocab))+b''.join(struct.pack('>I',len(s.encode()))+s.encode() for s in vocab)
def packet_bytes(raw,seq,width):
 bits=0
 for i in seq:bits=(bits<<width)|i
 bits<<=(-len(seq)*width)%8
 return b'LTV1'+bytes([width])+hashlib.sha256(raw).digest()+struct.pack('>I',len(seq))+bits.to_bytes(math.ceil(width*len(seq)/8),'big')
