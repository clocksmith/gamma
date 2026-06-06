import math,struct
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
  if s.n==0:
   s.c=s.d[s.i] if s.i<len(s.d) else 0;s.i+=1;s.n=8
  b=(s.c>>7)&1;s.c=(s.c<<1)&255;s.n-=1;return b
class E:
 def __init__(s):s.l=0;s.h=F-1;s.p=0;s.b=BO()
 def e(s,b):
  s.b.w(b)
  while s.p:s.b.w(1-b);s.p-=1
 def bit(s,p,b):
  t=4096;p=max(1,min(4095,p));c=0 if b==0 else 4096-p;f=(4096-p) if b==0 else p
  r=s.h-s.l+1;s.h=s.l+(r*(c+f))//t-1;s.l=s.l+(r*c)//t
  while 1:
   if s.h<H:s.e(0)
   elif s.l>=H:s.e(1);s.l-=H;s.h-=H
   elif s.l>=Q and s.h<H+Q:s.p+=1;s.l-=Q;s.h-=Q
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def fin(s):s.p+=1;s.e(0 if s.l<Q else 1);return s.b.f()
class D:
 def __init__(s,d):
  s.l=0;s.h=F-1;s.b=BI(d);s.c=0
  for _ in range(32):s.c=(s.c<<1)|s.b.r()
 def bit(s,p):
  t=4096;p=max(1,min(4095,p));r=s.h-s.l+1;x=((s.c-s.l+1)*t-1)//r
  b=0 if x<4096-p else 1;c=0 if b==0 else 4096-p;f=(4096-p) if b==0 else p
  s.h=s.l+(r*(c+f))//t-1;s.l=s.l+(r*c)//t
  while 1:
   if s.h<H:pass
   elif s.l>=H:s.l-=H;s.h-=H;s.c-=H
   elif s.l>=Q and s.h<H+Q:s.l-=Q;s.h-=Q;s.c-=Q
   else:break
   s.l<<=1;s.h=(s.h<<1)|1;s.c=(s.c<<1)|s.b.r()
  return b
class M:
 def __init__(s):s.a=1;s.b=1
 def p(s):return s.b*4096//(s.a+s.b)
 def u(s,x):
  if x:s.b+=1
  else:s.a+=1
  if s.a+s.b>2048:s.a=(s.a+1)//2;s.b=(s.b+1)//2
def L(p):
 p=max(1,min(4095,p))/4096
 return math.log(p/(1-p))/8
def S(x):
 if x<-20:return 0
 if x>20:return 4095
 return max(1,min(4095,int(4096/(1+math.exp(-x)))))
def C(b):
 if 65<=b<=90:return 1
 if 97<=b<=122:return 2
 if 48<=b<=57:return 3
 if b in (9,10,13,32):return 4
 if b in (60,62,47,34,38,59):return 5
 if b in (91,93,123,124,125):return 6
 if b>=128:return 7
 return 0
class X:
 def __init__(s):
  s.t=[{} for _ in range(9)];s.w=[[0.0]*10 for _ in range(8)];s.pr=[0,0,0,0];s.st=0;s.pc=0
 def p(s,bp,pfx,pos):
  a=s.pr;ks=((0,bp,pfx),(1,bp,pfx,a[0]),(2,bp,pfx,a[1],a[0]),(3,bp,pfx,a[2],a[1],a[0]),(4,bp,pfx,s.st),(5,bp,pfx,s.pc),(6,bp,pfx,a[0]>>4,s.st),(7,bp,pfx,pos&31),(8,bp,pfx,(a[0]^a[1])&255))
  ms=[];xs=[1.0]
  for i,k in enumerate(ks):
   m=s.t[i].setdefault(k,M());ms.append(m);xs.append(L(m.p()))
  z=0.0
  for w,x in zip(s.w[bp],xs):z+=w*x
  return S(z),ms,xs
 def u(s,bp,bit,p,ms,xs):
  e=bit-p/4096;w=s.w[bp]
  for i,x in enumerate(xs):
   v=w[i]+0.006*e*x
   w[i]=8 if v>8 else -8 if v<-8 else v
  for m in ms:m.u(bit)
 def byte(s,b):
  if b==60:s.st=1
  elif b==62 or b==10:s.st=0
  elif b==91:s.st=2
  elif b==123:s.st=3
  s.pr=[b,s.pr[0],s.pr[1],s.pr[2]];s.pc=C(b)
def compress(d):
 x=X();e=E()
 for pos,b in enumerate(d):
  pfx=1
  for bp in range(8):
   bit=(b>>(7-bp))&1;p,ms,xs=x.p(bp,pfx,pos);e.bit(p,bit);x.u(bp,bit,p,ms,xs);pfx=(pfx<<1)|bit
  x.byte(b)
 return struct.pack(">I",len(d))+e.fin()
def decompress(a):
 n=struct.unpack(">I",a[:4])[0];x=X();d=D(a[4:]);o=bytearray()
 for pos in range(n):
  b=0;pfx=1
  for bp in range(8):
   p,ms,xs=x.p(bp,pfx,pos);bit=d.bit(p);x.u(bp,bit,p,ms,xs);b=(b<<1)|bit;pfx=(pfx<<1)|bit
  o.append(b);x.byte(b)
 return bytes(o)
