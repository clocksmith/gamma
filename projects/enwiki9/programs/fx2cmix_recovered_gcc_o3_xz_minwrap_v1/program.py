import lzma,os,pathlib,subprocess,tempfile
P=pathlib.Path(__file__).resolve().parent
C=pathlib.Path(tempfile.gettempdir())/("fx2mw"+str(os.getpid()))
def _e():
 C.mkdir(exist_ok=True);b=C/"c";d=C/"d"
 if not b.exists():b.write_bytes(lzma.decompress((P/"cmix.xz").read_bytes()));b.chmod(493)
 if not d.exists():d.write_bytes(lzma.decompress((P/"english.dic.xz").read_bytes()))
 return b,d
def _r(f,x):
 b,d=_e()
 with tempfile.TemporaryDirectory() as td:
  q=pathlib.Path(td);i=q/"i";o=q/"o";i.write_bytes(x)
  subprocess.run([str(b),f,str(d),str(i),str(o)],cwd=q,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
  return o.read_bytes()
def compress(x):return _r("-c",x)
def decompress(x):return _r("-d",x)
