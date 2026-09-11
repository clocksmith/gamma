#!/usr/bin/env python3
"""Measure unchanged paired source ZIPs with explicitly incomplete closures."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import sys
import time
import zipfile

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
sys.dont_write_bytecode = True


def ref(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def verify(row):
    path = ROOT / row['path']
    assert path.is_file() and path.stat().st_size == row['bytes'], row['path']
    assert ref(path)['sha256'] == row['sha256'].removeprefix('sha256:'), row['path']


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write('\n')


def main():
    start = time.monotonic()
    assert os.sched_getaffinity(0) == {3}, 'CPU affinity differs'
    for kind, expected in ((resource.RLIMIT_AS, 268435456), (resource.RLIMIT_CPU, 10),
                           (resource.RLIMIT_FSIZE, 1048576)):
        assert resource.getrlimit(kind) == (expected, expected), 'process bounds differ'
    for name in ('staging', 'release', 'packages', 'result.json', 'artifacts.json'):
        if (BASE / name).exists(): raise FileExistsError('measurement output already exists: '+name)
    inputs = json.loads((BASE / 'bindings.json').read_text())['inputs']
    for row in inputs: verify(row)
    self_ref = ref(Path(__file__))
    runtime_plan = json.loads((ROOT / 'operations/provenance/opcode_previous_word_release250k_v1_inputs.json').read_text())
    runtime = runtime_plan['runtime_files']
    assert len(runtime) == 171
    for row in runtime: verify(row)
    sys.path.insert(0, str(ROOT / 'tools'))
    import enwiki9_dependency_closure as closure
    import build_reproducible_source_zip as zipper
    # Record the measurement process's loaded providers separately from codec dependencies.
    providers = sorted({str(Path(m.__file__).resolve()) for m in tuple(sys.modules.values())
                        if getattr(m, '__file__', None) and Path(m.__file__).is_file()})
    measurement_runtime = [ref(Path(p)) for p in providers]
    terminal = json.loads((ROOT / 'operations/provenance/opcode_previous_word_release_terminal_20260909.json').read_text())
    assert terminal['status'] == 'passed' and terminal['archive_difference_from_original_parent_bytes'] == 147
    assert terminal['archive_bytes'] == 67511 and terminal['original_parent_archive_bytes'] == 67658
    prior_commands = json.loads((ROOT / 'results/opcode_previous_word_release_v1_unit_20260909/fixtures/standalone/commands.json').read_text())
    prior = prior_commands[0]['argv']
    assert prior[1:5] == ['-I', '-S', '-B', '-c'] and prior[7] == 'compress'
    launcher = prior[5]
    commands = dict(build=[prior[0], '-I', '-S', '-B', '-c', 'pass'],
        compress=[*prior[:5], launcher, '{entry_point}', 'compress', '{corpus}', '{archive}'],
        decompress=[*prior[:5], launcher, '{entry_point}', 'decompress', '{archive}', '{restored}'])
    options = ['-I', '-S', '-B', '-c', launcher, 'compress', 'decompress', 'pass']
    write(BASE / 'declared-invocation.json', dict(commands=commands, required_options=options,
        command_source='Exact earlier isolated launcher; only path placeholders and operation arguments adapted.',
        executed_here=False, build_scope='No-op for already materialized source; not an executable-producing Makefile.',
        accounting_scope='Literal option union counted by dependency materializer; official option treatment unresolved.'))
    gaps = [
        'Python interpreter and transitive runtime availability/counting are unresolved; runtime171 is observation inventory, not minimal closure.',
        'Python standard-library and native liblzma/libm/provider license closure is not certified.',
        'No counted package license notice; Gamma repository notice applicability and required dependency notices remain to be delivered.',
        'Source ZIP lacks an executable-producing Makefile; delivered public entry/build form remains unresolved.',
        'Declared launcher option union is not verified official option accounting; archive/decoder multiplicities remain unresolved.',
        'Existing clean-room tool mounts all /usr and does not prove minimal runtime closure.'
    ]
    deps = [dict(name='Unchanged codec packed source', kind='bundled', provider='p', counted=True,
                 license='LicenseRef-Gamma-Source-Notice-Closure-Unresolved'),
            dict(name='Unchanged Python loader', kind='bundled', provider='program.py', counted=True,
                 license='LicenseRef-Gamma-Source-Notice-Closure-Unresolved'),
            dict(name='Python interpreter, standard modules and transitive native providers', kind='runtime',
                 provider='/usr/bin/python3', counted=False, license='LicenseRef-Python-Runtime-Closure-Unresolved')]
    write(BASE / 'dependencies.json', deps)
    write(BASE / 'roles.json', {'p':'source', 'program.py':'source'})
    (BASE / 'staging').mkdir(); (BASE / 'packages').mkdir()
    sources = {'P': ROOT / 'programs/opcode_field_compact_v1',
               'D': ROOT / 'results/opcode_previous_word_release_v1_source_20260909'}
    rows = {}
    for arm, source in sources.items():
        staged = BASE / 'staging' / arm; staged.mkdir()
        for name in ('p', 'program.py'): shutil.copyfile(source / name, staged / name)
        args = argparse.Namespace(candidate_id=BASE.name, source_root=staged,
            bundle=BASE / 'release' / arm, entry_point='program.py', platform='linux-x86-64',
            build_command_json=json.dumps(commands['build']), compress_command_json=json.dumps(commands['compress']),
            decompress_command_json=json.dumps(commands['decompress']), dependencies=BASE / 'dependencies.json',
            roles=BASE / 'roles.json', required_option=options, missing=gaps, declare_complete=False,
            require_license_audit=False)
        manifest_path = closure.materialize(args)
        manifest = json.loads(manifest_path.read_text())
        assert manifest['complete'] is False and manifest['missing']
        audit_path = manifest_path.with_name('license-audit.json')
        assert json.loads(audit_path.read_text())['audit']['approved'] is False
        files = sorted(row['path'] for row in manifest['countedFiles'])
        assert files == ['p', 'program.py']
        first, repeat = [BASE / 'packages' / (arm+suffix) for suffix in ('.zip', '.repeat.zip')]
        zipper.build_zip(manifest_path.parent / 'package', files, first, zipfile.ZIP_DEFLATED)
        zipper.build_zip(manifest_path.parent / 'package', files, repeat, zipfile.ZIP_DEFLATED)
        assert first.read_bytes() == repeat.read_bytes()
        members = []
        with zipfile.ZipFile(first) as z:
            assert z.namelist() == files and z.testzip() is None
            for info in z.infolist():
                data = z.read(info.filename)
                assert data == (staged / info.filename).read_bytes()
                assert data == (manifest_path.parent / 'package' / info.filename).read_bytes()
                members.append(dict(name=info.filename, bytes=len(data), compressed_bytes=info.compress_size,
                                    sha256=hashlib.sha256(data).hexdigest()))
        rows[arm] = dict(manifest=ref(manifest_path), license_audit=ref(audit_path), source_files=[ref(staged/n) for n in files],
            local_source_bytes=manifest['totalPackageBytes'], declared_option_union_bytes=manifest['requiredOptionBytes'],
            source_zip=ref(first), repeat_zip=ref(repeat), members=members, complete=False, license_audit_approved=False)
    assert rows['P']['local_source_bytes'] == 5746 and rows['D']['local_source_bytes'] == 5856
    assert rows['P']['declared_option_union_bytes'] == rows['D']['declared_option_union_bytes']
    delta = rows['D']['source_zip']['bytes'] - rows['P']['source_zip']['bytes']
    for row in inputs + runtime + measurement_runtime + [self_ref]: verify(row)
    result = dict(schema='gamma.enwiki9.opcode-word-release-package-measurement.v1', status='passed',
        owner='root_explore', inputs=inputs, measurement_source=self_ref, arms=rows,
        runtime_inventory_reference=ref(ROOT / 'operations/provenance/opcode_previous_word_release250k_v1_inputs.json'),
        runtime_inventory_count=171, runtime_inventory_not_minimal_package=True,
        measurement_runtime=measurement_runtime, declared_invocation=ref(BASE / 'declared-invocation.json'),
        source_zip_delta_bytes=delta, raw_source_delta_bytes=110, historical_opening_archive_saving_bytes=147,
        archive_minus_one_source_zip_delta_bytes=147-delta, archive_minus_two_source_zip_copies_delta_bytes=147-2*delta,
        raw_source_one_copy_subtotal_bytes=37, raw_source_two_copy_subtotal_bytes=-73,
        closure_complete=False, blockers=gaps, source_and_runtime_reverified=True, codec_executed=False, corpus_read=False,
        zip_policy='ZIP_DEFLATED via unchanged build_zip; sorted identical member paths, fixed1980 timestamp/mode. '
                   'No explicit per-ZipInfo compression level; library default applies. No parameter search.',
        deterministic_zip_repeat=True, all_members_verified=True,
        resources=dict(cpu=3, address_space_bytes=268435456, cpu_seconds_limit=10, wall_seconds_limit=15,
            file_bytes_limit=1048576, elapsed_seconds=time.monotonic()-start,
            peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
        scope='Unchanged local source delivery only; incomplete manifests and unexecuted invocation cannot establish submission closure.')
    write(BASE / 'result.json', result)
    write(BASE / 'artifacts.json', dict(files=[ref(p) for p in sorted(BASE.rglob('*'))
        if p.is_file() and p.name not in ('stdout.log', 'stderr.log')],
        live_execution_logs_excluded='Bound separately by the outer receipt after process exit.'))
    print(json.dumps(dict(status='passed', P_zip=rows['P']['source_zip']['bytes'], D_zip=rows['D']['source_zip']['bytes'],
                         source_zip_delta_bytes=delta, closure_complete=False, codec_executed=False)))


if __name__ == '__main__':
    main()
