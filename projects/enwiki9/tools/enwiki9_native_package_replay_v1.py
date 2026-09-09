"""Native package discovery through existing closure, sandbox and gate helpers.

Called by a separately frozen NativeGate, never an independent launch surface.
This reports execution parity even when license or submission closure is missing.
It cannot issue a release-canary pass or an objective receipt.
"""
from pathlib import Path
import json
import shutil

import enwiki9_clean_room_replay as replay
import research_contracts


def require(value, message):
    if not value:
        raise ValueError(message)


def match(path, expected):
    require(path.is_file() and not path.is_symlink(), 'missing regular artifact: ' + str(path))
    require(path.stat().st_size == expected['bytes'] and
            replay.digest(path) == expected['sha256'].removeprefix('sha256:'),
            'artifact identity differs: ' + str(path))


def bound_file(gate, relative):
    require(relative in gate.buffers, 'unbound package input: ' + relative)
    path = gate.root / relative
    require(path.resolve() == path and not Path(relative).is_absolute() and
            '..' not in Path(relative).parts, 'aliased package input')
    require(path.read_bytes() == gate.buffers[relative], 'changed package input: ' + relative)
    return path


def validate(gate, manifest_path, spec_path):
    manifest_file = bound_file(gate, manifest_path)
    spec = json.loads(bound_file(gate, spec_path).read_text())
    research_contracts.validate_artifact(manifest_file)
    manifest = json.loads(manifest_file.read_text())
    require(manifest['candidateId'] == gate.candidate, 'wrong package candidate')
    require(manifest['objective'] == research_contracts.objective_binding(), 'wrong package objective')
    replay.validate_command_contract(manifest)
    package = manifest_file.parent / manifest['candidateRoot']
    replay.verify_package_copy(package, manifest['countedFiles'])
    for row in manifest['countedFiles']:
        bound_file(gate, str((package / row['path']).relative_to(gate.root)))
    require(gate.caps['cpus'] == [2] and 0 < gate.caps['memory_bytes'] <= 10_000_000_000
            and 0 < gate.caps['scratch_bytes'] <= 100_000_000_000
            and gate.caps['swap_bytes'] == 0, 'native discovery resource bounds differ')
    require(spec['resource_budget'] == gate.caps, 'package spec budget differs')
    for key in ('build_phase_seconds', 'codec_phase_seconds'):
        require(type(spec[key]) is int and 0 < spec[key] <= gate.caps['wall_seconds'], 'invalid phase bound')
    require(0 < spec['corpus']['bytes'] <= 1_000_000, 'native package discovery population exceeds scope')
    for key in ('corpus', 'trace'):
        match(bound_file(gate, spec[key]['path']), spec[key])
    binary = Path(spec['binary']['path'])
    require(not binary.is_absolute() and '..' not in binary.parts and str(binary) not in
            {row['path'] for row in manifest['countedFiles']}, 'binary must be independently built')
    require(spec['trace']['bytes'] > 0 and spec['trace']['bytes'] % 28 == 0, 'invalid native trace size')
    return manifest_file, manifest, spec, package


def sandbox_command(work, corpus, command, manifest, *, trace=False):
    # Preserve the established isolated mounts and 16 MiB temporary filesystem.
    # Actual native/compiler scratch goes in the cgroup-guarded /work tree.
    prefix = replay.sandbox_prefix(work, corpus, canary=True)
    require(prefix[-1] == '--', 'sandbox command delimiter differs')
    environment = ['--setenv', 'TMPDIR', '/work/tmp']
    if trace:
        environment += ['--setenv', 'GAMMA_FX2_CODER_TRACE', '/work/codec.trace']
    return prefix[:-1] + environment + ['--'] + replay.expand_command(command, manifest, 'archive.bin')


def run(gate, manifest_path, spec_path):
    """Build/encode, independently build/re-encode, independently build/decode."""
    manifest_file, manifest, spec, package = validate(gate, manifest_path, spec_path)
    output = gate.result / 'package-replay'
    output.mkdir(exist_ok=False)
    source = bound_file(gate, spec['corpus']['path'])
    reference_trace = bound_file(gate, spec['trace']['path'])
    phases, first_archive = [], None
    for name in ('encode', 'repeat', 'decode'):
        gate.verify()
        work = replay.fresh_work(output, name, package, manifest)
        build = sandbox_command(work, None, manifest['commands']['build'], manifest)
        gate.run('package-' + name + '-build', build, spec['build_phase_seconds'])
        binary = work / 'package' / spec['binary']['path']
        match(binary, spec['binary'])
        # Build outputs may be new; every supplied source/model byte stays exact.
        for row in manifest['countedFiles']:
            match(work / 'package' / row['path'], row)
        gate.binaries[str(binary)] = spec['binary']['sha256'].removeprefix('sha256:')
        if name == 'decode':
            require(first_archive is not None, 'missing independently encoded archive')
            shutil.copyfile(first_archive, work / 'archive.bin')
            match(work / 'archive.bin', spec['archive'])
        command = manifest['commands']['decompress' if name == 'decode' else 'compress']
        invocation = sandbox_command(work, None if name == 'decode' else source,
                                     command, manifest, trace=True)
        gate.run('package-' + name, invocation, spec['codec_phase_seconds'])
        match(binary, spec['binary'])
        for row in manifest['countedFiles']:
            match(work / 'package' / row['path'], row)
        require(not (work / 'package/ppm.temp').exists(), 'native scratch did not close')
        artifact = work / ('restored.enwik9' if name == 'decode' else 'archive.bin')
        match(artifact, spec['corpus'] if name == 'decode' else spec['archive'])
        trace = gate.compare_trace(reference_trace, work / 'codec.trace', spec['trace']['bytes'])
        if name == 'encode':
            first_archive = artifact
        phases.append({'phase': name, 'binary': gate.artifact(binary),
                       'artifact': gate.artifact(artifact), 'trace_comparison': trace,
                       'corpus_mounted': name != 'decode'})
    gate.closure()
    gate.verify()
    replay.verify_package_copy(package, manifest['countedFiles'])
    result = {
        'schema': 'gamma.enwiki9.native-package-discovery.v1',
        'candidate_id': gate.candidate, 'status': 'execution-parity-pass',
        'manifest': gate.artifact(manifest_file), 'phases': phases,
        'independent_builds': 3, 'exact_inverse': True, 'exact_repeat': True,
        'native_coder_records_identical': True,
        'input_bytes': spec['corpus']['bytes'], 'archive_bytes': spec['archive']['bytes'],
        'counted_source_package_bytes': manifest['totalPackageBytes'],
        'declared_option_bytes': manifest['requiredOptionBytes'],
        'dependency_closure_complete': manifest['complete'],
        'license_audit': research_contracts.dependency_license_audit(manifest),
        'resource_budget': gate.caps, 'continuous_guard_decision': 'pending canonical outer guard closure',
        'qualification_authority': False, 'complete_package_bytes': None,
        'full_corpus_score_bytes': None, 'objective_credit_bytes': 0,
        'limitations': [
            'Host /usr supplies declared toolchain and runtime; this is not transitive dependency closure.',
            'Native entry-point parity does not execute full-corpus self-extracting preprocessing.',
            'Trace comparison covers recorded probabilities, coder state and truth, not every hidden-state byte.',
            'Source inventory and unique declared option strings are not committee-certified package accounting.'
        ]
    }
    gate.write('package-replay.json', result)
    return result
