import math,struct
F=1<<32;H=1<<31;Q=1<<30;T=4096
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
 def e(s,b):
  s.b.w(b)
  while s.p:s.b.w(1-b);s.p-=1
 def bit(s,p,b):
  p=max(1,min(T-1,p));c=0 if b==0 else T-p;f=T-p if b==0 else p
  r=s.h-s.l+1;s.h=s.l+(r*(c+f))//T-1;s.l=s.l+(r*c)//T
  while 1:
   if s.h<H:s.e(0)
   elif s.l>=H:s.e(1);s.l-=H;s.h-=H
   elif s.l>=Q and s.h<H+Q:s.p+=1;s.l-=Q;s.h-=Q
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def dbit(s,p):
  p=max(1,min(T-1,p));r=s.h-s.l+1;x=((s.c-s.l+1)*T-1)//r;b=0 if x<T-p else 1
  c=0 if b==0 else T-p;f=T-p if b==0 else p
  s.h=s.l+(r*(c+f))//T-1;s.l=s.l+(r*c)//T
  while 1:
   if s.h<H:pass
   elif s.l>=H:s.l-=H;s.h-=H;s.c-=H
   elif s.l>=Q and s.h<H+Q:s.l-=Q;s.h-=Q;s.c-=Q
   else:break
   s.l<<=1;s.h=(s.h<<1)|1;s.c=(s.c<<1)|s.b.r()
  return b
 def fin(s):s.p+=1;s.e(0 if s.l<Q else 1);return s.b.f()
class B:
 def __init__(s):s.z=1;s.o=1
 def p(s):return s.o*T//(s.z+s.o)
 def u(s,x):
  if x:s.o+=1
  else:s.z+=1
  if s.z+s.o>2048:s.z=(s.z+1)//2;s.o=(s.o+1)//2
def bc(b):
 if 65<=b<=90:return 1
 if 97<=b<=122:return 2
 if 48<=b<=57:return 3
 if b in (9,10,13,32):return 4
 if b in (60,62,47,34,38,59):return 5
 if b in (91,93,123,124,125):return 6
 if b>=128:return 7
 return 0
class S:
 def __init__(s):
  s.f=0;s.w=0;s.p=0;s.q=0;s.r=0;s.c=0;s.pg=0;s.col=0;s.tail=bytearray();s.word=bytearray();s.slot=0
 def up(s,b):
  if s.p==91 and b==91:s.w=1
  elif s.p==93 and b==93:s.w=0;s.slot=0 if s.slot in (1,2) else s.slot
  elif s.p==123 and b==123:s.w=2
  elif s.p==125 and b==125:s.w=0;s.slot=0 if s.slot in (3,4,7,8) else s.slot
  elif s.p==60 and b in (114,82):s.w=3
  s.tail.append(b)
  if len(s.tail)>192:del s.tail[:64]
  t=bytes(s.tail[-96:]);tl=t.lower()
  if tl.endswith(b"[[category:"):s.slot=1
  elif tl.endswith(b"[[image:") or tl.endswith(b"[[file:"):s.slot=2
  elif tl.endswith(b"{{cite"):s.slot=3
  elif tl.endswith(b"{{infobox"):s.slot=4
  elif tl.endswith(b"<ref"):s.slot=5
  elif s.slot==5 and (tl.endswith(b'name="') or tl.endswith(b"name='")):s.slot=6
  elif s.w==2 and tl.endswith(b"url="):s.slot=7
  elif s.w==2 and tl.endswith(b"title="):s.slot=8
  elif tl.endswith(b"==references=="):s.slot=9
  elif tl.endswith(b"</ref>"):s.slot=0
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
  elif t.endswith(b"</text>"):s.f=0;s.slot=0
  s.col=0 if b==10 else min(255,s.col+1);s.r=s.q;s.q=s.p;s.p=b;s.c=bc(b)
  if 65<=b<=90 or 97<=b<=122:
   s.word.append(b|32)
   if len(s.word)>24:del s.word[:8]
  else:s.word=bytearray()
class M:
 def __init__(s):s.m={};s.ss={}
 def bm(s,k):return s.m.setdefault(k,B())
 def keys(s,st,bp,pfx,pos):
  w=bytes(st.word[-8:]) if len(st.word)>=2 else b""
  w4=bytes(st.word[-4:]) if len(st.word)>=2 else b""
  return ((0,bp,pfx,st.p),(1,bp,pfx,st.q,st.p),(2,bp,pfx,st.r,st.q,st.p),(3,bp,pfx,st.f,st.p),(4,bp,pfx,st.f,st.slot,st.p),(5,bp,pfx,st.w,st.c,st.p),(6,bp,pfx,st.pg,st.f,st.slot),(7,bp,pfx,w),(8,bp,pfx,w4,st.f),(9,bp,pfx,st.col>>3,st.f),(10,bp,pfx,(pos>>6)&31,st.f),(11,bp,pfx,bc(st.p),bc(st.q)))
 def prob(s,st,bp,pfx,pos):
  num=2048;den=1;mods=[]
  for k in s.keys(st,bp,pfx,pos):
   m=s.bm(k);mods.append(m);n=m.z+m.o;w=1
   if n>4:w=2
   if n>16:w=4
   if n>64:w=8
   if n>256:w=16
   num+=m.p()*w;den+=w
  p=num//den
  sb=(min(15,p>>8),bp,pfx&15,st.f,st.slot)
  sm=s.ss.get(sb)
  if sm is not None and sm.z+sm.o>3:p=(p+sm.p())//2
  return max(1,min(T-1,p)),mods,sb
 def bitcost(s,st,bp,pfx,pos,bit):
  p,_,_=s.prob(st,bp,pfx,pos)
  return math.log2(T/p) if bit else math.log2(T/(T-p))
 def upd(s,mods,sb,bit):
  for m in mods:m.u(bit)
  sm=s.ss.setdefault(sb,B());sm.u(bit)
 def cost(s,st,b,pos):
  pfx=1;z=0.0
  for bp in range(8):
   bit=(b>>(7-bp))&1;z+=s.bitcost(st,bp,pfx,pos,bit);pfx=(pfx<<1)|bit
  return z
 def enc(s,a,st,b,pos):
  pfx=1
  for bp in range(8):
   bit=(b>>(7-bp))&1;p,mods,sb=s.prob(st,bp,pfx,pos);a.bit(p,bit);s.upd(mods,sb,bit);pfx=(pfx<<1)|bit
  st.up(b)
 def dec(s,a,st,pos):
  pfx=1;b=0
  for bp in range(8):
   p,mods,sb=s.prob(st,bp,pfx,pos);bit=a.dbit(p);s.upd(mods,sb,bit);b=(b<<1)|bit;pfx=(pfx<<1)|bit
  st.up(b);return b
def compress(d):
 a=AC();m=M();st=S()
 for i,b in enumerate(d):m.enc(a,st,b,i)
 return struct.pack(">I",len(d))+a.fin()
def decompress(x):
 n=struct.unpack(">I",x[:4])[0];a=AC(x[4:]);m=M();st=S();o=bytearray()
 for i in range(n):o.append(m.dec(a,st,i))
 return bytes(o)
