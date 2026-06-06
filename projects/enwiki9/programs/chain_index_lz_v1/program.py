import struct,math
F=1<<32;H=1<<31;Q=1<<30
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
  if s.n==0:s.c=s.d[s.i] if s.i<len(s.d) else 0;s.i+=1;s.n=8
  b=(s.c>>7)&1;s.c=(s.c<<1)&255;s.n-=1;return b
class AC:
 def __init__(s,d=None):
  s.l=0;s.h=F-1;s.p=0
  if d is None:s.b=BO();s.c=None
  else:
   s.b=BI(d);s.c=0
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
class M:
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
 def __init__(s):s.f=0;s.w=0;s.p=0;s.q=0;s.r=0;s.c=0;s.pg=0;s.tail=bytearray()
 def keys(s):
  return ((0,s.r,s.q,s.p,s.f,s.pg,s.c),(1,s.r,s.q,s.p,s.f,s.c),(2,s.r,s.q,s.p),(3,s.q,s.p))
 def up(s,b):
  if s.p==91 and b==91:s.w=1
  elif s.p==93 and b==93:s.w=0
  elif s.p==123 and b==123:s.w=2
  elif s.p==125 and b==125:s.w=0
  s.tail.append(b)
  if len(s.tail)>160:del s.tail[:64]
  t=bytes(s.tail[-96:])
  if t.endswith(b"<title>"):s.f=1
  elif t.endswith(b"</title>"):
   z=t.lower();s.pg=2 if b"list of" in z else 3 if b"disambiguation" in z else 4;s.f=0
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
  s.r=s.q;s.q=s.p;s.p=b;s.c=bc(b)
class COD:
 def __init__(s):s.ev={};s.lv={};s.ix={};s.ln={};s.lt={}
 def m(s,d,k,n):return d.setdefault(k,M(n))
 def evm(s,st):return s.m(s.ev,(st.f,st.pg,st.c),M(2) if 0 else 2)
 def cost_ev(s,st,x):return s.evm(st).bits(x)
 def enc_ev(s,a,st,x):m=s.evm(st);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
 def dec_ev(s,a,st):m=s.evm(st);x=a.tar(m.t);v,c,f=m.find(x);a.dec(c,f,m.t);m.up(v);return v
 def cost_match(s,st,lev,idx,L):
  lb=min(31,L-4);return s.m(s.lv,(st.f,st.pg),4).bits(lev)+s.m(s.ix,(lev,st.f,st.pg),16).bits(idx)+s.m(s.ln,(lev,idx,st.f),255).bits(lb)
 def enc_match(s,a,st,lev,idx,L):
  lb=min(31,L-4)
  for d,k,n,x in ((s.lv,(st.f,st.pg),4,lev),(s.ix,(lev,st.f,st.pg),16,idx),(s.ln,(lev,idx,st.f),255,lb)):
   m=s.m(d,k,n);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
 def dec_match(s,a,st):
  m=s.m(s.lv,(st.f,st.pg),4);x=a.tar(m.t);lev,c,f=m.find(x);a.dec(c,f,m.t);m.up(lev)
  m=s.m(s.ix,(lev,st.f,st.pg),16);x=a.tar(m.t);idx,c,f=m.find(x);a.dec(c,f,m.t);m.up(idx)
  m=s.m(s.ln,(lev,idx,st.f),255);x=a.tar(m.t);lb,c,f=m.find(x);a.dec(c,f,m.t);m.up(lb)
  return lev,idx,lb+4
 def litm(s,st):return s.m(s.lt,(st.f,st.w,st.c,st.p,st.q),256)
 def cost_lit(s,st,b):return s.litm(st).bits(b)
 def enc_lit(s,a,st,b):
  m=s.litm(st);c,f,t=m.cf(b);a.enc(c,f,t);m.up(b)
 def dec_lit(s,a,st):
  m=s.litm(st);x=a.tar(m.t);b,c,f=m.find(x);a.dec(c,f,m.t);m.up(b);return b
def add(ch,st,pos):
 for k in st.keys():
  a=ch.setdefault(k,[]);a.append(pos)
  if len(a)>64:del a[:-64]
def candidates(d,i,ch,st):
 out=[]
 for lev,k in enumerate(st.keys()):
  arr=ch.get(k,())[-16:]
  for idx,j in enumerate(reversed(arr)):
   if j>=i:continue
   L=0;m=min(258,len(d)-i)
   while L<m and d[j+L]==d[i+L]:L+=1
   if L>=4:out.append((min(L,35),lev,idx,j))
 out.sort(reverse=True);return out[:24]
def lit_enc(a,b):
 for i in range(8):a.enc(0 if ((b>>(7-i))&1)==0 else 1,1,2)
def lit_dec(a):
 b=0
 for _ in range(8):
  x=a.tar(2);a.dec(x,1,2);b=(b<<1)|x
 return b
def compress(d):
 a=AC();st=ST();co=COD();ch={};i=0
 while i<len(d):
  best=None
  cands=candidates(d,i,ch,st);cands.sort(key=lambda x:(x[1],x[2],-x[0]))
  for L,lev,idx,j in cands:
   if idx<16 and co.cost_ev(st,1)+co.cost_match(st,lev,idx,L)+1<co.cost_ev(st,0)+sum(co.cost_lit(st,d[i+k]) for k in range(min(L,16))):
    best=(L,lev,idx,j);break
  if best:
   L,lev,idx,j=best;co.enc_ev(a,st,1);co.enc_match(a,st,lev,idx,L)
   for p in range(i,i+L):add(ch,st,p);st.up(d[p])
   i+=L
  else:
   co.enc_ev(a,st,0);co.enc_lit(a,st,d[i]);add(ch,st,i);st.up(d[i]);i+=1
 return struct.pack(">I",len(d))+a.fin()
def decompress(x):
 n=struct.unpack(">I",x[:4])[0];a=AC(x[4:]);st=ST();co=COD();ch={};o=bytearray()
 while len(o)<n:
  if co.dec_ev(a,st)==0:
   b=co.dec_lit(a,st);o.append(b);add(ch,st,len(o)-1);st.up(b)
  else:
   lev,idx,L=co.dec_match(a,st);arr=ch.get(st.keys()[lev],())
   arr=arr[-16:]
   if idx>=len(arr):raise ValueError("chain")
   p=arr[-1-idx]
   for _ in range(L):
    b=o[p];p+=1;o.append(b);add(ch,st,len(o)-1);st.up(b)
 return bytes(o[:n])
