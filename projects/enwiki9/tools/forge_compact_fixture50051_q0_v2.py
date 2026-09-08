#!/usr/bin/env python3
"""Retry the unchanged parent with a scratch envelope covering its PPM heap."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
ID = 'forge_compact_fixture50051_q0_v2'
BASE = 'tools/forge_compact_fixture50051_q0_v1.py'


def load(validate):
    path = 'operations/adaptive/experiments/' + ID + '.json'
    content = (ROOT / path).read_bytes()
    if not validate:
        reference = {'path': path, 'sha256': 'sha256:' + hashlib.sha256(content).hexdigest()}
        if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) != reference:
            raise ValueError('experiment changed')
    refs = {r['path']: r['sha256'].removeprefix('sha256:') for r in json.loads(content)['inputs']}
    for name in ('tools/' + ID + '.py', BASE):
        p = ROOT / name
        if p.resolve() != p or hashlib.sha256(p.read_bytes()).hexdigest() != refs[name]:
            raise ValueError('retry source changed')
    namespace = {'__file__': str(ROOT / BASE), '__name__': 'forge_frozen_parent'}
    exec(compile((ROOT / BASE).read_bytes(), str(ROOT / BASE), 'exec'), namespace)
    namespace['ID'] = ID
    namespace['CAPS'] = {**namespace['CAPS'], 'scratch_bytes': 16000000000}
    if namespace['CAPS']['scratch_bytes'] <= (14000 << 20):
        raise ValueError('scratch does not cover pinned PPM heap')
    return namespace


if __name__ == '__main__':
    if sys.argv[1:] not in ([], ['--validate-only']):
        raise ValueError('unexpected arguments')
    raise SystemExit(load(bool(sys.argv[1:]))['main']())
