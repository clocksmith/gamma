import gzip,os,subprocess,tempfile
D=os.path.dirname(__file__)
B=None
def _b():
 global B
 if B and os.path.exists(B):return B
 f,p=tempfile.mkstemp();os.close(f)
 with gzip.open(D+"/cmix.bin.gz","rb")as g,open(p,"wb")as o:o.write(g.read())
 os.chmod(p,0o755);B=p;return p
def _r(a,d):
 with tempfile.TemporaryDirectory()as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(d)
  subprocess.run([_b(),a,i,o],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return open(o,"rb").read()
def compress(d):return _r("-c",d)
def decompress(d):return _r("-d",d)
