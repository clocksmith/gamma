import lzma,os,subprocess as s,tempfile
p=__file__[:-10];c=tempfile.gettempdir()+"/fx2d"+str(os.getpid())
def e():
 os.makedirs(c,exist_ok=1);b=c+"/c";d=c+"/d"
 if not os.path.exists(b):open(b,"wb").write(lzma.decompress(open(p+"cmix.xz","rb").read()));os.chmod(b,493)
 if not os.path.exists(d):open(d,"wb").write(lzma.decompress(open(p+"english.dic.xz","rb").read()))
 return b,d
def r(f,x):
 b,d=e()
 with tempfile.TemporaryDirectory() as t:
  i=t+"/i";o=t+"/o";open(i,"wb").write(x);s.run([b,f,d,i,o],cwd=t,stdout=s.DEVNULL,stderr=s.DEVNULL,check=1);return open(o,"rb").read()
def compress(x):return r("-c",x)
def decompress(x):return r("-d",x)
