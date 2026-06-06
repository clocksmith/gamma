import lzma,os,re,subprocess as s,tempfile
D=os.path.dirname(__file__);P=tempfile.gettempdir()+"/fx2gt"+str(os.getpid());B=P+"b";E=P+"d";O=b"  <page>\n";C=b"  </page>\n"
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
def sp(z,u=0):
 a=z.find(O);ps=[];i=a
 if a<0:return
 while 1:
  j=z.find(O,i);k=z.find(C,j)
  if j<0 or k<0:break
  k+=len(C);ps+=z[j:k],;i=k
 ids=[int(f(p,rb"<id>(\d+)</id>")or 10**30)for p in ps]
 if len(ps)>1 and len(ids)==len(set(ids))and(u or ids==sorted(ids)):return z[:a],ps,z[i:],ids
def n(v):
 return re.sub(rb"[^a-z0-9]+",b" ",v.lower()).strip()[:240]
def k(p):
 t=f(p,rb"<title>(.*?)</title>");r=f(p,rb"#redirect\s*\[\[([^\]\|\n]{1,140})")
 if r:return n(b"z "+r)
 c=re.findall(rb"\[\[Category:([^\]\|\n]{1,100})",p,re.I)
 if c:return n(b"c "+b" ".join(sorted(c))+b" t "+t[:80])
 i=f(p,rb"\{\{\s*(infobox[^\|\}\n]{0,80})")
 if i:return n(b"i "+i+b" t "+t)
 return n(b"x "+(f(p,rb"\{\{([^\|\}\n]{1,80})")or t)+b" t "+t)
def o(z):
 x=sp(z)
 if not x:return
 h,p,t,ids=x;q=sorted(range(len(p)),key=lambda i:(k(p[i]),ids[i]))
 return None if q==list(range(len(p)))else h+b"".join(p[i]for i in q)+t
def e(z):
 x=sp(z,1)
 if not x:return z
 h,p,t,ids=x;return h+b"".join(p[i]for i in sorted(range(len(p)),key=lambda i:ids[i]))+t
def compress(z):
 y=o(z);return b"G"+r("-c",y)if y else b"R"+r("-c",z)
def decompress(z):
 y=r("-d",z[1:]);return e(y)if z[:1]==b"G"else y
