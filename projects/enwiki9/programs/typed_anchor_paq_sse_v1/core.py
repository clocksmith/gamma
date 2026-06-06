
import math, struct

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

class AC:
 def __init__(s,d=None):
  s.l=0;s.h=FULL-1;s.p=0
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
   if s.h<HALF:s.emit(0)
   elif s.l>=HALF:s.emit(1);s.l-=HALF;s.h-=HALF
   elif s.l>=QTR and s.h<HALF+QTR:s.p+=1;s.l-=QTR;s.h-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def bit(s,p,b):
  p=max(1,min(TOT-1,p));c=0 if b==0 else TOT-p;f=TOT-p if b==0 else p;r=s.h-s.l+1
  s.h=s.l+(r*(c+f))//TOT-1;s.l=s.l+(r*c)//TOT
  while 1:
   if s.h<HALF:s.emit(0)
   elif s.l>=HALF:s.emit(1);s.l-=HALF;s.h-=HALF
   elif s.l>=QTR and s.h<HALF+QTR:s.p+=1;s.l-=QTR;s.h-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def tar(s,t):return ((s.c-s.l+1)*t-1)//(s.h-s.l+1)
 def dec(s,c,f,t):
  r=s.h-s.l+1;s.h=s.l+(r*(c+f))//t-1;s.l=s.l+(r*c)//t
  while 1:
   if s.h<HALF:pass
   elif s.l>=HALF:s.l-=HALF;s.h-=HALF;s.c-=HALF
   elif s.l>=QTR and s.h<HALF+QTR:s.l-=QTR;s.h-=QTR;s.c-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1;s.c=(s.c<<1)|s.b.r()
 def bit_dec(s,p):
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
 def fin(s):s.p+=1;s.emit(0 if s.l<QTR else 1);return s.b.f()

class BM:
 def __init__(s):s.a=1;s.b=1
 def p(s):return s.b*TOT//(s.a+s.b)
 def u(s,x):
  if x:s.b+=1
  else:s.a+=1
  if s.a+s.b>2048:s.a=(s.a+1)//2;s.b=(s.b+1)//2

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

def bc(b):
 if 65<=b<=90:return 1
 if 97<=b<=122:return 2
 if 48<=b<=57:return 3
 if b in (9,10,13,32):return 4
 if b in (60,62,47,34,38,59):return 5
 if b in (91,93,123,124,125):return 6
 if b>=128:return 7
 return 0

class GST:
 def __init__(s):
  s.f=0;s.p=0;s.q=0;s.r=0;s.c=0;s.tail=bytearray()
  s.t_dep=0;s.l_dep=0;s.in_ref=b"";s.cap_ref=False;s.ref_n=bytearray()
  s.t_stk=[];s.cap_tmpl=False;s.tmpl_n=bytearray()
  s.in_cat=False
 def anchor(s):
  t_cur = s.t_stk[-1] if s.t_stk else b""
  return (s.f, s.t_dep, s.l_dep, s.in_cat, s.in_ref, t_cur)
 def up(s,b):
  s.tail.append(b)
  if len(s.tail)>128:del s.tail[:64]
  t=bytes(s.tail)
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
  
  if s.f==6:
   if s.p==123 and b==123:
    s.t_dep+=1;s.cap_tmpl=True;s.tmpl_n=bytearray()
   elif s.cap_tmpl:
    if b in (124,125,10):
     s.cap_tmpl=False;s.t_stk.append(bytes(s.tmpl_n))
    else:
     s.tmpl_n.append(b)
     if len(s.tmpl_n)>32:s.cap_tmpl=False;s.t_stk.append(b"?")
   elif s.p==125 and b==125:
    s.t_dep=max(0,s.t_dep-1)
    if s.t_stk:s.t_stk.pop()
    s.cap_tmpl=False

   if s.p==91 and b==91:
    s.l_dep+=1
    if t.endswith(b"[[Category:"):s.in_cat=True
   elif s.p==93 and b==93:
    s.l_dep=max(0,s.l_dep-1)
    if s.l_dep==0:s.in_cat=False

   if t.endswith(b'<ref name="'):
    s.cap_ref=True;s.ref_n=bytearray()
   elif s.cap_ref:
    if b==34:
     s.cap_ref=False;s.in_ref=bytes(s.ref_n)
    else:
     s.ref_n.append(b)
     if len(s.ref_n)>32:s.cap_ref=False;s.in_ref=b"?"
   elif t.endswith(b"</ref>"):
    s.in_ref=b""
  else:
   s.t_dep=0;s.l_dep=0;s.in_ref=b"";s.cap_ref=False;s.t_stk=[];s.cap_tmpl=False;s.in_cat=False

  s.r=s.q;s.q=s.p;s.p=b;s.c=bc(b)

