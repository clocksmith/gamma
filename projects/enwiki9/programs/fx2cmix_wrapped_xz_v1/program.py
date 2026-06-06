import lzma,os,subprocess,tempfile
D=os.path.dirname(__file__)
B=E=None
def x(n,e):
 f,p=tempfile.mkstemp();os.close(f);open(p,"wb").write(lzma.open(D+"/"+n+".xz").read())
 if e:os.chmod(p,0o755)
 return p
def b():
 global B
 if B and os.path.exists(B):return B
 B=x("cmix",1);return B
def d():
 global E
 if E and os.path.exists(E):return E
 E=x("english.dic",0);return E
def r(a,z):
 with tempfile.TemporaryDirectory()as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(z)
  subprocess.run([b(),a,d(),i,o],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return open(o,"rb").read()
def compress(z):return r("-c",z)
def decompress(z):return r("-d",z)
