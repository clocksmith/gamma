#!/usr/bin/env python3
"""Materialize a new source-integrated realization of the measured word predictor."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = 'programs/opcode_field_compact_v1/p'
PARENT_SHA = '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'
LOADER = '''import lzma
from pathlib import Path
_source=lzma.decompress(Path(__file__).with_name('p').read_bytes())
def namespace(arm='D'):
 if arm not in ('P','K','D','S'):raise ValueError('arm')
 n={'__name__':'compact_previous_word','_arm':arm};exec(compile(_source,'<packed-codec>','exec'),n);return n
def compress(d):return namespace()['compress'](d)
def decompress(d):return namespace()['decompress'](d)
'''

# Each replacement is checked against authenticated immutable parent bytes.
# The prefix estimator has a local state with disabled history. It therefore
# retains parent keys even when the surrounding namespace selects D or S.
# There is no mutable global phase selector and no second code namespace.
REPLACEMENTS = (
    ('   (bp,st.col>>3,st.f),',
     "   (bp,st._completed_words[_arm=='S'],bytes(st.word[-2:]),st.f) if _arm in ('D','S') and st._completed_words is not None else (bp,st.col>>3,st.f),"),
    (' lit=LIT();st=GST();pre=[0.0]',
     ' lit=LIT();st=GST(False);pre=[0.0]'),
    (' def __init__(s):\n  super().__init__();s.modeled_f=s.f;s.field=Field();s.position=0',
     " def __init__(s,words=True):\n  super().__init__();s.modeled_f=s.f;s.field=Field();s.position=0\n  s._completed_words=(b'',b'') if words and _arm!='P' else None\n def completed_words(s):return s._completed_words or (b'',b'')"),
    ("  require(s.position<_limit,'modeled output bound')\n  s.f=s.modeled_f;super().up(b);s.modeled_f=s.f\n  s.field.up(b);s.f=s.field.f;s.position+=1",
     "  require(s.position<_limit,'modeled output bound')\n  w=bytes(s.word[-8:]) if s._completed_words is not None and s.word and not(65<=b<=90 or 97<=b<=122) else b''\n  s.f=s.modeled_f;super().up(b);s.modeled_f=s.f\n  s.field.up(b);s.f=s.field.f;s.position+=1\n  if w:s._completed_words=(w,s._completed_words[0])"),
)


def source(root=ROOT):
    packed = (Path(root) / PARENT).read_bytes()
    if hashlib.sha256(packed).hexdigest() != PARENT_SHA:
        raise ValueError('parent identity differs')
    text = lzma.decompress(packed).decode('utf-8')
    for before, after in REPLACEMENTS:
        if text.count(before) != 1:
            raise ValueError('parent source site differs')
        text = text.replace(before, after)
    result = text.encode('utf-8')
    compile(result, '<compact-previous-word>', 'exec')
    return result


def bundle(root=ROOT):
    return {'p': lzma.compress(source(root), format=lzma.FORMAT_ALONE, preset=6),
            'program.py': LOADER.encode('utf-8')}


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
