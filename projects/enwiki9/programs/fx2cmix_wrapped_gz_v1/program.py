import gzip,os,subprocess,tempfile
H=os.path.dirname(__file__)
B=C=None
def _x(n,e=0):
 global B,C
 p=B if n=="cmix" else C
 if p and os.path.exists(p):return p
 f,p=tempfile.mkstemp();os.close(f)
 with gzip.open(H+"/"+n+".gz","rb")as a,open(p,"wb")as b:b.write(a.read())
 if e:os.chmod(p,0o755)
 if n=="cmix":B=p
 else:C=p
 return p
def _r(m,d):
 with tempfile.TemporaryDirectory()as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(d)
  subprocess.run([_x("cmix",1),m,_x("english.dic"),i,o],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return open(o,"rb").read()
def compress(d):return _r("-c",d)
def decompress(d):return _r("-d",d)
