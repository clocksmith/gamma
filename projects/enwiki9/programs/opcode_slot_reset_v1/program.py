import lzma
from pathlib import Path
_source=lzma.decompress(Path(__file__).with_name('p').read_bytes())
def namespace(arm='D'):
 if arm not in ('P','K','D'):raise ValueError('arm')
 n={'__name__':'compact_opcode_field'};exec(compile(_source,'<packed-codec>','exec'),n)
 if arm=='P':return n
 class State(n['GST']):
  def up(s,b):
   close=s.field.pending and b==2
   super().up(b)
   if arm=='D' and close:s.slot=0
 n['GST']=State
 return n
def compress(d,arm='D'):return namespace(arm)['compress'](d)
def decompress(d,arm='D'):return namespace(arm)['decompress'](d)