def stretch(p):
 p=max(1,min(TOT-1,p))/TOT
 return math.log(p/(1-p))/8

def squash(x):
 if x<-20:return 0
 if x>20:return TOT-1
 return max(1,min(TOT-1,int(TOT/(1+math.exp(-x)))))

class PAQ:
 def __init__(s):
  s.m = {}
  s.st = GST()
  s.w = [[0.0]*10 for _ in range(8)]
  # SSE array: shape (8 bits) x (4 buckets of prob) x (256 previous bytes) = 8192 parameters
  s.sse = [[[1.0]*256 for _ in range(8)] for _ in range(8)]
  
 def model(s,k):return s.m.setdefault(k,BM())
 
 def get_mix(s,bp,pfx,pos):
  # Get features from state
  anc = s.st.anchor()
  q = s.st.q; p = s.st.p; c = s.st.c
  
  # Contexts
  ks = (
      (0, bp, pfx),
      (1, bp, pfx, p),
      (2, bp, pfx, q, p),
      (3, bp, pfx, c, p),
      (4, bp, pfx, anc),
      (5, bp, pfx, anc, p),
      (6, bp, pfx, (pos>>8)&15),
      (7, bp, pfx, anc, c)
  )
  ms = []; xs = [1.0] # bias
  for k in ks:
   m = s.model(k); ms.append(m); xs.append(stretch(m.p()))
  
  # Predict
  z = 0.0
  for wt, x in zip(s.w[bp], xs): z += wt * x
  raw_p = squash(z)
  
  # SSE Correction
  sse_bucket = (raw_p * 8) // TOT
  if sse_bucket == 8: sse_bucket = 7
  sse_val = s.sse[bp][sse_bucket][p]
  
  # Combine raw logistic mix and SSE
  final_z = stretch(raw_p) + sse_val
  final_p = squash(final_z)
  
  return final_p, raw_p, sse_bucket, ms, xs
  
 def update(s, bp, bit, p_final, p_raw, sse_bucket, ms, xs):
  p_prev = s.st.p
  # Update SSE
  err = bit - p_final/TOT
  s.sse[bp][sse_bucket][p_prev] += 0.05 * err
  s.sse[bp][sse_bucket][p_prev] = max(-8.0, min(8.0, s.sse[bp][sse_bucket][p_prev]))
  
  # Update Mixer
  err_mix = bit - p_raw/TOT
  w = s.w[bp]
  for i, x in enumerate(xs):
   w[i] += 0.005 * err_mix * x
   w[i] = max(-8.0, min(8.0, w[i]))
   
  # Update Models
  for m in ms: m.u(bit)

class TOK:
 def __init__(s):s.e={};s.cix={};s.cln={};s.last=(0,0)
 def m(s,d,k,n):return d.setdefault(k,CM(n))
 def ev(s,st):return s.m(s.e,(st.anchor(),st.c),2)
 def evc(s,st,x):return s.ev(st).bits(x)
 def eve(s,a,st,x):m=s.ev(st);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
 def evd(s,a,st):m=s.ev(st);x=a.tar(m.t);v,c,f=m.find(x);a.dec(c,f,m.t);m.up(v);return v

 def chainc(s,st,idx,L):
  return s.m(s.cix,st.anchor(),16).bits(idx)+s.m(s.cln,(idx,st.anchor()),255).bits(L-4)
 def chaine(s,a,st,idx,L):
  for d,k,n,x in ((s.cix,st.anchor(),16,idx),(s.cln,(idx,st.anchor()),255,L-4)):
   m=s.m(d,k,n);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
  s.last=(L,0)
 def chaind(s,a,st):
  m=s.m(s.cix,st.anchor(),16);x=a.tar(m.t);idx,c,f=m.find(x);a.dec(c,f,m.t);m.up(idx)
  m=s.m(s.cln,(idx,st.anchor()),255);x=a.tar(m.t);lb,c,f=m.find(x);a.dec(c,f,m.t);m.up(lb)
  L=lb+4;s.last=(L,0);return idx,L

def addc(ch,st,pos):
 a=ch.setdefault(st.anchor(),[]);a.append(pos)
 if len(a)>64:del a[:-64]

