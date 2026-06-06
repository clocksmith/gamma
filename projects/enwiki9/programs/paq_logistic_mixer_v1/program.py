import math,struct
FULL=1<<32;HALF=1<<31;QTR=1<<30;TOT=4096
class BO:
 def __init__(s):s.o=bytearray();s.c=0;s.n=0
 def w(s,b):
  s.c=(s.c<<1)|(b&1);s.n+=1
  if s.n==8:s.o.append(s.c);s.c=0;s.n=0
 def f(s):
  if s.n:s.o.append((s.c<<(8-s.n))&255)
  return bytes(s.o)
class BI:
 def __init__(s,d):s.d=d;s.i=0;s.c=0;s.n=0
 def r(s):
  if s.n==0:
   s.c=s.d[s.i] if s.i<len(s.d) else 0;s.i+=1;s.n=8
  b=(s.c>>7)&1;s.c=(s.c<<1)&255;s.n-=1;return b
class AE:
 def __init__(s):s.l=0;s.h=FULL-1;s.p=0;s.b=BO()
 def emit(s,b):
  s.b.w(b)
  while s.p:s.b.w(1-b);s.p-=1
 def bit(s,p,b):
  p=max(1,min(TOT-1,p));c=0 if b==0 else TOT-p;f=TOT-p if b==0 else p;r=s.h-s.l+1
  s.h=s.l+(r*(c+f))//TOT-1;s.l=s.l+(r*c)//TOT
  while 1:
   if s.h<HALF:s.emit(0)
   elif s.l>=HALF:s.emit(1);s.l-=HALF;s.h-=HALF
   elif s.l>=QTR and s.h<HALF+QTR:s.p+=1;s.l-=QTR;s.h-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def fin(s):s.p+=1;s.emit(0 if s.l<QTR else 1);return s.b.f()
class AD:
 def __init__(s,d):
  s.l=0;s.h=FULL-1;s.b=BI(d);s.c=0
  for _ in range(32):s.c=(s.c<<1)|s.b.r()
 def bit(s,p):
  p=max(1,min(TOT-1,p));r=s.h-s.l+1;x=((s.c-s.l+1)*TOT-1)//r;b=0 if x<TOT-p else 1
  c=0 if b==0 else TOT-p;f=TOT-p if b==0 else p
  s.h=s.l+(r*(c+f))//TOT-1;s.l=s.l+(r*c)//TOT
  while 1:
   if s.h<HALF:pass
   elif s.l>=HALF:s.l-=HALF;s.h-=HALF;s.c-=HALF
   elif s.l>=QTR and s.h<HALF+QTR:s.l-=QTR;s.h-=QTR;s.c-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1;s.c=(s.c<<1)|s.b.r()
  return b
class BM:
 def __init__(s):s.a=1;s.b=1
 def p(s):return s.b*TOT//(s.a+s.b)
 def u(s,x):
  if x:s.b+=1
  else:s.a+=1
  if s.a+s.b>2048:s.a=(s.a+1)//2;s.b=(s.b+1)//2
def bc(b):
 if 65<=b<=90:return 1
 if 97<=b<=122:return 2
 if 48<=b<=57:return 3
 if b in (9,10,13,32):return 4
 if b in (60,62,47,34,38,59):return 5
 if b in (91,93,123,124,125):return 6
 if b>=128:return 7
 return 0
def lg(p):
 p=max(1,min(TOT-1,p))/TOT
 return math.log2(1/p)

def stretch(p):
 p=max(1,min(TOT-1,p))/TOT
 return math.log(p/(1-p))/8

def squash(x):
 if x<-20:return 0
 if x>20:return TOT-1
 return max(1,min(TOT-1,int(TOT/(1+math.exp(-x)))))

