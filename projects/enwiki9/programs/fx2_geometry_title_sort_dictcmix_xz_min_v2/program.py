import lzma,os,re,subprocess as s,tempfile as t
P=__file__[:-10];T=t.gettempdir()+"/g"+str(os.getpid());B=T+"b";D=T+"d";O=b"  <page>\n";C=b"  </page>\n";N=s.DEVNULL;R=s.run;A=os.path.exists;S=sorted;G=range;L=len;J=b"".join;Q=open
def b():
 if not A(B):Q(B,"wb").write(lzma.open(P+"c").read());os.chmod(B,493)
 return B
def d():
 if not A(D):R([b(),"-d",P+"d",D],stdout=N,stderr=N)
 return D
def r(a,z):
 with t.TemporaryDirectory()as q:
  i=q+"/i";o=q+"/o";Q(i,"wb").write(z);R([b(),a,d(),i,o],cwd=q,stdout=N,stderr=N);return Q(o,"rb").read()
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
 if c:return n(b"c "+b" ".join(S(c))+b" t "+t[:80])
 i=f(p,rb"\{\{\s*(infobox[^|}\n]{0,80})")
 if i:return n(b"i "+i+b" t "+t)
 return n(b"x "+(f(p,rb"\{\{([^|}\n]{1,80})")or t)+b" t "+t)
def o(z):
 x=sp(z)
 if not x:return
 h,p,t,v=x;q=S(G(L(p)),key=lambda i:(k(p[i]),v[i]))
 if q!=S(G(L(p))):return h+J(p[i]for i in q)+t
def e(z):
 x=sp(z,1)
 if not x:return z
 h,p,t,v=x;return h+J(p[i]for i in S(G(L(p)),key=lambda i:v[i]))+t
def compress(z):
 y=o(z);return b"G"+r("-c",y)if y else b"R"+r("-c",z)
def decompress(z):
 y=r("-d",z[1:]);return e(y)if z[:1]==b"G"else y
