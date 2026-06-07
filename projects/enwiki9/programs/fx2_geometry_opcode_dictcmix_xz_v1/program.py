import lzma,re,subprocess as s,tempfile as t
from os import path,chmod,getpid
D=path.dirname(__file__);P=t.gettempdir()+"/go%d"%getpid();B,E=P+"b",P+"d";O,C=b"  <page>\n",b"  </page>\n";N=s.DEVNULL;R=s.run;A=path.exists;S=sorted;G=range;L=len;J=b"".join;K=dict(check=1,stdout=N,stderr=N)
T=[b'<text xml:space="preserve">',b"</text>",b"<page>",b"</page>",b"<revision>",b"</revision>",b"<contributor>",b"</contributor>",b"<timestamp>",b"</timestamp>",b"<username>",b"</username>",b"<comment>",b"</comment>",b"<title>",b"</title>",b"<id>",b"</id>",b"<minor />",b"{{",b"}}",b"[[Category:",b"[[Image:",b"[[File:",b"[[",b"]]",b"&quot;",b"&lt;",b"&gt;",b"&amp;",b"http://",b"https://",b"<ref",b"</ref>",b"|thumb",b"|right",b"|left",b"Category:",b"File:",b"Image:"]
U=S(enumerate(T,1),key=lambda x:L(x[1]),reverse=1)
def b():
 if not A(B):open(B,"wb").write(lzma.open(D+"/cmix.xz").read());chmod(B,493)
 return B
def d():
 if not A(E):R([b(),"-d",D+"/english.dic.cmix",E],**K)
 return E
def r(a,z):
 with t.TemporaryDirectory()as q:
  i=q+"/i";o=q+"/o";open(i,"wb").write(z);R([b(),a,d(),i,o],cwd=q,**K);return open(o,"rb").read()
def f(p,x):
 m=re.search(x,p,18);return m.group(1)if m else b""
def sp(z,u=0):
 a=z.find(O);p=[];i=a
 if a<0:return
 while 1:
  j=z.find(O,i);k=z.find(C,j)
  if j<0 or k<0:break
  k+=L(C);p+=z[j:k],;i=k
 v=[int(f(x,rb"<id>(\d+)</id>")or 1<<99)for x in p]
 if L(p)>1 and L(v)==L(set(v))and(u or v==S(v)):return z[:a],p,z[i:],v
def n(v):return re.sub(rb"[^a-z0-9]+",b" ",v.lower()).strip()[:240]
def k(p):
 t=f(p,rb"<title>(.*?)</title>");r=f(p,rb"#redirect\s*\[\[([^]|\n]{1,140})")
 if r:return n(b"z "+r)
 c=re.findall(rb"\[\[Category:([^]|\n]{1,100})",p,2)
 if c:return n(b"c "+b" ".join(S(c))+b" t "+t[:40])
 i=f(p,rb"\{\{\s*(infobox[^|}\n]{0,80})")
 if i:return n(b"i "+i)
 return n(b"x "+(f(p,rb"\{\{([^|}\n]{1,80})")or t))
def o(z):
 x=sp(z)
 if not x:return
 h,p,t,v=x;q=S(G(L(p)),key=lambda i:(k(p[i]),v[i]))
 if q!=list(G(L(p))):return h+J(p[i]for i in q)+t
def e(z):
 x=sp(z,1)
 if not x:return z
 h,p,t,v=x;return h+J(p[i]for i in S(G(L(p)),key=lambda i:v[i]))+t
def te(z):
 o=bytearray();i=0
 while i<L(z):
  if z[i]==0:o.extend((0,255));i+=1;continue
  for c,w in U:
   if z.startswith(w,i):o.extend((0,c));i+=L(w);break
  else:o.append(z[i]);i+=1
 return bytes(o)
def td(z):
 o=bytearray();i=0
 while i<L(z):
  c=z[i];i+=1
  if c:o.append(c);continue
  c=z[i];i+=1
  if c==255:o.append(0)
  else:o.extend(T[c-1])
 return bytes(o)
def compress(z):
 y=o(z)
 if not y:return b"R"+r("-c",z)
 a=b"G"+r("-c",y);q=b"O"+r("-c",te(y))
 return a if L(a)<=L(q)else q
def decompress(z):
 y=r("-d",z[1:])
 if z[:1]==b"O":y=td(y)
 return e(y)if z[:1]in b"GO"else y
