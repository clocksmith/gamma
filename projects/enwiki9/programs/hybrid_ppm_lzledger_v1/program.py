import math,struct
F=1<<32;H=1<<31;Q=1<<30;ESC=256
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
class AC:
 def __init__(s,w=None):
  s.l=0;s.h=F-1;s.p=0
  if w is None:s.b=BO();s.c=None
  else:
   s.b=BI(w);s.c=0
   for _ in range(32):s.c=(s.c<<1)|s.b.r()
 def emit(s,b):
  s.b.w(b)
  while s.p:s.b.w(1-b);s.p-=1
 def enc(s,c,f,t):
  r=s.h-s.l+1;s.h=s.l+(r*(c+f))//t-1;s.l=s.l+(r*c)//t
  while 1:
   if s.h<H:s.emit(0)
   elif s.l>=H:s.emit(1);s.l-=H;s.h-=H
   elif s.l>=Q and s.h<H+Q:s.p+=1;s.l-=Q;s.h-=Q
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def tar(s,t):return ((s.c-s.l+1)*t-1)//(s.h-s.l+1)
 def dec(s,c,f,t):
  r=s.h-s.l+1;s.h=s.l+(r*(c+f))//t-1;s.l=s.l+(r*c)//t
  while 1:
   if s.h<H:pass
   elif s.l>=H:s.l-=H;s.h-=H;s.c-=H
   elif s.l>=Q and s.h<H+Q:s.l-=Q;s.h-=Q;s.c-=Q
   else:break
   s.l<<=1;s.h=(s.h<<1)|1;s.c=(s.c<<1)|s.b.r()
 def fin(s):s.p+=1;s.emit(0 if s.l<Q else 1);return s.b.f()
class CM:
 def __init__(s,n):s.c=[1]*n;s.t=n
 def cf(s,x):
  c=0
  for i in range(x):c+=s.c[i]
  return c,s.c[x],s.t
 def find(s,x):
  c=0
  for i,f in enumerate(s.c):
   if x<c+f:return i,c,f
   c+=f
  raise ValueError("arith")
 def bits(s,x):return math.log2(s.t/s.c[x])
 def up(s,x):
  s.c[x]+=1;s.t+=1
  if s.t>4096:
   s.t=0
   for i,v in enumerate(s.c):
    nv=(v+1)//2;s.c[i]=nv;s.t+=nv
