import functools,lzma,os,pathlib,subprocess,tempfile
P=pathlib.Path(__file__).parent;A=P/'source.tar.raw';F=[{'id':lzma.FILTER_LZMA2,'preset':9|lzma.PRESET_EXTREME}]
def _d(p):
 d=p.read_bytes()
 if d[:4]!=b'BPD1' or len(d)<5 or d[4]not in(0,1):raise ValueError('dictionary')
 x=b'';w=[]
 for r in d[5:].splitlines():
  if not r:raise ValueError('record')
  n=r[0]-32
  if n<0 or n>len(x):raise ValueError('prefix')
  x=x[:n]+r[1:];w.append(x)
 p.write_bytes(b'\n'.join(w)+(b'\n'if d[4]else b''))
@functools.lru_cache(1)
def _b():
 r=lzma.decompress(A.read_bytes(),format=lzma.FORMAT_RAW,filters=F)
 if r[:4]!=b'FCF1'or len(r)<6:raise ValueError('frame')
 i=4;n=int.from_bytes(r[i:i+2],'big');i+=2;d=pathlib.Path(tempfile.mkdtemp(prefix='c-'));s=set()
 for _ in range(n):
  if i+6>len(r):raise ValueError('record')
  a=int.from_bytes(r[i:i+2],'big');b=int.from_bytes(r[i+2:i+6],'big');i+=6;j=i+a;k=j+b
  if k>len(r):raise ValueError('payload')
  z=r[i:j].decode();p=pathlib.PurePosixPath(z)
  if not z or p.is_absolute()or'..'in p.parts or z in s:raise ValueError('path')
  s.add(z);o=d.joinpath(*p.parts);o.parent.mkdir(parents=True,exist_ok=True);o.write_bytes(r[j:k]);i=k
 if i!=len(r):raise ValueError('trailing')
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
