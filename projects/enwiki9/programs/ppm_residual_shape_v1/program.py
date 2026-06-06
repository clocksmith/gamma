T=(b"</text>\n    </revision>\n  </page>\n  <page>\n",b"    </revision>\n  </page>\n  <page>\n",b"</text>\n    </revision>\n  </page>\n",b"</timestamp>\n      <contributor>\n",b"</id>\n      </contributor>\n      <minor />\n",b"</comment>\n      <text xml:space=\"preserve\">",b"      <text xml:space=\"preserve\">#REDIRECT [[",b"{{R from CamelCase}}</text>\n",b"</username>\n        <id>",b"    <revision>\n      <id>",b"</id>\n      <timestamp>",b"      </contributor>\n      <minor />\n",b"      <minor />\n      <comment>",b"  <page>\n",b"  </page>\n",b"    <title>",b"</title>\n",b"    <id>",b"</id>\n",b"    <revision>\n",b"    </revision>\n",b"      <id>",b"      <timestamp>",b"</timestamp>\n",b"      <contributor>\n",b"      </contributor>\n",b"        <username>",b"</username>\n",b"        <id>",b"        <ip>",b"</ip>\n",b"      <minor />\n",b"      <comment>",b"</comment>\n",b"      <text xml:space=\"preserve\">",b"</text>\n",b"<mediawiki ",b" xmlns=",b"http://www.mediawiki.org/xml/export-0.3/",b"<siteinfo>",b"</siteinfo>",b"<namespaces>",b"</namespaces>",b"<namespace key=\"",b"</namespace>",b" />",b"<page>",b"</page>",b"<revision>",b"</revision>",b"<contributor>",b"</contributor>",b"<text xml:space=\"preserve\">",b"</text>",b"<title>",b"</title>",b"<id>",b"</id>",b"<timestamp>",b"</timestamp>",b"<username>",b"</username>",b"<comment>",b"</comment>",b"<minor />",b"<ip>",b"</ip>",b"#REDIRECT [[",b"{{R from CamelCase}}",b"[[Category:",b"[[Image:",b"[[File:",b"[[",b"]]",b"{{",b"}}",b"&quot;",b"&lt;",b"&gt;",b"&amp;",b"http://",b"https://",b"Category:",b"Image:",b"File:",b"|thumb",b"|right",b"|left",b"=\"",b"\">")
TS=sorted(enumerate(T,1),key=lambda x:-len(x[1]));TD=dict(enumerate(T,1))
O=4;ST=32;FULL=1<<ST;HALF=FULL>>1;QTR=HALF>>1;TQ=QTR*3;LAST={}
def shape(d):
 o=bytearray();i=h=0;n=len(d)
 while i<n:
  if d[i]==0:o+=b"\0\xff";i+=1;continue
  for c,t in TS:
   if d.startswith(t,i):o.extend((0,c));i+=len(t);h+=1;break
  else:o.append(d[i]);i+=1
 return bytes(o),h