class SM:
 def __init__(s):s.c={};s.e=1;s.t=1
 def has(s,x):return x in s.c
 def bits(s,x):
  f=s.e if x==ESC else s.c.get(x,0)
  return math.log2(s.t/f) if f else 99
 def cf(s,x):
  c=0
  for k in sorted(s.c):
   if k==x:return c,s.c[k],s.t
   c+=s.c[k]
  if x==ESC:return c,s.e,s.t
  raise ValueError("sym")
 def find(s,x):
  c=0
  for k in sorted(s.c):
   f=s.c[k]
   if x<c+f:return k,c,f
   c+=f
  if x<c+s.e:return ESC,c,s.e
  raise ValueError("arith")
 def up(s,x):
  if x==ESC:s.e+=1
  else:s.c[x]=s.c.get(x,0)+1
  s.t+=1
  if s.t>4096:
   nc={};nt=0
   for k,v in s.c.items():
    nv=(v+1)//2
    if nv:nc[k]=nv;nt+=nv
   s.c=nc;s.e=max(1,(s.e+1)//2);s.t=nt+s.e
def bc(b):
 if 65<=b<=90:return 1
 if 97<=b<=122:return 2
 if 48<=b<=57:return 3
 if b in (9,10,13,32):return 4
 if b in (60,62,47,34,38,59):return 5
 if b in (91,93,123,124,125):return 6
 if b>=128:return 7
 return 0
class ST:
 def __init__(s):s.f=0;s.w=0;s.p=0;s.q=0;s.c=0;s.col=0;s.hist=[];s.tail=bytearray()
 def cp(s):
  t=bytes(s.tail[-96:])
  if t.endswith(b"<title>"):s.f=1
  elif t.endswith(b"</title>"):s.f=0
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
 def up(s,b):
  if s.p==91 and b==91:s.w=1
  elif s.p==93 and b==93:s.w=0
  elif s.p==123 and b==123:s.w=2
  elif s.p==125 and b==125:s.w=0
  elif s.p==60 and b in (114,82):s.w=3
  s.tail.append(b)
  if len(s.tail)>192:del s.tail[:64]
  s.cp();s.col=0 if b==10 else min(255,s.col+1);s.q=s.p;s.p=b;s.c=bc(b);s.hist.append(b)
  if len(s.hist)>8:del s.hist[0]
 def keys(s):
  h=bytes(s.hist)
  return ((4,s.f,s.w,h[-4:]),(3,s.f,h[-3:]),(2,s.w,h[-2:]),(1,s.c,h[-1:]),(0,))
class PPM:
 def __init__(s):s.m={}
 def mod(s,k):return s.m.setdefault(k,SM())
 def cost(s,st,b):
  z=0.0
  for k in st.keys():
   m=s.mod(k)
   if m.has(b):return z+m.bits(b)
   z+=m.bits(ESC)
  return z+8
 def enc(s,a,st,b):
  used=[]
  for k in st.keys():
   m=s.mod(k);used.append(m)
   if m.has(b):
    c,f,t=m.cf(b);a.enc(c,f,t)
    for x in used:x.up(b)
    return
   c,f,t=m.cf(ESC);a.enc(c,f,t);m.up(ESC)
  for i in range(8):a.enc(0 if ((b>>(7-i))&1)==0 else 1,1,2)
  for x in used:x.up(b)
 def dec(s,a,st):
  used=[]
  for k in st.keys():
   m=s.mod(k);used.append(m);x=a.tar(m.t);sym,c,f=m.find(x);a.dec(c,f,m.t)
   if sym!=ESC:
    for q in used:q.up(sym)
    return sym
   m.up(ESC)
  b=0
  for _ in range(8):
   bit=a.tar(2);a.dec(bit,1,2);b=(b<<1)|bit
  for x in used:x.up(b)
  return b
class TOK:
 def __init__(s):s.e=CM(2);s.l={};s.d={};s.lo={};s.last=(0,0)
 def mc(s,L,D):
  db=D.bit_length()-1;lo=D-(1<<db);lb=min(254,L-4);lk=(s.last[1],min(31,s.last[0]//8));dk=(min(31,L//8),s.last[1])
  lm=s.l.setdefault(lk,CM(255));dm=s.d.setdefault(dk,CM(32));om=s.lo.setdefault((db,s.last[1]),CM(2))
  return s.e.bits(1)+lm.bits(lb)+dm.bits(db)+db
 def me(s,a,L,D):
  db=D.bit_length()-1;lo=D-(1<<db);lb=min(254,L-4);lk=(s.last[1],min(31,s.last[0]//8));dk=(min(31,L//8),s.last[1])
  c,f,t=s.e.cf(1);a.enc(c,f,t);s.e.up(1)
  lm=s.l.setdefault(lk,CM(255));c,f,t=lm.cf(lb);a.enc(c,f,t);lm.up(lb)
  dm=s.d.setdefault(dk,CM(32));c,f,t=dm.cf(db);a.enc(c,f,t);dm.up(db)
  for i in range(db-1,-1,-1):a.enc(0 if ((lo>>i)&1)==0 else 1,1,2)
  s.last=(L,db)
 def md(s,a):
  c,f,t=s.e.cf(1);a.dec(c,f,t);s.e.up(1)
  lk=(s.last[1],min(31,s.last[0]//8));lm=s.l.setdefault(lk,CM(255));x=a.tar(lm.t);lb,c,f=lm.find(x);a.dec(c,f,lm.t);lm.up(lb)
  dk=(min(31,(lb+4)//8),s.last[1]);dm=s.d.setdefault(dk,CM(32));x=a.tar(dm.t);db,c,f=dm.find(x);a.dec(c,f,dm.t);dm.up(db)
  lo=0
  for _ in range(db):bit=a.tar(2);a.dec(bit,1,2);lo=(lo<<1)|bit
  L=lb+4;D=(1<<db)+lo;s.last=(L,db);return L,D
 def lc(s):return s.e.bits(0)
 def le(s,a):c,f,t=s.e.cf(0);a.enc(c,f,t);s.e.up(0);s.last=(0,s.last[1])
 def ld(s,a):c,f,t=s.e.cf(0);a.dec(c,f,t);s.e.up(0);s.last=(0,s.last[1])
def add(tab,d,i):
 if i+4<=len(d):
  k=d[i:i+4];a=tab.setdefault(k,[]);a.append(i)
  if len(a)>128:del a[:-128]
def mat(d,i,tab):
 r=[]
 for j in reversed(tab.get(d[i:i+4],())[-96:]):
  if i<=j:continue
  L=4;m=min(258,len(d)-i)
  while L<m and d[j+L]==d[i+L]:L+=1
  if L>=4:r.append((L,i-j))
 r.sort(reverse=True);return r[:16]
def compress(d):
 a=AC();st=ST();ppm=PPM();tok=TOK();tab={};i=0;n=len(d)
 while i<n:
  lit=tok.lc()+ppm.cost(st,d[i]);best=None
  if i+4<=n:
   for L,D in mat(d,i,tab):
    if tok.mc(L,D)<sum(ppm.cost(st,d[i+k]) for k in range(min(L,24)))+tok.lc():
     best=(L,D);break
  if best:
   L,D=best;tok.me(a,L,D)
   for k in range(i,i+L):st.up(d[k]);add(tab,d,k)
   i+=L
  else:
   tok.le(a);ppm.enc(a,st,d[i]);st.up(d[i]);add(tab,d,i);i+=1
 return struct.pack(">I",n)+a.fin()
def decompress(x):
 n=struct.unpack(">I",x[:4])[0];a=AC(x[4:]);st=ST();ppm=PPM();tok=TOK();o=bytearray()
 while len(o)<n:
  if a.tar(tok.e.t)<tok.e.c[0]:
   tok.ld(a);b=ppm.dec(a,st);o.append(b);st.up(b)
  else:
   L,D=tok.md(a);p=len(o)-D
   if p<0:raise ValueError("distance")
   for _ in range(L):
    b=o[p];p+=1;o.append(b);st.up(b)
 return bytes(o[:n])