class ST:
 def __init__(s):
  s.f=0;s.w=0;s.p=0;s.q=0;s.c=0;s.col=0;s.tail=bytearray();s.pc=0
 def cp(s):
  t=bytes(s.tail[-96:])
  if t.endswith(b"<title>"):s.f=1
  elif t.endswith(b"</title>"):
   z=t.lower();s.pc=2 if b"list of" in z else 3 if b"disambiguation" in z else 4;s.f=0
  elif t.endswith(b"<id>"):s.f=2
  elif t.endswith(b"</id>"):s.f=0
  elif t.endswith(b"<timestamp>"):s.f=3
  elif t.endswith(b"</timestamp>"):s.f=0
  elif t.endswith(b"<username>"):s.f=4
  elif t.endswith(b"</username>"):s.f=0
  elif t.endswith(b"<comment>"):s.f=5
  elif t.endswith(b"</comment>"):s.f=0
  elif t.endswith(b'<text xml:space="preserve">'):s.f=6
  elif t.endswith(b"</text>"):s.f=0
 def keys(s,bp,pfx,pos):
  return ((0,bp,pfx),(1,bp,pfx,s.p),(2,bp,pfx,s.q,s.p),(3,bp,pfx,s.f,s.p),(4,bp,pfx,s.w,s.p),(5,bp,pfx,s.c,bc(s.p)),(6,bp,pfx,s.col>>3,s.p),(7,bp,pfx,s.pc,s.f,s.w),(8,bp,pfx,(pos>>8)&15,s.f,s.c))
 def up(s,b):
  if s.p==91 and b==91:s.w=1
  elif s.p==93 and b==93:s.w=0
  elif s.p==123 and b==123:s.w=2
  elif s.p==125 and b==125:s.w=0
  elif s.p==60 and b in (114,82):s.w=3
  s.tail.append(b)
  if len(s.tail)>192:del s.tail[:64]
  s.cp();s.col=0 if b==10 else min(255,s.col+1);s.q=s.p;s.p=b;s.c=bc(b)

class COD:
 def __init__(s):
  s.m={}
  s.st=ST()
  s.last=(0,0)
  s.reps=[1,2,4,8]
  # Weight matrix: 8 bits x 10 inputs (9 contexts + 1 bias)
  s.w=[[0.0]*10 for _ in range(8)]
 def model(s,k):return s.m.setdefault(k,BM())
 def bitp(s,k):return s.model(k).p()
 def costbit(s,k,b):
  p=s.bitp(k);return lg(p) if b else lg(TOT-p)
 def encbit(s,ae,k,b):
  m=s.model(k);ae.bit(m.p(),b);m.u(b)
 def decbit(s,ad,k):
  m=s.model(k);b=ad.bit(m.p());m.u(b);return b

 def get_mix(s,st,bp,pfx,pos):
  ks=st.keys(bp,pfx,pos)
  ms=[];xs=[1.0]
  for k in ks:
   m=s.model(k);ms.append(m);xs.append(stretch(m.p()))
  z=0.0
  for wt,x in zip(s.w[bp],xs):z+=wt*x
  return squash(z),ms,xs

 def update_mix(s,bp,bit,p,ms,xs):
  e=bit-p/TOT;w=s.w[bp]
  for i,x in enumerate(xs):
   v=w[i]+0.006*e*x
   w[i]=8 if v>8 else -8 if v<-8 else v
  for m in ms:m.u(bit)

 def lit_cost(s,st,b,pos):
  pfx=1;c=0.0
  for bp in range(8):
   bit=(b>>(7-bp))&1
   p,_,_=s.get_mix(st,bp,pfx,pos)
   c+=lg(p) if bit else lg(TOT-p)
   pfx=(pfx<<1)|bit
  return c

 def lit_enc(s,ae,b,pos):
  pfx=1
  for bp in range(8):
   bit=(b>>(7-bp))&1
   p,ms,xs=s.get_mix(s.st,bp,pfx,pos)
   ae.bit(p,bit)
   s.update_mix(bp,bit,p,ms,xs)
   pfx=(pfx<<1)|bit
  s.st.up(b)

 def lit_dec(s,ad,pos):
  pfx=1;b=0
  for bp in range(8):
   p,ms,xs=s.get_mix(s.st,bp,pfx,pos)
   bit=ad.bit(p)
   s.update_mix(bp,bit,p,ms,xs)
   b=(b<<1)|bit
   pfx=(pfx<<1)|bit
  s.st.up(b);return b

 def evkey(s):return ("e",s.st.f,s.st.w,s.last[0]>>3,min(31,s.last[1]))
 def evcost(s,b):return s.costbit(s.evkey(),b)
 def evenc(s,ae,b):s.encbit(ae,s.evkey(),b)
 def evdec(s,ad):return s.decbit(ad,s.evkey())
 def uint_cost(s,v,n,tag):
  c=0.0
  for i in range(n-1,-1,-1):
   bit=(v>>i)&1;c+=s.costbit((tag,n,i,s.st.f,s.last[0]>>3),bit)
  return c
 def uint_enc(s,ae,v,n,tag):
  for i in range(n-1,-1,-1):s.encbit(ae,(tag,n,i,s.st.f,s.last[0]>>3),(v>>i)&1)
 def uint_dec(s,ad,n,tag):
  v=0
  for i in range(n-1,-1,-1):v=(v<<1)|s.decbit(ad,(tag,n,i,s.st.f,s.last[0]>>3))
  return v
 def mcost(s,L,D):
  db=D.bit_length()-1;lo=D-(1<<db);lc=min(254,L-4)
  c=s.evcost(1)+s.uint_cost(lc,8,"l")
  if D in s.reps:
   return c+s.uint_cost(1,1,"rp")+s.uint_cost(s.reps.index(D),2,"ri")
  return c+s.uint_cost(0,1,"rp")+s.uint_cost(db,5,"db")+s.uint_cost(lo,db,"lo")
 def menc(s,ae,L,D):
  db=D.bit_length()-1;lo=D-(1<<db);lc=min(254,L-4)
  s.evenc(ae,1);s.uint_enc(ae,lc,8,"l")
  if D in s.reps:
   s.uint_enc(ae,1,1,"rp");s.uint_enc(ae,s.reps.index(D),2,"ri")
  else:
   s.uint_enc(ae,0,1,"rp");s.uint_enc(ae,db,5,"db");s.uint_enc(ae,lo,db,"lo")
  if D in s.reps:s.reps.remove(D)
  s.reps=[D]+s.reps[:3];s.last=(L,db)
 def mdec(s,ad):
  lc=s.uint_dec(ad,8,"l")
  if s.uint_dec(ad,1,"rp"):
   D=s.reps[s.uint_dec(ad,2,"ri")];db=D.bit_length()-1
  else:
   db=s.uint_dec(ad,5,"db");lo=s.uint_dec(ad,db,"lo");D=(1<<db)+lo
  L=lc+4
  if D in s.reps:s.reps.remove(D)
  s.reps=[D]+s.reps[:3];s.last=(L,db);return L,D

