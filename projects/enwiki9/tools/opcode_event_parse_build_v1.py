#!/usr/bin/env python3
"""Relocatable bundle of the unchanged parent and measured encoder correction."""
import hashlib
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    'programs/opcode_field_compact_v1/p': '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8',
    'lib/opcode_literal_event_cost_v1.py': 'ad49a96b20d6505514b4a5224018729bda90c86aa0f108cfbfdb28df8c8cb697',
    'lib/opcode_event_parse_v1.py': '388a87ed3155fa2f3db6dff5d6a87c4eb6d9e34472facdd36b883552a5d92437',
}
LOADER = '''import hashlib,lzma
from pathlib import Path
_base=Path(__file__).parent
_parts={name:(_base/name).read_bytes() for name in ('p','v')}
for name,digest in DIGESTS.items():
 if hashlib.sha256(_parts[name]).hexdigest()!=digest:raise ValueError('source identity')
def namespace(arm='D'):
 n={'__name__':'opcode_event_parse_bundle'}
 exec(compile(lzma.decompress(_parts['p']),'<parent>','exec'),n)
 exec(compile(lzma.decompress(_parts['v']),'<encoder-correction>','exec'),n)
 return n['install'](n,_parts['p'],arm)
def compress(data):return namespace()['compress'](data)
def decompress(data):return namespace('P')['decompress'](data)
'''


def bundle(root=ROOT):
    parts = []
    for name, digest in INPUTS.items():
        data = (root / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('measured source differs: ' + name)
        parts.append(data)
    imported = b'from lib.opcode_literal_event_cost_v1 import literal_event_costs\n'
    if parts[2].count(imported) != 1:
        raise ValueError('helper import differs')
    mutation = parts[1] + b'\n' + parts[2].replace(imported, b'')
    compile(mutation, '<encoder-correction>', 'exec')
    files = dict(p=parts[0], v=lzma.compress(mutation, format=lzma.FORMAT_ALONE, preset=6))
    digests = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    files['program.py'] = LOADER.replace('DIGESTS', repr(digests)).encode()
    return files


def write_bundle(output):
    files = bundle()
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    return {name: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            for name, data in files.items()}
