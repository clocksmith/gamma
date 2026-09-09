#!/usr/bin/env python3
"""Export only the measured treatment; development arm selection is not required at runtime."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'results/opcode_previous_word_compact_v1_source_20260909/p'
SOURCE_SHA = 'b58e245d32513d7446d338f6a1a36956d2d77b25777621408da1658e9b6b394f'
LOADER = 'programs/opcode_field_compact_v1/program.py'
LOADER_SHA = '7361c8aa3695ec9d1556be02de66a1f0781414e78b44827511fb08bf8c8c05eb'


def checked(root, path, digest):
    data = (Path(root) / path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('release input identity differs')
    return data


def bundle(root=ROOT):
    text = lzma.decompress(checked(root, SOURCE, SOURCE_SHA)).decode('utf-8')
    replacements = (
        ("st._completed_words[_arm=='S']", 'st._completed_words[0]'),
        ("_arm in ('D','S') and st._completed_words is not None", 'st._completed_words is not None'),
        ("words and _arm!='P'", 'words'),
    )
    for before, after in replacements:
        if text.count(before) != 1:
            raise ValueError('release source site differs')
        text = text.replace(before, after)
    if '_arm' in text:
        raise ValueError('release retains arm dependency')
    compile(text, '<word-release>', 'exec')
    return {'p': lzma.compress(text.encode('utf-8'), format=lzma.FORMAT_ALONE, preset=6),
            'program.py': checked(root, LOADER, LOADER_SHA)}


def write_bundle(output):
    files = bundle()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        with (output / name).open('xb') as stream:
            stream.write(data)
    return {name: dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            for name, data in files.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    files = write_bundle(args.output)
    print(json.dumps(dict(files=files, local_source_bytes=sum(r['bytes'] for r in files.values()),
                          complete_package_bytes=None), sort_keys=True))


if __name__ == '__main__':
    main()