def matches(d,i,tab):
 k=d[i:i+4];a=tab.get(k,());r=[]
 for j in a[-64:]:
  L=4;m=min(258,len(d)-i)
  while L<m and d[j+L]==d[i+L]:L+=1
  if L>=4:r.append((L,i-j))
 r.sort(reverse=True);return r[:12]

def addpos(tab,d,i):
 if i+4<=len(d):
  k=d[i:i+4];a=tab.setdefault(k,[]);a.append(i)
  if len(a)>128:del a[:-128]

def compress(d):
 ae=AE();c=COD();tab={};i=0;n=len(d)
 while i<n:
  best=None;lit1=c.evcost(0)+c.lit_cost(c.st,d[i],i)
  if i+4<=n:
   for L,D in matches(d,i,tab):
    lc=0.0;lim=min(L,32)
    ss=ST();ss.__dict__=c.st.__dict__.copy() if hasattr(c.st,"__dict__") else None
    
    # Fast evaluation of lit cost using the snapshot
    pfx=1; t_c=0.0
    for q in range(lim):
     # Using the exact same PAQ mixing cost
     b=d[i+q]
     pfx_q=1
     for bp in range(8):
      bit=(b>>(7-bp))&1
      p,_,_=c.get_mix(ss,bp,pfx_q,i+q)
      t_c+=lg(p) if bit else lg(TOT-p)
      pfx_q=(pfx_q<<1)|bit
     ss.up(b)
     
    mc=c.mcost(L,D)
    if mc+0.5<t_c and (best is None or mc-t_c<best[0]):best=(mc-t_c,L,D)
  if best:
   _,L,D=best;c.menc(ae,L,D)
   for q in range(i,i+L):c.st.up(d[q]);addpos(tab,d,q)
   i+=L
  else:
   c.evenc(ae,0);c.lit_enc(ae,d[i],i);addpos(tab,d,i);i+=1
 return struct.pack(">I",n)+ae.fin()

def decompress(a):
 n=struct.unpack(">I",a[:4])[0];ad=AD(a[4:]);c=COD();o=bytearray()
 while len(o)<n:
  if c.evdec(ad)==0:o.append(c.lit_dec(ad,len(o)))
  else:
   L,D=c.mdec(ad);p=len(o)-D
   if p<0:raise ValueError("bad distance")
   for _ in range(L):
    b=o[p];p+=1;o.append(b);c.st.up(b)
 return bytes(o[:n])