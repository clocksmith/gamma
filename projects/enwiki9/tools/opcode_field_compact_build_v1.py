#!/usr/bin/env python3
"""Build only a new compact field-repair source bundle from authenticated inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT / 'programs/opcode_field_confirmation1m_q0_v1'
PARENT_SHA = '3e9c9ed25997ad10bac94575fb3da5009530ba04fa961da14a016fe89eec9a15'
EXPANDED_SHA = '4f37b0da3fd7642533ca8d2ac865019c218c2508482aba85f9a2c1d35cde6cb4'
LOADER = '''import lzma
from pathlib import Path
_source=lzma.decompress(Path(__file__).with_name('p').read_bytes())
def namespace():
 n={'__name__':'compact_opcode_field'};exec(compile(_source,'<packed-codec>','exec'),n);return n
def compress(d):return namespace()['compress'](d)
def decompress(d):return namespace()['decompress'](d)
'''

# The retained arithmetic, predictor, frontend and search bodies precede this
# overlay. Every change here implements the already measured D policy or its
# bounds; optional observers live outside the counted runtime.
OVERLAY = '''
_limit=0
_capture=lambda *args:None
def require(ok,message):
 if not ok:raise ValueError(message)
class Field:
 def __init__(s):s.f=0;s.pending=False
 def up(s,b):
  if s.pending:
   require(b==255 or 1<=b<=39,'unknown opcode')
   if b in (15,17,9,11,13,1):s.f={15:1,17:2,9:3,11:4,13:5,1:6}[b]
   elif b in (16,18,10,12,14,2):s.f=0
   s.pending=False
  elif b==0:s.pending=True
_GST=GST
class GST(_GST):
 def __init__(s):
  super().__init__();s.modeled_f=s.f;s.field=Field();s.position=0
 def up(s,b):
  require(s.position<_limit,'modeled output bound')
  s.f=s.modeled_f;super().up(b);s.modeled_f=s.f
  s.field.up(b);s.f=s.field.f;s.position+=1
_AC=AC
class AC(_AC):
 def __init__(s,d=None):
  super().__init__(d);s.payload=d;s.shadow=_AC() if d is not None else None
 def dec(s,c,f,t):
  s.shadow.enc(c,f,t);super().dec(c,f,t)
  require((s.l,s.h)==(s.shadow.l,s.shadow.h),'arithmetic interval')
def _finish(a,lit,st,tok,ch,d):
 require(len(d)==st.position==_limit,'modeled terminal length')
 require(not st.field.pending,'truncated opcode')
 _capture(a,lit,st,tok,ch,d)
 if a.shadow is not None:require(a.shadow.fin()==a.payload,'noncanonical arithmetic payload')
def compress(d):
 global _limit
 require(type(d) is bytes and len(d)<=1000000,'raw input bound')
 enc=oe(d);_limit=len(enc)
 require(_limit<=2*len(d),'opcode expansion bound')
 out=struct.pack('>II',len(d),len(enc))+compress_inner(enc)
 require(len(out)<=33554432,'archive bound')
 return out
def decompress(x):
 global _limit
 require(type(x) is bytes and 9<=len(x)<=33554432,'archive bound')
 n,m=struct.unpack('>II',x[:8]);_limit=m
 require(n<=1000000 and m<=2*n,'declared output bound')
 try:raw=od(decompress_inner(x[8:],m))
 except (IndexError,KeyError,ZeroDivisionError) as e:raise ValueError('malformed native archive') from e
 require(len(raw)==n,'raw output length')
 return raw
'''


def source() -> bytes:
    packed = (PARENT / 'p').read_bytes()
    if hashlib.sha256(packed).hexdigest() != PARENT_SHA:
        raise ValueError('parent packed source changed')
    raw = lzma.decompress(packed, format=lzma.FORMAT_ALONE)
    if hashlib.sha256(raw).hexdigest() != EXPANDED_SHA:
        raise ValueError('parent expanded source changed')
    text = raw.decode('utf-8')
    replacements = {
        ' out=a.fin();_S=': ' _finish(a,lit,st,tok,ch,d)\n out=a.fin();_S=',
        ' return bytes(o[:n])': ' _finish(a,lit,st,tok,ch,bytes(o))\n return bytes(o[:n])',
    }
    for before, after in replacements.items():
        if text.count(before) != 1:
            raise ValueError('parent terminal site changed')
        text = text.replace(before, after)
    expanded = (text + OVERLAY).encode('utf-8')
    compile(expanded, '<compact-opcode-build>', 'exec')
    return expanded


def bundle() -> dict[str, bytes]:
    return {'p': lzma.compress(source(), format=lzma.FORMAT_ALONE, preset=6),
            'program.py': LOADER.encode('utf-8')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    files = bundle()
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (args.output / name).open('xb') as stream:
            stream.write(data)
    print(json.dumps({'members': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                                  for name, data in files.items()},
                      'local_source_bytes': sum(map(len, files.values())),
                      'expanded_source_sha256': hashlib.sha256(source()).hexdigest(),
                      'complete_package_bytes': None}, sort_keys=True))


if __name__ == '__main__':
    main()
