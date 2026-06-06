import lzma,os,subprocess,tempfile
D=os.path.dirname(__file__)
B=None
def b():
 global B
 if B and os.path.exists(B):return B
 f,p=tempfile.mkstemp();os.close(f);open(p,"wb").write(lzma.open(D+"/cmix.xz").read());os.chmod(p,0o755);B=p;return p
def r(a,z):
 with tempfile.TemporaryDirectory()as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(z)
  subprocess.run([b(),a,i,o],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return open(o,"rb").read()
def compress(z):return r("-c",z)
def decompress(z):return r("-d",z)
