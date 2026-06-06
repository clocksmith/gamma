
E0=0;L0=255
TT=[b'<text xml:space="preserve">',b"</text>",b"<page>",b"</page>",b"<revision>",b"</revision>",b"<contributor>",b"</contributor>",b"<timestamp>",b"</timestamp>",b"<username>",b"</username>",b"<comment>",b"</comment>",b"<title>",b"</title>",b"<id>",b"</id>",b"<minor />",b"{{",b"}}",b"[[Category:",b"[[Image:",b"[[",b"]]",b"&quot;",b"&lt;",b"&gt;",b"&amp;",b"http://",b"https://",b"<ref",b"</ref>",b"|thumb",b"|right",b"|left",b"Category:",b"File:",b"Image:"]
TS=sorted(enumerate(TT,1),key=lambda x:len(x[1]),reverse=True);TD={i:t for i,t in enumerate(TT,1)}
def oe(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  if d[i]==E0:o.extend((E0,L0));i+=1;continue
  for c,t in TS:
   if d.startswith(t,i):o.extend((E0,c));i+=len(t);break
  else:o.append(d[i]);i+=1
 return bytes(o)
def od(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  b=d[i]
  if b!=E0:o.append(b);i+=1;continue
  if i+1>=n:raise ValueError('truncated opcode')
  c=d[i+1];o.append(E0) if c==L0 else o.extend(TD[c]);i+=2
 return bytes(o)

import math,struct
_S={}
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
class PPM:
 def __init__(s,o=5):s.o=o;s.m={};s.t=bytearray()
 def keys(s,pref=b""):
  r=[]
  for n in range(s.o,-1,-1):
   if n<=len(s.t):
    p=pref if n>=5 else b""
    r.append(p+(bytes(s.t[-n:]) if n else b""))
  return r
 def mod(s,k):return s.m.setdefault(k,SM())
 def cost(s,b,pref=b""):
  z=0.0;ex=set()
  for k in s.keys(pref):
   m=s.mod(k);items=sorted((x,c) for x,c in m.c.items() if x not in ex)
   if not items:continue
   total=sum(c for _,c in items)+len(items)
   for x,c in items:
    if x==b:return z+math.log2(total/c)
   z+=math.log2(total/len(items));ex.update(x for x,_ in items)
  return z+math.log2(256-len(ex))
 def enc(s,a,b,pref=b""):
  ex=set();used=[]
  for k in s.keys(pref):
   m=s.mod(k);items=sorted((x,c) for x,c in m.c.items() if x not in ex)
   if not items:continue
   used.append(m);total=sum(c for _,c in items)+len(items);cum=0
   for x,c in items:
    if x==b:
     a.enc(cum,c,total)
     for q in used:q.up(b)
     s.up(b,pref);return
    cum+=c
   a.enc(cum,len(items),total);m.up(ESC);ex.update(x for x,_ in items)
  rem=[x for x in range(256) if x not in ex];i=rem.index(b);a.enc(i,1,len(rem))
  for q in used:q.up(b)
  s.up(b,pref)
 def dec(s,a,pref=b""):
  ex=set();used=[]
  for k in s.keys(pref):
   m=s.mod(k);items=sorted((x,c) for x,c in m.c.items() if x not in ex)
   if not items:continue
   used.append(m);total=sum(c for _,c in items)+len(items);tgt=a.tar(total);cum=0
   sym=None
   for x,c in items:
    if tgt<cum+c:sym=x;freq=c;break
    cum+=c
   if sym is not None:
    a.dec(cum,freq,total)
    for q in used:q.up(sym)
    s.up(sym,pref);return sym
   a.dec(cum,len(items),total);m.up(ESC);ex.update(x for x,_ in items)
  rem=[x for x in range(256) if x not in ex];i=a.tar(len(rem));a.dec(i,1,len(rem));b=rem[i]
  for q in used:q.up(b)
  s.up(b,pref);return b
 def up(s,b,pref=b""):
  for n in range(s.o+1):
   if n<=len(s.t):
    p=pref if n>=5 else b""
    k=p+(bytes(s.t[-n:]) if n else b"");m=s.mod(k);m.c[b]=m.c.get(b,0)+1;m.t+=1
  s.t.append(b)
  if len(s.t)>s.o:del s.t[0]
def _pp(st):
 return bytes((st.slot,st.f))
class GST:
 def __init__(s):s.f=0;s.w=0;s.p=0;s.q=0;s.r=0;s.c=0;s.pg=0;s.col=0;s.tail=bytearray();s.word=bytearray();s.slot=0;s.ents=[];s.lb=bytearray();s.in_link=0;s.tb=bytearray();s.in_title=0
 def _ep(s,v):
  if 2<=len(v)<=128:
   s.ents.append(bytes(v))
   if len(s.ents)>2048:del s.ents[:512]
 def keys(s):
  wk=bytes(s.word[-8:]) if len(s.word)>=2 else b""
  wk4=bytes(s.word[-4:]) if len(s.word)>=2 else b""
  return ((0,s.r,s.q,s.p,s.f,s.pg,s.c),(1,s.r,s.q,s.p,s.f,s.c),(2,s.r,s.q,s.p),(3,s.q,s.p),(4,wk,s.f),(5,wk4,s.w,s.f),(6,s.slot,s.f,s.w,s.c,s.p),(7,s.slot,wk4,s.f,s.w))
 def up(s,b):
  if s.p==91 and b==91:s.w=1
  elif s.p==93 and b==93:s.w=0;s.slot=0 if s.slot in (1,2) else s.slot
  elif s.p==123 and b==123:s.w=2
  elif s.p==125 and b==125:s.w=0;s.slot=0 if s.slot in (3,4,7,8) else s.slot
  elif s.p==60 and b in (114,82):s.w=3
  s.tail.append(b)
  if len(s.tail)>192:del s.tail[:64]
  t=bytes(s.tail[-96:])
  tl=t.lower()
  # opcode-event detection: pair (0, code) means we just consumed an opcode token.
  # code 24=[[  25=]]  22=[[Category:  23=[[Image:  15=<title>  16=</title>  10=<username>  11=</username>
  opc=b if (s.p==0 and b!=0 and b!=255) else 0
  # link-target receipts (between [[ open opcodes and ]] / | / link-close opcodes)
  if s.in_link:
   if opc==25 or (b==124 and not opc):
    v=bytes(s.lb);s.lb=bytearray();s.in_link=0;s._ep(v)
   else:
    if b!=0 and not (s.p==0 and b!=255):s.lb.append(b)  # skip both halves of any opcode
    if len(s.lb)>256:s.in_link=0;s.lb=bytearray()
  if opc in (22,23,24) and not s.in_link:s.in_link=1;s.lb=bytearray()
  # title receipts
  if s.in_title:
   if opc==16:
    v=bytes(s.tb);s.tb=bytearray();s.in_title=0;s._ep(v)
   else:
    if b!=0 and not (s.p==0 and b!=255):s.tb.append(b)
  if opc==15:s.in_title=1;s.tb=bytearray()
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
   s.word.append(b)
   if len(s.word)>16:del s.word[:8]
  else:s.word=bytearray()
class TOK:
 def __init__(s):s.e={};s.rl={};s.rd={};s.clv={};s.cix={};s.cln={};s.last=(0,0)
 def m(s,d,k,n):return d.setdefault(k,CM(n))
 def ev(s,st):return s.m(s.e,(st.f,st.w,st.pg,st.c),4)
 def _vint_bits(s,d,kk,v):
  v+=1;bl=v.bit_length()
  z=s.m(d,(kk,0),24).bits(bl)
  for i in range(bl-2,-1,-1):z+=s.m(d,(kk,1),2).bits((v>>i)&1)
  return z
 def _vint_enc(s,a,d,kk,v):
  v+=1;bl=v.bit_length()
  mm=s.m(d,(kk,0),24);c,f,t=mm.cf(bl);a.enc(c,f,t);mm.up(bl)
  for i in range(bl-2,-1,-1):
   bit=(v>>i)&1;mm=s.m(d,(kk,1),2);c,f,t=mm.cf(bit);a.enc(c,f,t);mm.up(bit)
 def _vint_dec(s,a,d,kk):
  mm=s.m(d,(kk,0),24);x=a.tar(mm.t);bl,c,f=mm.find(x);a.dec(c,f,mm.t);mm.up(bl)
  v=1
  for _ in range(bl-1):
   mm=s.m(d,(kk,1),2);x=a.tar(mm.t);b2,c,f=mm.find(x);a.dec(c,f,mm.t);mm.up(b2);v=(v<<1)|b2
  return v-1
 def ercptc(s,st,k):return s._vint_bits(s.__dict__.setdefault('ek',{}),st.c,k-1)
 def ercpte(s,a,st,k):s._vint_enc(a,s.__dict__.setdefault('ek',{}),st.c,k-1)
 def ercptd(s,a,st):return s._vint_dec(a,s.__dict__.setdefault('ek',{}),st.c)+1
 def evc(s,st,x):return s.ev(st).bits(x)
 def eve(s,a,st,x):m=s.ev(st);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
 def evd(s,a,st):m=s.ev(st);x=a.tar(m.t);v,c,f=m.find(x);a.dec(c,f,m.t);m.up(v);return v
 def rawc(s,L,D):
  db=D.bit_length()-1;lo=D-(1<<db);lb=L-4;lk=(s.last[1],min(31,s.last[0]//8));dk=(min(31,L//8),s.last[1])
  return s.m(s.rl,lk,255).bits(lb)+s.m(s.rd,dk,32).bits(db)+db
 def rawe(s,a,L,D):
  db=D.bit_length()-1;lo=D-(1<<db);lb=L-4;lk=(s.last[1],min(31,s.last[0]//8));dk=(min(31,L//8),s.last[1])
  for d,k,n,x in ((s.rl,lk,255,lb),(s.rd,dk,32,db)):
   m=s.m(d,k,n);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
  for i in range(db-1,-1,-1):a.enc((lo>>i)&1,1,2)
  s.last=(L,db)
 def rawd(s,a):
  lk=(s.last[1],min(31,s.last[0]//8));m=s.m(s.rl,lk,255);x=a.tar(m.t);lb,c,f=m.find(x);a.dec(c,f,m.t);m.up(lb)
  dk=(min(31,(lb+4)//8),s.last[1]);m=s.m(s.rd,dk,32);x=a.tar(m.t);db,c,f=m.find(x);a.dec(c,f,m.t);m.up(db)
  lo=0
  for _ in range(db):bit=a.tar(2);a.dec(bit,1,2);lo=(lo<<1)|bit
  L=lb+4;D=(1<<db)+lo;s.last=(L,db);return L,D
 def chainc(s,st,lev,idx,L):
  return s.m(s.clv,(st.f,st.pg),8).bits(lev)+s.m(s.cix,(lev,st.f,st.pg),16).bits(idx)+s.m(s.cln,(lev,idx,st.f),255).bits(L-4)
 def chaine(s,a,st,lev,idx,L):
  for d,k,n,x in ((s.clv,(st.f,st.pg),8,lev),(s.cix,(lev,st.f,st.pg),16,idx),(s.cln,(lev,idx,st.f),255,L-4)):
   m=s.m(d,k,n);c,f,t=m.cf(x);a.enc(c,f,t);m.up(x)
  s.last=(L,0)
 def chaind(s,a,st):
  m=s.m(s.clv,(st.f,st.pg),8);x=a.tar(m.t);lev,c,f=m.find(x);a.dec(c,f,m.t);m.up(lev)
  m=s.m(s.cix,(lev,st.f,st.pg),16);x=a.tar(m.t);idx,c,f=m.find(x);a.dec(c,f,m.t);m.up(idx)
  m=s.m(s.cln,(lev,idx,st.f),255);x=a.tar(m.t);lb,c,f=m.find(x);a.dec(c,f,m.t);m.up(lb)
  L=lb+4;s.last=(L,0);return lev,idx,L
def addh(tab,d,i):
 if i+4<=len(d):
  k=d[i:i+4];a=tab.setdefault(k,[]);a.append(i)
  if len(a)>128:del a[:-128]
def rawm(d,i,tab):
 r=[]
 if i+4>len(d):return r
 for j in reversed(tab.get(d[i:i+4],())[-64:]):
  if j>=i:continue
  L=4;m=min(258,len(d)-i)
  while L<m and d[j+L]==d[i+L]:L+=1
  if L>=4:r.append((L,i-j))
 r.sort(reverse=True);return r[:12]
def addc(ch,st,pos):
 for k in st.keys():
  a=ch.setdefault(k,[]);a.append(pos)
  if len(a)>64:del a[:-64]
def chainm(d,i,ch,st):
 r=[]
 for lev,k in enumerate(st.keys()):
  for idx,j in enumerate(reversed(ch.get(k,())[-16:])):
   if j>=i:continue
   L=0;m=min(258,len(d)-i)
   while L<m and d[j+L]==d[i+L]:L+=1
   if L>=4:r.append((L,lev,idx,j))
 r.sort(reverse=True);return r[:16]
def lit_prefix(d):
 p=PPM();pre=[0.0]
 for b in d:
  pre.append(pre[-1]+p.cost(b));p.up(b)
 return pre
def upd_byte(ppm,st,ch,d,pos,b):
 addc(ch,st,pos);ppm.up(b,_pp(st));st.up(b)
def compress(d):
 global _S
 a=AC();ppm=PPM();st=GST();tok=TOK();ht={};ch={};pre=lit_prefix(d);i=0;n=len(d);cnt=[0,0,0,0];mb=[0,0,0,0];cl=[0,0,0,0,0,0,0,0]
 while i<n:
  best=(0.0,0,1,0,0,0)
  if i+4<=n:
   for L,D in rawm(d,i,ht):
    lit=(pre[i+L]-pre[i])+L*tok.evc(st,0);c=tok.evc(st,1)+tok.rawc(L,D)
    g=lit-c
    if g>0.5 and g>best[0]:best=(g,1,L,D,0,0)
   for L,lev,idx,j in chainm(d,i,ch,st):
    lit=(pre[i+L]-pre[i])+L*tok.evc(st,0);c=tok.evc(st,2)+tok.chainc(st,lev,idx,L)
    g=lit-c
    if g>0.5 and g>best[0]:best=(g,2,L,lev,idx,j)
  if st.ents:
   ne=min(64,len(st.ents))
   for k in range(1,ne+1):
    e=st.ents[-k]
    if d.startswith(e,i):
     L=len(e)
     if L>=4:
      lit=(pre[i+L]-pre[i])+L*tok.evc(st,0);c=tok.evc(st,3)+tok.ercptc(st,k)
      g=lit-c
      if g>0.5 and g>best[0]:best=(g,3,L,k,0,0)
     break
  if best[1]==0:
   cnt[0]+=1;mb[0]+=1;tok.eve(a,st,0);ppm.enc(a,d[i],_pp(st));addh(ht,d,i);addc(ch,st,i);st.up(d[i]);i+=1
  elif best[1]==1:
   _,_,L,D,_,_=best;cnt[1]+=1;mb[1]+=L;tok.eve(a,st,1);tok.rawe(a,L,D)
   for p in range(i,i+L):addh(ht,d,p);upd_byte(ppm,st,ch,d,p,d[p])
   i+=L
  elif best[1]==2:
   _,_,L,lev,idx,_=best;cnt[2]+=1;mb[2]+=L;cl[lev]+=1;tok.eve(a,st,2);tok.chaine(a,st,lev,idx,L)
   for p in range(i,i+L):addh(ht,d,p);upd_byte(ppm,st,ch,d,p,d[p])
   i+=L
  else:
   _,_,L,k,_,_=best;cnt[3]=cnt[3]+1 if len(cnt)>3 else 1;mb[3]=mb[3]+L if len(mb)>3 else L;tok.eve(a,st,3);tok.ercpte(a,st,k)
   for p in range(i,i+L):addh(ht,d,p);upd_byte(ppm,st,ch,d,p,d[p])
   i+=L
 out=struct.pack(">I",n)+a.fin();_S={"events":cnt,"bytes_by_mode":mb,"chain_levels":cl,"archive":len(out)};return out
def decompress(x):
 n=struct.unpack(">I",x[:4])[0];a=AC(x[4:]);ppm=PPM();st=GST();tok=TOK();ch={};o=bytearray()
 while len(o)<n:
  m=tok.evd(a,st)
  if m==0:
   b=ppm.dec(a,_pp(st));o.append(b);addc(ch,st,len(o)-1);st.up(b)
  elif m==1:
   L,D=tok.rawd(a);p=len(o)-D
   if p<0:raise ValueError("distance")
   for _ in range(L):
    b=o[p];p+=1;o.append(b);addc(ch,st,len(o)-1);ppm.up(b,_pp(st));st.up(b)
  elif m==2:
   lev,idx,L=tok.chaind(a,st);arr=ch.get(st.keys()[lev],())[-16:]
   if idx>=len(arr):raise ValueError("chain")
   p=arr[-1-idx]
   for _ in range(L):
    b=o[p];p+=1;o.append(b);addc(ch,st,len(o)-1);ppm.up(b,_pp(st));st.up(b)
  else:
   k=tok.ercptd(a,st)
   if k>len(st.ents):raise ValueError("ercpt")
   e=st.ents[-k];L=len(e)
   for kk in range(L):
    b=e[kk];o.append(b);addc(ch,st,len(o)-1);ppm.up(b,_pp(st));st.up(b)
 return bytes(o[:n])
def stats():return _S

_GC=compress
_GD=decompress
def compress(d):
 return _GC(oe(d))
def decompress(x):
 return od(_GD(x))
