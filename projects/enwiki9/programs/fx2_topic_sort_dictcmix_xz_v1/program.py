import lzma,os,re,subprocess as s,tempfile
D=os.path.dirname(__file__);P=tempfile.gettempdir()+"/fx2ts"+str(os.getpid());B=P+"b";E=P+"d"
O=b"  <page>\n";C=b"  </page>\n"
def b():
 if not os.path.exists(B):open(B,"wb").write(lzma.open(D+"/cmix.xz").read());os.chmod(B,493)
 return B
def d():
 if not os.path.exists(E):s.run([b(),"-d",D+"/english.dic.cmix",E],check=1,stdout=s.DEVNULL,stderr=s.DEVNULL)
 return E
def r(a,z):
 with tempfile.TemporaryDirectory()as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(z);s.run([b(),a,d(),i,o],cwd=t,check=1,stdout=s.DEVNULL,stderr=s.DEVNULL);return open(o,"rb").read()
def f(p,x):
 m=re.search(x,p,re.S|re.I);return m.group(1)if m else b""
def n(x):return re.sub(rb"[^a-z0-9]+",b" ",x.lower()).strip()[:120]
def sp(z,u=0):
 a=z.find(O)
 if a<0:return None
 ps=[];i=a
 while 1:
  j=z.find(O,i)
  if j<0:break
  k=z.find(C,j)
  if k<0:break
  k+=len(C);ps.append(z[j:k]);i=k
 ids=[int(f(p,rb"<id>(\d+)</id>")or 10**30)for p in ps]
 if len(ps)<2 or len(ids)!=len(set(ids))or(not u and ids!=sorted(ids)):return None
 return z[:a],ps,z[i:],ids
def key(p):
 return n(f(p,rb"\[\[Category:([^\]\|\n]{1,96})")or f(p,rb"\{\{([^\|\}\n]{1,96})")or f(p,rb"<title>(.*?)</title>"))
def ordz(z):
 x=sp(z)
 if not x:return None
 h,ps,t,ids=x;o=sorted(range(len(ps)),key=lambda i:(key(ps[i]),ids[i]))
 if o==list(range(len(ps))):return None
 return h+b"".join(ps[i]for i in o)+t
def rez(z):
 x=sp(z,1)
 if not x:return z
 h,ps,t,ids=x;return h+b"".join(ps[i]for i in sorted(range(len(ps)),key=lambda i:ids[i]))+t
def compress(z):
 y=ordz(z)
 return b"T"+r("-c",y)if y else b"R"+r("-c",z)
def decompress(z):
 y=r("-d",z[1:])
 return rez(y)if z[:1]==b"T"else y
