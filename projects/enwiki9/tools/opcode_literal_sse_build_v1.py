#!/usr/bin/env python3
"""Build an independently loadable parent plus literal-calibration mutation."""
import hashlib
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'programs/opcode_field_compact_v1/p'
MUTATION = 'lib/opcode_literal_sse_v1.py'
PARENT_SHA = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'
LOADER = '''import hashlib,lzma
from pathlib import Path
_root=Path(__file__).parent
_parts={name:(_root/name).read_bytes() for name in ('p','v')}
for name,digest in DIGESTS.items():
 if hashlib.sha256(_parts[name]).hexdigest()!=digest:raise ValueError('source identity')
def namespace(arm='D'):
 n={'__name__':'opcode_literal_sse_bundle'}
 exec(compile(lzma.decompress(_parts['p']),'<parent>','exec'),n)
 exec(compile(lzma.decompress(_parts['v']),'<literal-calibration>','exec'),n)
 return n['install'](n,_parts['p'],arm)
def compress(data):return namespace()['compress'](data)
def decompress(data):return namespace()['decompress'](data)
'''


def bundle(root=ROOT):
    parent = (root / PARENT).read_bytes()
    if hashlib.sha256(parent).hexdigest() != PARENT_SHA:
        raise ValueError('parent differs')
    mutation = (root / MUTATION).read_bytes()
    compile(mutation, '<literal-calibration>', 'exec')
    files = dict(p=parent, v=lzma.compress(mutation, format=lzma.FORMAT_ALONE, preset=6))
    files['program.py'] = LOADER.replace('DIGESTS', repr({name: hashlib.sha256(data).hexdigest()
                                                      for name, data in files.items()})).encode()
    return files


def write_bundle(output):
    files = bundle()
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    return {name: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) for name, data in files.items()}
