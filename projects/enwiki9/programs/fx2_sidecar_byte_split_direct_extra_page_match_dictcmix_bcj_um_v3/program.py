import lzma,os,subprocess as s,tempfile as t
P=os.path.dirname(__file__)+"/";T=t.gettempdir()+"/f"+str(os.getpid());B=T+"b";D=T+"d"
def b():
 if not os.path.exists(B):open(B,"wb").write(lzma.open(P+"c").read());os.chmod(B,493)
 return B
def d():
 if not os.path.exists(D):s.run([b(),"-d",P+"d",D],check=1,stdout=s.DEVNULL,stderr=s.DEVNULL)
 return D
def r(a,z):
 with t.TemporaryDirectory()as x:
  i=x+"/i";o=x+"/o";open(i,"wb").write(z);s.run([b(),a,d(),i,o],cwd=x,check=1,stdout=s.DEVNULL,stderr=s.DEVNULL);return open(o,"rb").read()
def compress(z):return r("-c",z)
def decompress(z):return r("-d",z)
