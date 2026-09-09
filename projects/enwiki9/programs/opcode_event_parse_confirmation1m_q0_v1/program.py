import hashlib,lzma
from pathlib import Path
_base=Path(__file__).parent
_parts={name:(_base/name).read_bytes() for name in ('p','v')}
for name,digest in {'p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8', 'v': 'd9c4d28792936916715d37b1ace4572c0cdc2cc106498077418a3f32b66de48b'}.items():
 if hashlib.sha256(_parts[name]).hexdigest()!=digest:raise ValueError('source identity')
def namespace(arm='D'):
 n={'__name__':'opcode_event_parse_bundle'}
 exec(compile(lzma.decompress(_parts['p']),'<parent>','exec'),n)
 exec(compile(lzma.decompress(_parts['v']),'<encoder-correction>','exec'),n)
 return n['install'](n,_parts['p'],arm)
def compress(data):return namespace()['compress'](data)
def decompress(data):return namespace('P')['decompress'](data)
