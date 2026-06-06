import lzma,os,subprocess as s,tempfile
D=os.path.dirname(__file__)
P=tempfile.gettempdir()+"/fx2xd"+str(os.getpid());B=P+"b";E=P+"d"
def b():
 if not os.path.exists(B):open(B,"wb").write(lzma.open(D+"/cmix.xz").read());os.chmod(B,0o755)
 return B
def d():
 if not os.path.exists(E):s.run([b(),"-d",D+"/english.dic.cmix",E],check=1,stdout=s.DEVNULL,stderr=s.DEVNULL)
 return E
def r(a,z):
 with tempfile.TemporaryDirectory()as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(z)
  s.run([b(),a,d(),i,o],cwd=t,check=1,stdout=s.DEVNULL,stderr=s.DEVNULL)
  return open(o,"rb").read()
def compress(z):return r("-c",z)
def decompress(z):return r("-d",z)
