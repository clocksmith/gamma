#!/usr/bin/env python3
"""Build auxiliary assets and a native self-extracting compressor.

Delivered as gamma_pack_auxiliary.py in the new source package. Execution needs
an independently admitted native gate; this file is not a gate launcher.
The binary must be built from that package with the pinned compiler/options.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess

ASSETS = {
    'dictionary/english.dic': '4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a',
    'src/readalike_prepr/data/new_article_order': '4d0fa5313c753c1ecf71e91a83e285894cdde20049711456e6514c07eb85c581',
    'models/6m-q4-fp32.tfwc2': '7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860',
}


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def assemble(binary, dictionary, order, weights, target):
    """Exact little-endian upstream four-int footer; all supplied bytes paid."""
    paths = [binary, dictionary, order, weights]
    if target.exists() or target.is_symlink():
        raise ValueError('output already exists')
    if any(not p.is_file() or p.is_symlink() for p in paths):
        raise ValueError('nonregular package member')
    sizes = [p.stat().st_size for p in paths]
    if any(n <= 0 for n in sizes) or any(n > 2147483647 for n in sizes[1:]):
        raise ValueError('member outside native footer bounds')
    with target.open('xb') as out:
        for p in paths:
            with p.open('rb') as source:
                shutil.copyfileobj(source, out)
        out.write(struct.pack('<iiii', sizes[1], sizes[2], 0, sizes[3]))
    target.chmod(0o755)
    return {'bytes': target.stat().st_size, 'sha256': digest(target),
            'member_bytes': dict(zip(('executable', 'dictionary', 'order', 'model'), sizes)),
            'footer_bytes': 16}


def build(root, binary, work):
    for name, expected in ASSETS.items():
        p = root / name
        if not p.is_file() or p.is_symlink() or digest(p) != expected:
            raise ValueError('asset identity differs: ' + name)
    if not binary.is_file() or binary.is_symlink():
        raise ValueError('native binary missing or aliased')
    work.mkdir(exist_ok=False)
    local = work / 'native'
    local.mkdir()
    helper = local / 'cmix'
    shutil.copyfile(binary, helper); helper.chmod(0o755)
    commands = []
    for name, source in [('dict', root / 'dictionary/english.dic'),
                         ('order', root / 'src/readalike_prepr/data/new_article_order')]:
        encoded, decoded = local / (name + '.comp'), local / (name + '.restored')
        for mode, src, dst in [('c', source, encoded), ('d', encoded, decoded)]:
            cmd = [str(helper), '-' + mode, str(src), str(dst), '--ppmd-only']
            # Outer native gate owns process-tree/resource stops and evidence.
            done = subprocess.run(cmd, cwd=local, check=False)
            commands.append({'command': cmd, 'returncode': done.returncode})
            (work / 'commands.json').write_text(json.dumps(commands, indent=2) + '\n')
            if done.returncode:
                raise RuntimeError('auxiliary codec returned ' + str(done.returncode))
            scratch = local / 'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file():
                    raise ValueError('unexpected auxiliary scratch')
                scratch.unlink()
        if digest(decoded) != digest(source) or decoded.stat().st_size != source.stat().st_size:
            raise ValueError('auxiliary inverse differs')
    result = assemble(helper, local / 'dict.comp', local / 'order.comp',
                      root / 'models/6m-q4-fp32.tfwc2', work / 'cmix')
    result.update(complete_submission_package=False,
                  scope='Auxiliary build only; no enwik9 main encode/decode or eligibility claim.')
    (work / 'package.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(Path(__file__).resolve().parent,
                           args.binary.resolve(), args.work.resolve())))
