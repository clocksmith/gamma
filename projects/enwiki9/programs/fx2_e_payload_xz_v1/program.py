import lzma,os,stat,struct,subprocess,tempfile
D=os.path.dirname(__file__)
C=None
def cmix():
 global C
 if C is None:C=lzma.open(D+"/cmix.xz").read()
 return C
def put(p,b,x=False):
 open(p,"wb").write(b)
 if x:os.chmod(p,0o755)
def split():
 c=cmix();ds,osz,_=struct.unpack("<iii",c[-12:]);bs=len(c)-ds-osz-12
 return c[:bs],c[bs:bs+ds],ds
def compress(z):
 with tempfile.TemporaryDirectory()as t:
  b=t+"/cmix";i=t+"/i";o=t+"/p";put(b,cmix(),1);put(i,z)
  subprocess.run([b,"-e",i,o],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return open(o,"rb").read()
def decompress(z):
 with tempfile.TemporaryDirectory()as t:
  b,d,ds=split();a=t+"/archive9"
  put(a,b+d+z+struct.pack("<iii",ds,0,len(z)),1)
  subprocess.run([a],cwd=t,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  p=t+"/enwik9_uncompressed"
  if not os.path.exists(p):p=t+"/enwik9_restored"
  return open(p,"rb").read()
