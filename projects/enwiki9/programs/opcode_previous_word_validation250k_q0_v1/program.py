import lzma
from pathlib import Path
_source=lzma.decompress(Path(__file__).with_name('p').read_bytes())
def namespace(arm='D'):
 if arm not in ('P','K','D','S'):raise ValueError('arm')
 n={'__name__':'compact_previous_word','_arm':arm};exec(compile(_source,'<packed-codec>','exec'),n);return n
def compress(d):return namespace()['compress'](d)
def decompress(d):return namespace()['decompress'](d)
