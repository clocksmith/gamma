import lzma
from pathlib import Path
_source=lzma.decompress(Path(__file__).with_name('p').read_bytes())
def namespace(arm='D'):
 if arm not in ('P','K','D'):raise ValueError('arm')
 n={'__name__':'compact_opcode_field'};exec(compile(_source,'<packed-codec>','exec'),n)
 if arm=='P':return n
 base=n['GST'];raw=n['_GST']
 class State(base):
  def __init__(s):
   super().__init__();s.modeled_slot=s.slot;s.raw_state=raw();s.raw_pending=False;s.raw_position=0
  def up(s,b):
   s.slot=s.modeled_slot;super().up(b);s.modeled_slot=s.slot
   if s.raw_pending:
    part=b'\0' if b==255 else n['TD'][b];s.raw_pending=False
   elif b==0:part=b'';s.raw_pending=True
   else:part=bytes((b,))
   for c in part:s.raw_state.up(c);s.raw_position+=1
   if arm=='D':s.slot=s.raw_state.slot
 n['GST']=State
 return n
def compress(d,arm='D'):return namespace(arm)['compress'](d)
def decompress(d,arm='D'):return namespace(arm)['decompress'](d)
