import os,pathlib,subprocess,tarfile,tempfile
P=pathlib.Path(__file__).parent
A=P/'nncp_cpu_source.tar.xz';B=None
F='-O3 -Wall -Wpointer-arith -fno-math-errno -fno-trapping-math -MMD -Wno-format-truncation -DCONFIG_VERSION=\\"2024-06-05\\" -DLIBNC_CONFIG_FULL'
def _b():
 global B
 if B is None:
  B=pathlib.Path(tempfile.mkdtemp(prefix='n-'))
  with tarfile.open(A,'r:xz') as t:t.extractall(B)
  subprocess.run(['make','-C',str(B),'-j2','CFLAGS='+F],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 e=os.environ.copy();q=e.get('LD_LIBRARY_PATH');e['LD_LIBRARY_PATH']=str(B)+((':'+q) if q else '')
 return B/'nncp',e
def _r(a,d):
 b,e=_b()
 with tempfile.TemporaryDirectory(prefix='n-') as t:
  t=pathlib.Path(t);i=t/'i';o=t/'o';i.write_bytes(d)
  subprocess.run([str(b),*a,str(i),str(o)],check=True,env=e,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  return o.read_bytes()
def compress(d):return _r(['--profile','enwik9','--batch_size','1','-T','4','--n_layer','5','--d_model','256','--d_inner','768','--preprocess','16384,512','c'],d)
def decompress(d):return _r(['d'],d)
