import lzma,os,subprocess as s,tempfile as t
P=__file__[:-10];T=t.gettempdir()+"/f"+str(os.getpid());B=T+"b";D=T+"d";N=s.DEVNULL;E=os.path.exists;O=open
def b():
 if not E(B):O(B,"wb").write(lzma.open(P+"c").read());os.chmod(B,493)
 return B
def d():
 if not E(D):s.run([b(),"-d",P+"d",D],stdout=N,stderr=N)
 return D
def r(a,z):
 with t.TemporaryDirectory()as x:
  i=x+"/i";o=x+"/o";O(i,"wb").write(z);s.run([b(),a,d(),i,o],cwd=x,stdout=N,stderr=N);return O(o,"rb").read()
def compress(z):return r("-c",z)
def decompress(z):return r("-d",z)
