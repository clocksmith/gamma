import hashlib,lzma
from pathlib import Path
_packed=Path(__file__).with_name('p').read_bytes()
if hashlib.sha256(_packed).hexdigest()!='2d29f154a9df186caa7b547fa304820b6ceb6d675aef59005d7a1319febf3c64':raise ValueError('packed source identity')
_source=lzma.decompress(_packed)
def namespace(arm='D'):
 n={'__name__':'opcode_field_history_bundle'}
 exec(compile(_source,'<packed-codec>','exec'),n)
 return n['install'](n,arm)
def compress(d):return namespace()['compress'](d)
def decompress(d):return namespace()['decompress'](d)
