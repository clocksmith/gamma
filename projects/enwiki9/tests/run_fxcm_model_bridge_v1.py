#!/usr/bin/env python3
"""Bounded synthetic adapter regression; never initialize native predictors."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'results/forge_parent_source_audit_v1/source-tree/src/models/fxcm_v26.cpp'
EXPECTED = 'cd4534a22908d7e2a55b594e8604b3c513922e646ff206b4d237a1dd95a71149'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.relative_to(ROOT / 'results')
    if os.sched_getaffinity(0) != {3}:
        raise SystemExit('run this synthetic check with taskset -c 3')
    if digest(UPSTREAM) != EXPECTED:
        raise SystemExit('pinned upstream source mismatch')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    source = UPSTREAM.read_text()
    begin = source.index('int squashc(int d')
    end = source.index('\n}', begin) + 2
    function = source[begin:end]
    (output / 'squash.inc').write_text('using U32 = unsigned int;\n' + function + '\n')
    files = [UPSTREAM, Path(__file__), ROOT / 'tests/fxcm_model_bridge_v1.cpp',
             ROOT / 'tests/fxcm_model_bridge_upstream_v1.cpp',
             ROOT / 'lib/fxcm_model_bridge_v1.hpp',
             ROOT / 'lib/forge_fxcm_raw_adapter_v1.hpp',
             ROOT / 'lib/forge_fxcm_raw_adapter_v2.hpp',
             ROOT / 'operations/provenance/fx2_compact_v26_bridge_v1_plan.json']
    inputs = {str(p.relative_to(ROOT)): digest(p) for p in files}
    records = []

    def limits():
        resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
        resource.setrlimit(resource.RLIMIT_CPU, (90, 90))
        resource.setrlimit(resource.RLIMIT_FSIZE, (33554432, 33554432))

    def run(name, command):
        remaining = 120 - (time.monotonic() - started)
        if remaining <= 0:
            raise RuntimeError('aggregate elapsed stop')
        stdout_path, stderr_path = output / (name + '.stdout'), output / (name + '.stderr')
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        t0 = time.monotonic()
        with stdout_path.open('xb') as out, stderr_path.open('xb') as err:
            child = subprocess.Popen(command, cwd=ROOT, stdout=out, stderr=err,
                                     env={**os.environ, 'TMPDIR': str(output)},
                                     preexec_fn=limits, start_new_session=True)
            timeout = False
            try:
                child.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                timeout = True
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        record = dict(name=name, argv=command, returncode=child.returncode,
                      elapsed_seconds=time.monotonic() - t0,
                      cpu_seconds=after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
                      cumulative_child_maxrss_kib=after.ru_maxrss, timeout=timeout,
                      stdout_sha256=digest(stdout_path), stderr_sha256=digest(stderr_path))
        records.append(record)
        (output / 'phases.json').write_text(json.dumps(records, indent=2) + '\n')
        scratch = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
        if child.returncode or timeout or scratch > 67108864:
            raise RuntimeError(f'{name} failed; see retained phase and stderr')

    flags = ['g++', '-std=c++17', '-include', 'cstdint', '-march=x86-64-v3',
             '-fno-fast-math', '-fno-math-errno', '-fno-exceptions',
             '-fno-threadsafe-statics', '-mrecip=none']
    run('compile', flags + ['-O2', '-I', str(output), 'tests/fxcm_model_bridge_v1.cpp',
                            '-o', str(output / 'fixture')])
    run('fixture', [str(output / 'fixture')])
    run('upstream_syntax', flags + ['-fsyntax-only', 'tests/fxcm_model_bridge_upstream_v1.cpp'])
    if any(digest(ROOT / name) != value for name, value in inputs.items()):
        raise RuntimeError('source changed during test')
    receipt = dict(schema='gamma.enwiki9.interface-unit.v1', id='fx2_compact_v26_bridge_v1',
                   status='pass', source_bindings=inputs, phases=records,
                   actual_upstream_initialization=False, corpus_execution=False,
                   fixture_output=(output / 'fixture.stdout').read_text().strip(),
                   extracted_function_sha256=hashlib.sha256(function.encode()).hexdigest(),
                   scope='Synthetic state/update parity and authenticated pure mapping; native synchronization unproved',
                   objective_credit_bytes=0)
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
