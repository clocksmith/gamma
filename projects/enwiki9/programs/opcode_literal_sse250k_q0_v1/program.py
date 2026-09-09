import hashlib,lzma
from pathlib import Path
_root=Path(__file__).parent
_parts={name:(_root/name).read_bytes() for name in ('p','v')}
for name,digest in {'p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8', 'v': '63e1c3baba782ab9e348481939e889e7a28d5472af6ba2f04d260e4a4003db85'}.items():
 if hashlib.sha256(_parts[name]).hexdigest()!=digest:raise ValueError('source identity')
def namespace(arm='D'):
 n={'__name__':'opcode_literal_sse_bundle'}
 exec(compile(lzma.decompress(_parts['p']),'<parent>','exec'),n)
 exec(compile(lzma.decompress(_parts['v']),'<literal-calibration>','exec'),n)
 return n['install'](n,_parts['p'],arm)
def compress(data):return namespace()['compress'](data)
def decompress(data):return namespace()['decompress'](data)
