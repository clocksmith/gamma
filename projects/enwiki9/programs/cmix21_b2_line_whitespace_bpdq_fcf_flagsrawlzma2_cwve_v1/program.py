import functools,lzma,os,pathlib,subprocess,tempfile
P=pathlib.Path(__file__).parent;A=P/'source.tar.raw';F=[{'id':lzma.FILTER_LZMA2,'preset':9|lzma.PRESET_EXTREME}]
def _d(p):
 d=p.read_bytes();x=b'';w=[]
 for r in d[5:].splitlines():n=r[0]-32;x=x[:n]+r[1:];w.append(x)
 p.write_bytes(b'\n'.join(w)+(b'\n'if d[4]else b''))
@functools.lru_cache(1)
def _b():
 r=lzma.decompress(A.read_bytes(),format=lzma.FORMAT_RAW,filters=F);i=4;n=int.from_bytes(r[i:i+2],'big');i+=2;d=pathlib.Path(tempfile.mkdtemp(prefix='c-'))
 for _ in range(n):
  a=int.from_bytes(r[i:i+2],'big');b=int.from_bytes(r[i+2:i+6],'big');i+=6;j=i+a;k=j+b;z=r[i:j].decode();o=d/z;o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(r[j:k]);i=k
 x=d/'cmix21';_d(x/'english.dic')
 subprocess.run(['make','-C',str(x),'cmix','CXX=g++','LFLAGS='+(x/'.gamma_lflags').read_text()],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 return x/'cmix',x/'english.dic'
def _r(d,m):
 b,q=_b()
 with tempfile.TemporaryDirectory(prefix='c-')as t:
  t=pathlib.Path(t);i=t/'i';o=t/'o';i.write_bytes(d);e=os.environ.copy();e.setdefault('CMIX_MMAP_ALLOC','1');e.setdefault('CMIX_MMAP_DIR',str(t))
  subprocess.run([str(b),m,str(q),str(i),str(o)],cwd=t,env=e,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return o.read_bytes()
def compress(d):return _r(d,'-t')
def decompress(d):return _r(d,'-d')
