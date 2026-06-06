from __future__ import annotations
import re,subprocess
E=0;L=255
T=[b'<text xml:space="preserve">',b"</text>",b"<page>",b"</page>",b"<revision>",b"</revision>",b"<contributor>",b"</contributor>",b"<timestamp>",b"</timestamp>",b"<username>",b"</username>",b"<comment>",b"</comment>",b"<title>",b"</title>",b"<id>",b"</id>",b"<minor />",b"{{",b"}}",b"[[Category:",b"[[Image:",b"[[",b"]]",b"&quot;",b"&lt;",b"&gt;",b"&amp;",b"http://",b"https://",b"<ref",b"</ref>",b"|thumb",b"|right",b"|left",b"Category:",b"File:",b"Image:"]
S=sorted(enumerate(T,1),key=lambda x:len(x[1]),reverse=True)
D={i:t for i,t in enumerate(T,1)}
A=["xz","-q","-c","-T1","--check=crc32","--lzma2=preset=9e,dict=1024MiB"]
P=b"  <page>\n";Z=b"  </page>\n"
def en(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  if d[i]==E:o.extend((E,L));i+=1;continue
  for c,t in S:
   if d.startswith(t,i):o.extend((E,c));i+=len(t);break
  else:o.append(d[i]);i+=1
 return bytes(o)
def de(d):
 o=bytearray();i=0;n=len(d)
 while i<n:
  b=d[i]
  if b!=E:o.append(b);i+=1;continue
  if i+1>=n:raise ValueError("truncated opcode")
  c=d[i+1];o.append(E) if c==L else o.extend(D[c]);i+=2
 return bytes(o)
def xz(d):return subprocess.run(A,input=en(d),stdout=subprocess.PIPE,check=True).stdout
def ux(d):return de(subprocess.run(["xz","-q","-d","-c","--memlimit-decompress=0"],input=d,stdout=subprocess.PIPE,check=True).stdout)
def ps(d):
 f=d.find(P)
 if f<0:return None
 a=[];p=f
 while 1:
  s=d.find(P,p)
  if s<0:break
  e=d.find(Z,s)
  if e<0:break
  e+=len(Z);a.append(d[s:e]);p=e
 return d[:f],a,d[p:]
def pi(p,i=0):
 m=re.search(b"<id>(\\d+)</id>",p)
 return int(m.group(1)) if m else 10**18+i
def pf(p,r):
 m=re.search(r,p,re.S|re.I)
 return m.group(1) if m else b""
def pn(b):return re.sub(b"[^a-z0-9]+",b" ",b.lower()).strip()[:240]
def pt(p):
 r=pf(p,b"#REDIRECT\\s*\\[\\[([^\\]\\|\\n]{1,120})")
 if r:return b"~~Z~~"+r
 t=pf(p,b"<title>(.*?)</title>");k=t[-30:] if len(t)>30 else t
 c=re.findall(b"\\[\\[Category:([^\\]\\|\\n]{1,80})",p)
 if c:return b" ".join(sorted(c))+b" "+k
 return pf(p,b"\\{\\{([^\\|\\}\\n]{1,80})") or t
def po(d):
 z=ps(d)
 if not z:return None
 h,a,c=z;ids=[pi(p,i) for i,p in enumerate(a)]
 if not a or ids!=sorted(ids) or len(ids)!=len(set(ids)):return None
 q=sorted(range(len(a)),key=lambda i:(pn(pt(a[i])),ids[i]))
 return h+b"".join(a[i] for i in q)+c
def pr(d):
 z=ps(d)
 if not z:return d
 h,a,c=z;a.sort(key=pi);return h+b"".join(a)+c
def compress(d):
 r=xz(d);t=po(d)
 if t is not None:
  u=xz(t)
  if len(u)<len(r):r=u
 return r
def decompress(d):return pr(ux(d))
