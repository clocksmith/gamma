#!/usr/bin/env python3
"""Bounded synthetic native tensor parity; no trained model or corpus access."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time
from fx2_weight_adaptive_loader_gate_v1 import phase
from fx2_weight_neighbor_model_audit_v1 import binding
from fx2_weight_sign_magnitude_loader_v1 import patch

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', required=True, type=Path)
    p.add_argument('--admission', required=True, type=Path)
    args = p.parse_args()
    plan = json.loads(args.plan.read_text())
    admission = json.loads(args.admission.read_text())
    if (admission.get('id') != plan['id'] or admission.get('admitted') is not True
            or admission.get('plan_sha256') != hashlib.sha256(args.plan.read_bytes()).hexdigest()):
        raise ValueError('matching source-bound admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')

    def verify():
        for row in plan['inputs']:
            actual = binding(ROOT / row['path'])
            if any(actual[k] != row[k] for k in ('bytes', 'sha256')):
                raise ValueError('changed input: ' + row['path'])
    verify()
    output = ROOT / plan['output']
    output.mkdir(exist_ok=False)
    (output / 'tmp').mkdir()
    deadline = time.monotonic() + plan['bounds']['elapsed_seconds']

    def invoke(name, cmd):
        return phase(output, name, cmd, plan['bounds'], deadline, ROOT)

    source = output / 'source'
    source.mkdir()
    for name, path in plan['sources'].items():
        data = (ROOT / path).read_bytes()
        if name == 'weights_io_compressed.cpp':
            data = patch(data)
        with (source / name).open('xb') as stream:
            stream.write(data)
    common = ['/usr/bin/g++', '-std=c++17', '-O2', '-include', 'cstdint',
              '-fno-exceptions', '-fno-fast-math', '-mrecip=none', '-I' + str(source),
              source / 'weights_io.cpp', source / 'weights_io_compressed.cpp']
    for name, fixture in [('new', 'test_weights_compressed.cpp'), ('compare', 'compare.cpp')]:
        invoke('build-' + name, common + [source / fixture, '-o', output / name])
    env = {
        'FX2_LOADER_TMP': str(output / 'tmp'),
        'FX2_LOADER_CODEC': str(ROOT / plan['codec']),
        'FX2_LOADER_ADAPTIVE_CODEC': str(ROOT / plan['adaptive_codec']),
        'FX2_LOADER_OLD': str(ROOT / plan['old']),
        'FX2_LOADER_NEW': str(output / 'new'),
        'FX2_LOADER_COMPARE': str(output / 'compare'),
        'FX2_LOADER_SOURCE': str(ROOT / plan['sources']['weights_io_compressed.cpp']),
    }
    invoke('native-tests', ['/usr/bin/env', *[k + '=' + v for k, v in env.items()],
           '/usr/bin/python3', '-m', 'unittest', 'discover', '-s', 'tests',
           '-p', 'test_fx2_weight_sign_magnitude_native_v1.py', '-v'])
    verify()
    rows = [json.loads(s) for s in (output / 'commands.jsonl').read_text().splitlines()]
    result = dict(schema='gamma.enwiki9.sign-magnitude-native-unit.v1',
                  id=plan['id'], status='passed', source_inputs_unchanged=True,
                  phases=rows, builds=[binding(output / name) for name in ('new', 'compare')],
                  scope='Seven synthetic native tensor tests; no production TransformerOpt initialization.',
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0)
    with (output / 'receipt.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], phases=len(rows), objective_credit_bytes=0)))


if __name__ == '__main__':
    main()
