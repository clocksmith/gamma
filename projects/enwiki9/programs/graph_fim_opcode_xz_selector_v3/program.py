import re,subprocess,bz2
X=["xz","-q","-c","-T1","--check=crc32","--lzma2=preset=9e,dict=1024MiB"]
U=["xz","-q","-d","-c","--memlimit-decompress=0"]
O=re.compile(rb"<title>|<id>|<timestamp>|<username>|<comment>|<text xml:space=\"preserve\">")
F={b"<title>":(1,b"</title>"),b"<id>":(2,b"</id>"),b"<timestamp>":(3,b"</timestamp>"),b"<username>":(4,b"</username>"),b"<comment>":(5,b"</comment>"),b'<text xml:space="preserve">':(6,b"</text>")}
W=re.compile(rb"[A-Za-z]{3,32}")
E=2;B=128
T=b"""<text xml:space="preserve">
</text>
<page>
</page>
<revision>
</revision>
<contributor>
</contributor>
<timestamp>
</timestamp>
<username>
</username>
<comment>
</comment>
<title>
</title>
<id>
</id>
<minor />
{{
}}
[[Category:
[[Image:
[[
]]
&quot;
&lt;
&gt;
&amp;
http://
https://
<ref
</ref>
|thumb
|right
|left
Category:
File:
Image:
|url=
|title=
|date=
|accessdate=
|publisher=
|author=
|first=
|last=
{{ActingFilmography-movie 
== External links ==
|align=
{{note
{{succession box
[[simple:
{{cite book
{{ThisDateInRecentYears
{{ref
{{IPA
[[image:
== See also ==
{{cite web 
{{cite web
{{main
== References ==
{{cite book 
{{flagicon
[[Special:
{{succession box """.splitlines()
T.sort(key=len,reverse=True)
def x(d):return subprocess.run(X,input=d,stdout=subprocess.PIPE,check=True).stdout
def ux(d):return subprocess.run(U,input=d,stdout=subprocess.PIPE,check=True).stdout
def pv(o,n):
 while n>127:o.append(n&127|128);n>>=7
 o.append(n)
def gv(d,p):
 n=s=0
 while 1:
  b=d[p];p+=1;n|=(b&127)<<s
  if b<128:return n,p
  s+=7
def em(o,c):
 if 0 not in c:o.extend(c);return
 for b in c:o.extend((0,0)) if b==0 else o.append(b)
def pg(d):
 s=bytearray();c=[[] for _ in range(7)];p=0
 for m in O.finditer(d):
  if m.start()<p:continue
  k,z=F[m.group(0)];e=d.find(z,m.end())
  if e<0:continue
  em(s,d[p:m.end()]);s.extend((0,k));c[k].append(d[m.end():e]);p=e
 em(s,d[p:]);o=bytearray(b"GF1");pv(o,len(s));o.extend(s)
 for k in range(1,7):
  pv(o,len(c[k]))
  for v in c[k]:pv(o,len(v));o.extend(v)
 return bytes(o)
def ug(d):
 if d[:3]!=b"GF1":raise ValueError("graph")
 p=3;n,p=gv(d,p);s=d[p:p+n];p+=n;c=[[] for _ in range(7)]
 for k in range(1,7):
  q,p=gv(d,p)
  for _ in range(q):n,p=gv(d,p);c[k].append(d[p:p+n]);p+=n
 i=[0]*7;o=bytearray();p=0
 while p<len(s):
  b=s[p]
  if b:o.append(b);p+=1;continue
  k=s[p+1];p+=2
  if k==0:o.append(0)
  else:j=i[k];o.extend(c[k][j]);i[k]=j+1
 return bytes(o)
def pt(d):
 o=bytearray();i=0
 while i<len(d):
  if d[i]==0:o.extend((0,255));i+=1;continue
  for n,t in enumerate(T,1):
   if d.startswith(t,i):o.extend((0,n));i+=len(t);break
  else:o.append(d[i]);i+=1
 return bytes(o)
def ut(d):
 o=bytearray();i=0
 while i<len(d):
  b=d[i]
  if b:o.append(b);i+=1;continue
  n=d[i+1];i+=2
  if n==255:o.append(0)
  elif 0<n<=len(T):o.extend(T[n-1])
  else:raise ValueError("token")
 return bytes(o)
def words(d):
 c={}
 for m in W.finditer(d):w=m.group(0);c[w]=c.get(w,0)+1
 a=[]
 for w,f in c.items():
  z=f*(len(w)-1)-len(w)-1
  if z>0:a.append((-z,w))
 a.sort();return [w for _,w in a[:128]]
def esc(d):
 if not any(b==E or b>=B for b in d):return d
 o=bytearray()
 for b in d:
  if b==E or b>=B:o.append(E)
  o.append(b)
 return bytes(o)
def pw(d):
 ws=words(d);o=bytearray(b"WD1");pv(o,len(ws))
 for w in ws:pv(o,len(w));o.extend(w)
 if not ws:o.extend(esc(d));return bytes(o)
 mp={w:bytes([B+i]) for i,w in enumerate(ws)};pat=re.compile(b"|".join(re.escape(w) for w in ws));p=0
 for m in pat.finditer(d):o.extend(esc(d[p:m.start()]));o.extend(mp[m.group(0)]);p=m.end()
 o.extend(esc(d[p:]));return bytes(o)
def uw(d):
 if d[:3]!=b"WD1":raise ValueError("words")
 p=3;n,p=gv(d,p);ws=[]
 for _ in range(n):q,p=gv(d,p);ws.append(d[p:p+q]);p+=q
 o=bytearray()
 while p<len(d):
  b=d[p];p+=1
  if b==E:o.append(d[p]);p+=1
  elif b>=B:o.extend(ws[b-B])
  else:o.append(b)
 return bytes(o)
def compress(d):
 q=pw(pt(pg(d)));r=b"R"+x(d);g=b"O"+x(q);b=b"B"+bz2.compress(q,9)
 return min((r,g,b),key=len)
def decompress(d):
 m=d[:1]
 return ux(d[1:]) if m==b"R" else ug(ut(uw(bz2.decompress(d[1:]) if m==b"B" else ux(d[1:]))))