def unshape(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  b=d[i];i+=1
  if b:o.append(b)
  else:c=d[i];i+=1;o.extend(b"\0" if c==255 else TD[c])
 return bytes(o)
class BO:
 def __init__(s):s.o=bytearray();s.c=s.n=0
 def w(s,b):
  s.c=s.c*2|b;s.n+=1
  if s.n==8:s.o.append(s.c);s.c=s.n=0
 def f(s):
  if s.n:s.o.append(s.c<<(8-s.n))
  return bytes(s.o)
class BI:
 def __init__(s,d):s.d=d;s.i=s.c=s.n=0
 def r(s):
  if s.n==0:s.c=s.d[s.i] if s.i<len(s.d) else 0;s.i+=1;s.n=8
  s.n-=1;return(s.c>>s.n)&1
class AE:
 def __init__(s):s.l=0;s.h=FULL-1;s.p=0;s.b=BO()
 def e(s,b):
  s.b.w(b)
  while s.p:s.b.w(1-b);s.p-=1
 def y(s,c,f,t):
  r=s.h-s.l+1;s.h=s.l+r*(c+f)//t-1;s.l=s.l+r*c//t
  while 1:
   if s.h<HALF:s.e(0)
   elif s.l>=HALF:s.e(1);s.l-=HALF;s.h-=HALF
   elif s.l>=QTR and s.h<TQ:s.p+=1;s.l-=QTR;s.h-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1
 def f(s):s.p+=1;s.e(0 if s.l<QTR else 1);return s.b.f()
class AD:
 def __init__(s,d):
  s.l=0;s.h=FULL-1;s.b=BI(d);s.c=0
  for _ in range(ST):s.c=s.c*2|s.b.r()
 def t(s,total):return((s.c-s.l+1)*total-1)//(s.h-s.l+1)
 def y(s,c,f,t):
  r=s.h-s.l+1;s.h=s.l+r*(c+f)//t-1;s.l=s.l+r*c//t
  while 1:
   if s.h<HALF:pass
   elif s.l>=HALF:s.l-=HALF;s.h-=HALF;s.c-=HALF
   elif s.l>=QTR and s.h<TQ:s.l-=QTR;s.h-=QTR;s.c-=QTR
   else:break
   s.l<<=1;s.h=(s.h<<1)|1;s.c=s.c*2|s.b.r()
class P:
 def __init__(s):s.m={};s.t=bytearray()
 def tr(s,b):
  e=set()
  for o in range(O,-1,-1):
   if o>len(s.t):continue
   x=s.m.get(bytes(s.t[-o:]) if o else b"")
   if not x:continue
   it=[(a,n) for a,n in x.items() if a not in e]
   if not it:continue
   st=sum(n for _,n in it);cu=0;tt=st+len(it)
   for a,n in it:
    if a==b:yield cu,n,tt;return
    cu+=n
   yield st,len(it),tt
   for a,_ in it:e.add(a)
  r=[a for a in range(256) if a not in e];yield r.index(b),1,len(r)
 def up(s,b):
  for o in range(O+1):
   if o and o>len(s.t):continue
   k=bytes(s.t[-o:]) if o else b"";c=s.m.setdefault(k,{});c[b]=c.get(b,0)+1
  s.t.append(b)
  if len(s.t)>O:del s.t[0]
 def enc(s,d):
  a=AE()
  for b in d:
   for c,f,t in s.tr(b):a.y(c,f,t)
   s.up(b)
  return a.f()
 def dec(s,d,n):
  a=AD(d);out=bytearray()
  for _ in range(n):
   e=set()
   for o in range(O,-1,-1):
    if o>len(s.t):continue
    x=s.m.get(bytes(s.t[-o:]) if o else b"")
    if not x:continue
    it=[(a0,n0) for a0,n0 in x.items() if a0 not in e]
    if not it:continue
    st=sum(n0 for _,n0 in it);tt=st+len(it);v=a.t(tt)
    if v<st:
     cu=0
     for b,f in it:
      if v<cu+f:a.y(cu,f,tt);out.append(b);s.up(b);break
      cu+=f
     break
    a.y(st,len(it),tt)
    for b,_ in it:e.add(b)
   else:
    r=[b for b in range(256) if b not in e];v=a.t(len(r));b=r[v];a.y(v,1,len(r));out.append(b);s.up(b)
  return bytes(out)
def compress(data:bytes)->bytes:
 z,h=shape(data);p=P();body=p.enc(z);LAST.clear();LAST.update({"shape_bytes":len(z),"shape_hits":h,"contexts":len(p.m)});return b"PRS1"+len(z).to_bytes(4,"big")+body
def decompress(data:bytes)->bytes:
 if data[:4]!=b"PRS1":raise ValueError("bad archive")
 return unshape(P().dec(data[8:],int.from_bytes(data[4:8],"big")))
def stats()->dict:return dict(LAST)
