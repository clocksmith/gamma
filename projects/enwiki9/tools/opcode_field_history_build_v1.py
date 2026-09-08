#!/usr/bin/env python3
"""Package the authenticated field-history implementation without changing it."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUTS = {
    'programs/opcode_field_compact_v1/p':
        '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8',
    'lib/opcode_field_history_v1.py':
        '800eca6682f8d21743216b2adebcad29086081ff7638b4f97decc3f34db3f52b',
}
LOADER = '''import hashlib,lzma
from pathlib import Path
_packed=Path(__file__).with_name('p').read_bytes()
if hashlib.sha256(_packed).hexdigest()!='PACKED_SHA':raise ValueError('packed source identity')
_source=lzma.decompress(_packed)
def namespace(arm='D'):
 n={'__name__':'opcode_field_history_bundle'}
 exec(compile(_source,'<packed-codec>','exec'),n)
 return n['install'](n,arm)
def compress(d):return namespace()['compress'](d)
def decompress(d):return namespace()['decompress'](d)
'''


def source(root=ROOT):
    contents = []
    for path, digest in INPUTS.items():
        data = (root / path).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('source identity differs: ' + path)
        contents.append(data)
    expanded = lzma.decompress(contents[0], format=lzma.FORMAT_ALONE) + b'\n' + contents[1]
    compile(expanded, '<field-history-bundle>', 'exec')
    return expanded


def bundle(root=ROOT):
    packed = lzma.compress(source(root), format=lzma.FORMAT_ALONE, preset=6)
    loader = LOADER.replace('PACKED_SHA', hashlib.sha256(packed).hexdigest()).encode()
    return {'p': packed, 'program.py': loader}


def write_bundle(output, root=ROOT):
    files = bundle(root)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (output / name).open('xb') as stream:
            stream.write(data)
    return {
        'members': {name: {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                    for name, data in files.items()},
        'local_source_bytes': sum(map(len, files.values())),
        'expanded_source_sha256': hashlib.sha256(source(root)).hexdigest(),
        'complete_package_bytes': None,
        'unresolved': ['Python and standard-library runtime', 'license closure',
                       'official packaging multiplicities and options'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(write_bundle(args.output), sort_keys=True))


if __name__ == '__main__':
    main()