def chainm(d,i,ch,st):
 r=[]
 for idx,j in enumerate(reversed(ch.get(st.anchor(),())[-16:])):
  if j>=i:continue
  L=0;m=min(258,len(d)-i)
  while L<m and d[j+L]==d[i+L]:L+=1
  if L>=4:r.append((L,idx,j))
 r.sort(reverse=True);return r[:16]

def lit_cost(p, b, pos):
 pfx = 1
 c = 0.0
 for bp in range(8):
  bit = (b>>(7-bp))&1
  prob, raw_p, sbucket, ms, xs = p.get_mix(bp, pfx, pos)
  c += -math.log2(prob/TOT) if bit else -math.log2((TOT-prob)/TOT)
  pfx = (pfx<<1) | bit
 return c

def lit_prefix(d):
 p=PAQ();pre=[0.0]
 for pos, b in enumerate(d):
  pfx = 1
  for bp in range(8):
   bit = (b>>(7-bp))&1
   prob, raw_p, sbucket, ms, xs = p.get_mix(bp, pfx, pos)
   p.update(bp, bit, prob, raw_p, sbucket, ms, xs)
   pfx = (pfx<<1) | bit
  p.st.up(b)
  pre.append(pre[-1] + lit_cost(p, b, pos))
 return pre

def upd_byte(p,ch,d,pos,b):
 addc(ch,p.st,pos)
 pfx = 1
 for bp in range(8):
  bit = (b>>(7-bp))&1
  prob, raw_p, sbucket, ms, xs = p.get_mix(bp, pfx, pos)
  p.update(bp, bit, prob, raw_p, sbucket, ms, xs)
  pfx = (pfx<<1) | bit
 p.st.up(b)

def compress(d):
 a=AC();p=PAQ();tok=TOK();ch={};pre=lit_prefix(d);i=0;n=len(d);
 
 # Reset PAQ for actual pass
 p = PAQ()
 
 while i<n:
  best=(0.0,0,1,0,0)
  if i+4<=n:
   for L,idx,j in chainm(d,i,ch,p.st):
    lit=(pre[i+L]-pre[i])+L*tok.evc(p.st,0);c=tok.evc(p.st,1)+tok.chainc(p.st,idx,L)
    g=lit-c
    if g>0.5 and g>best[0]:best=(g,1,L,idx,j)
  if best[1]==0:
   tok.eve(a,p.st,0)
   pfx = 1
   b = d[i]
   for bp in range(8):
    bit = (b>>(7-bp))&1
    prob, raw_p, sbucket, ms, xs = p.get_mix(bp, pfx, i)
    a.bit(prob, bit)
    p.update(bp, bit, prob, raw_p, sbucket, ms, xs)
    pfx = (pfx<<1) | bit
   addc(ch,p.st,i);p.st.up(b);i+=1
  else:
   _,_,L,idx,_=best;tok.eve(a,p.st,1);tok.chaine(a,p.st,idx,L)
   for q in range(i,i+L):upd_byte(p,ch,d,q,d[q])
   i+=L
 out=struct.pack(">I",n)+a.fin()
 return out

def decompress(x):
 n=struct.unpack(">I",x[:4])[0];a=AC(x[4:]);p=PAQ();tok=TOK();ch={};o=bytearray()
 while len(o)<n:
  m=tok.evd(a,p.st)
  if m==0:
   pfx = 1
   b = 0
   for bp in range(8):
    prob, raw_p, sbucket, ms, xs = p.get_mix(bp, pfx, len(o))
    bit = a.bit_dec(prob)
    p.update(bp, bit, prob, raw_p, sbucket, ms, xs)
    b = (b<<1) | bit
    pfx = (pfx<<1) | bit
   o.append(b);addc(ch,p.st,len(o)-1);p.st.up(b)
  else:
   idx,L=tok.chaind(a,p.st);arr=ch.get(p.st.anchor(),())[-16:]
   if idx>=len(arr):raise ValueError("chain")
   pos=arr[-1-idx]
   for _ in range(L):
    b=o[pos];pos+=1;o.append(b);addc(ch,p.st,len(o)-1)
    
    pfx = 1
    for bp in range(8):
     bit = (b>>(7-bp))&1
     prob, raw_p, sbucket, ms, xs = p.get_mix(bp, pfx, len(o)-1)
     p.update(bp, bit, prob, raw_p, sbucket, ms, xs)
     pfx = (pfx<<1) | bit
    p.st.up(b)
 return bytes(o[:n])
