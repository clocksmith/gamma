#!/usr/bin/env python3
"""Bounded production-entrypoint parity and native rebuild for adaptive packing."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from fx2_weight_adaptive_dispatch_v1 import patch
from fx2_weight_adaptive_loader_gate_v1 import FAST, phase
from fx2_weight_neighbor_model_audit_v1 import binding

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'operations/provenance/fx2_weight_adaptive_dispatch_gate_v1_plan.json'


def verify(plan, inputs):
    rows = inputs['inputs'] + inputs['native_sources'] + list(plan['models'].values())
    rows += [plan['native_parent'], plan['patched_loader']]
    for row in rows:
        actual = binding(ROOT/row['path'])
        if any(actual[k] != row[k] for k in ('bytes', 'sha256')):
            raise ValueError('changed input: '+row['path'])


def run(plan, inputs, output):
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    (output/'tmp').mkdir()
    deadline = time.monotonic()+plan['bounds']['elapsed_seconds']
    def invoke(name, command, work=None):
        return phase(output, name, command, plan['bounds'], deadline, work)
    builds, probes = {}, {}
    dispatcher = 'cpp_infer/src/opt/arena_build.cpp'
    loader = 'cpp_infer/src/weights_io_compressed.cpp'
    source_delta = 0
    for arm in ('P', 'D'):
        tree = output/arm; tree.mkdir()
        for row in inputs['native_sources']:
            original = (ROOT/row['path']).read_bytes()
            source = original
            if arm == 'D':
                if row['relative'] == loader:
                    source = (ROOT/plan['patched_loader']['path']).read_bytes()
                elif row['relative'] == dispatcher:
                    source = patch(source)
                source_delta += len(source)-len(original)
            target = tree/row['relative']; target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(source)
        invoke('build-'+arm, ['/usr/bin/make', '-j1', 'cmix', 'CC=/usr/bin/g++',
               'CPPFLAGS_PART-THAT-SHOULD-BE-FAST='+FAST+' -O3',
               'CPPFLAGS_PART-THAT-CAN-BE-SLOW='+FAST+' -Os'], tree)
        builds[arm] = binding(tree/'cmix')
        probe = tree/'production-probe'
        objects = sorted(tree.glob('tf_*.o'))
        if len(objects) != 9: raise ValueError('transformer object closure differs')
        invoke('probe-build-'+arm, ['/usr/bin/g++', '-std=c++17', '-O2', '-march=x86-64-v3',
               '-mrecip=none', '-fno-fast-math', '-Wl,--gc-sections',
               '-I'+str(tree/'cpp_infer/src'), ROOT/plan['probe'], *objects, '-o', probe])
        probes[arm] = probe
    for key in ('bytes', 'sha256'):
        if builds['P'][key] != plan['native_parent'][key]:
            raise ValueError('retained parent native rebuild differs')
    # A matched negative control must reproduce the diagnosed production failure.
    invoke('old-dispatch-negative', [sys.executable, Path(__file__).resolve(), '--expect-bad-magic',
           probes['P'], ROOT/plan['models']['adaptive']['path'], output/'negative.bin'])
    outputs = []
    for arm, model, label in [('P', 'original', 'P-original'), ('P', 'parent', 'P-fixed'),
                              ('D', 'original', 'D-original'), ('D', 'parent', 'D-fixed'),
                              ('D', 'adaptive', 'D-adaptive'), ('D', 'adaptive', 'D-repeat')]:
        target = output/(label+'.bin')
        invoke(label, [probes[arm], ROOT/plan['models'][model]['path'], target])
        raw = target.read_bytes()
        if len(raw) != 104960: raise ValueError('production smoke population differs')
        if outputs and raw != (ROOT/outputs[0]['path']).read_bytes():
            raise ValueError('production probability/logit divergence: '+label)
        outputs.append(binding(target))
    needed = {}
    for arm in ('P', 'D'):
        report = invoke('dependencies-'+arm, ['/usr/bin/objdump', '-p', builds[arm]['path']])
        needed[arm] = re.findall(r'^\s+NEEDED\s+(\S+)', report, re.M)
    if needed['P'] != needed['D']: raise ValueError('dynamic dependencies differ')
    instructions = invoke('disassemble-D', ['/usr/bin/objdump', '-d', '--insn-width=16', builds['D']['path']])
    if re.search(r'\b(?:v?(?:rcp|rsqrt)(?:14|28)?(?:ss|ps))\b|%zmm|%k[0-7]|\{vex\}|\t62 [0-9a-f][0-9a-f] ', instructions):
        raise ValueError('forbidden reciprocal or AVX512 instruction')
    verify(plan, inputs)
    model_delta = plan['models']['adaptive']['bytes']-plan['models']['parent']['bytes']
    binary_delta = builds['D']['bytes']-builds['P']['bytes']
    result = dict(schema='gamma.enwiki9.adaptive-production-dispatch.v1',
                  status='passed', native_builds=builds, needed_libraries=needed,
                  synthetic_symbols_per_phase=64, output_bytes_per_phase=104960,
                  production_outputs=outputs, all_production_outputs_exact=True,
                  old_dispatch_negative_reproduced=True, model_delta_per_copy=model_delta,
                  binary_delta_per_copy=binary_delta, raw_source_delta=source_delta,
                  runtime_pair_delta=2*(model_delta+binary_delta),
                  source_compressor_plus_decoder_delta=2*model_delta+binary_delta+source_delta,
                  option_delta_bytes=0, complete_package_bytes=None,
                  full_corpus_score_bytes=None, objective_credit_bytes=0)
    with (output/'receipt.json').open('x') as stream: json.dump(result, stream, indent=2); stream.write('\n')
    return result


def main():
    if sys.argv[1:2] == ['--expect-bad-magic']:
        if len(sys.argv) != 5: return 2
        attempt = subprocess.run(sys.argv[2:], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        sys.stderr.buffer.write(attempt.stderr)
        return 0 if attempt.returncode == 1 and b'bad magic' in attempt.stderr and not Path(sys.argv[4]).exists() else 3
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('inputs', 'admission', 'output'): parser.add_argument('--'+name, required=True)
    args = parser.parse_args()
    plan = json.loads((ROOT/PLAN).read_text()); inputs = json.loads(Path(args.inputs).read_text())
    admission = json.loads(Path(args.admission).read_text())
    if admission.get('id') != plan['id'] or admission.get('admitted') is not True:
        raise ValueError('matching admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    if Path(args.output).resolve() != (ROOT/plan['output']).resolve():
        raise ValueError('frozen output differs')
    verify(plan, inputs)
    result = run(plan, inputs, args.output)
    print(json.dumps({k: result[k] for k in ('status', 'binary_delta_per_copy', 'runtime_pair_delta', 'source_compressor_plus_decoder_delta')}))
    return 0


if __name__ == '__main__': raise SystemExit(main())
