import hashlib,lzma
from pathlib import Path
_root=Path(__file__).parent
_parts={name:(_root/name).read_bytes() for name in ('p','v')}
for name,digest in {'p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8', 'v': '2415dc99d1338ab9d50f189070144fdf0d54c751e091e2b7a307eaf2e682481b'}.items():
 if hashlib.sha256(_parts[name]).hexdigest()!=digest:raise ValueError('source identity')
def namespace(arm='D'):
 n={'__name__':'opcode_previous_word_bundle'}
 exec(compile(lzma.decompress(_parts['p']),'<parent>','exec'),n)
 exec(compile(lzma.decompress(_parts['v']),'<previous-word>','exec'),n)
 return n['install'](n,_parts['p'],arm)
def compress(data):return namespace()['compress'](data)
def decompress(archive):return namespace()['decompress'](archive)
