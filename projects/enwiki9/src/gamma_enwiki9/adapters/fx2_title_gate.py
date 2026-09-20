"""Frozen-budget P/E/K/M/S development through the existing lab application."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import shutil
import zipfile

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_training_capture import source_members
from .fx2_title_native import adapt


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value) + b'\n')


def prepare_zero(root, output, plan):
    import numpy as np
    from .fx2_training_reference import materialize as adapt_python, load_package
    from .fx2_title_conditioning import metadata_entries
    output.mkdir()
    reference = output / 'reference'
    adapt_python(root / plan['upstream'], reference)
    package = load_package(reference)
    pack = importlib.import_module(package + '.weights_compress')
    template = pack.read_tensor_file_v2(str(root / plan['entropy_packed']))
    entries = [(name, kind, data) for name, (kind, data) in template.items()]
    entries += metadata_entries(np.zeros(192, dtype=np.float32), 1)
    path = output / 'weights.tfwc2'
    pack.write_tensor_file_v2(str(path), entries)
    decoded = pack.read_tensor_file_v2(str(path))
    if any(kind != decoded[name][0] or not np.array_equal(data, decoded[name][1]) for name, kind, data in entries):
        raise ValueError('zero-control packing differs')


def source_package(path, members):
    # Same deterministic source-only representation on both sides. All counted
    # native sources and dictionary included; packed model priced separately.
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(members.items()):
            if name.startswith('models/'):
                continue
            info = zipfile.ZipInfo(name, (2026, 9, 19, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)


def run(root, output, experiment_path, closure_path, plan_path):
    experiment = json.loads(experiment_path.read_bytes())
    plan = json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root / row['path'], root)['sha256'] != row['sha256'].removeprefix('sha256:'):
            raise ValueError('bound input differs: ' + row['path'])
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / 'snapshot'
    materialize(root, json.loads(closure_path.read_bytes()), snapshot)
    native = output / 'native'; native.mkdir()
    members, changes = adapt(snapshot / plan['native_source_zip'], snapshot / 'lib')
    for name, data in members.items():
        path = native / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
    write(output / 'native-adaptation.json', {'changes': changes})
    source_package(output / 'parent-source.zip', source_members(snapshot / plan['native_source_zip']))
    source_package(output / 'title-source.zip', members)
    env = {'PATH': '/usr/bin:/bin', 'PYTHONPATH': str(snapshot / 'src'),
           'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
           'OPENBLAS_NUM_THREADS': '1', 'TMPDIR': str(native), 'PYTHONHASHSEED': '0',
           'GAMMA_FX2_TITLE_CAPTURE': str(native / 'current-title')}
    caps = plan['caps']
    context = ExecutionContext(experiment['experimentId'], snapshot, native,
        ResourceBudget(tuple(caps['cpus']), caps['memory_bytes'], caps['scratch_bytes'], caps['wall_seconds']),
        BuildProfile(tuple(plan['compile_command']), tuple(map(tuple, plan['build_tools']))), tuple(env.items()))
    records, witnesses = [], []
    with CgroupMemoryGuard.current(caps['memory_bytes']) as resident_guard:
        executor = CommandExecutor(context, resident_guard=resident_guard)
        def phase(name, argv, seconds=240):
            for tool, digest in plan['build_tools']:
                if hashlib.sha256(Path(tool).read_bytes()).hexdigest() != digest:
                    raise ValueError('build/runtime tool changed')
            outcome, row = executor.run(name, argv,
                PhaseLimits(seconds, seconds + 10, plan['address_space_bytes'], caps['scratch_bytes']))
            records.append(row)
            scratch = native / 'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file(): raise ValueError('unexpected PPM scratch')
                scratch.unlink()
            if outcome.classification != 'completed': raise RuntimeError('phase failed: ' + name)

        def capture(name):
            identities = {}
            for suffix in ('features', 'state', 'raw'):
                path = native / ('current-title.' + suffix)
                identity = fingerprint(path, root)
                identities[suffix] = {k: identity[k] for k in ('sha256', 'bytes')}
                if name == 'K-encode':
                    path.rename(native / ('title.' + suffix))
                else:
                    expected = fingerprint(native / ('title.' + suffix), root)
                    if identity['sha256'] != expected['sha256'] or identity['bytes'] != expected['bytes']:
                        raise ValueError('introduced memory/feature/raw witness differs: ' + name + '/' + suffix)
                    path.unlink()
            witnesses.append({'phase': name, 'identities': identities, 'equals_K_encode': True})

        phase('build', plan['compile_command'], 300)
        executable = str(native / 'cmix')
        dictionary = str(native / 'dictionary/english.dic')
        raw = snapshot / plan['raw']
        models = {'P': snapshot / plan['parent_packed'], 'E': snapshot / plan['entropy_packed']}
        entry = snapshot / 'tools/fx2_title_gate_v1.py'
        common = [plan['python'], str(entry), '--root', str(snapshot), '--plan', str(snapshot / plan_path.relative_to(root))]
        phase('K-prepare', common + ['--phase', 'prepare', '--output', str(native / 'K')])
        models['K'] = native / 'K/weights.tfwc2'
        for arm in ('P', 'E'):
            phase(arm + '-encode', [executable, '-c', dictionary, str(raw), str(native / (arm + '.arc')), '--transformer', str(models[arm])])
            reference = snapshot / plan['parent_archive' if arm == 'P' else 'entropy_archive']
            if fingerprint(native / (arm + '.arc'), root)['sha256'] != fingerprint(reference, root)['sha256']:
                raise ValueError('native source adaptation changed baseline ' + arm)
        for arm in ('K', 'M', 'S'):
            if arm != 'K':
                phase(arm + '-train', common + ['--phase', 'train', '--output', str(native / arm),
                       '--features', str(native / 'title.features'), '--mode', '1' if arm == 'M' else '2'], 900)
                models[arm] = native / arm / 'weights.tfwc2'
            for name, mode, source, destination in (
                ('encode', '-c', raw, native / (arm + '.arc')),
                ('decode', '-d', native / (arm + '.arc'), native / (arm + '.raw')),
                ('repeat', '-c', native / (arm + '.raw'), native / (arm + '.repeat.arc'))):
                command = [executable, mode, dictionary, str(source), str(destination), '--transformer', str(models[arm])]
                if name == 'encode': command += ['--save-ppmd-probs', str(native / (arm + '.priors'))]
                phase(arm + '-' + name, command)
                capture(arm + '-' + name)
                if name == 'encode':
                    for suffix, key in (('', 'priors'), ('.tokens', 'tokens')):
                        observed = native / (arm + '.priors' + suffix)
                        if fingerprint(observed, root)['sha256'] != fingerprint(snapshot / plan[key], root)['sha256']:
                            raise ValueError('metadata changes PPMD or native token/reset population')
                        observed.unlink()
            if (native / (arm + '.raw')).read_bytes() != raw.read_bytes() or (native / (arm + '.repeat.arc')).read_bytes() != (native / (arm + '.arc')).read_bytes():
                raise ValueError('native inverse or repeat differs: ' + arm)
            if arm == 'K':
                if (native / 'K.arc').read_bytes() != (native / 'E.arc').read_bytes():
                    raise ValueError('zero metadata path changed E')
                if (native / 'title.raw').read_bytes() != raw.read_bytes():
                    raise ValueError('metadata inverse differs from canonical raw prefix')
        archives = {arm: (native / (arm + '.arc')).stat().st_size for arm in models}
        weights = {arm: path.stat().st_size for arm, path in models.items()}
        executable_delta = (native / 'cmix').stat().st_size - (snapshot / plan['parent_executable']).stat().st_size
        source_delta = (output / 'title-source.zip').stat().st_size - (output / 'parent-source.zip').stat().st_size
        result = {'schema': 'gamma.enwiki9.fx2-title-comparison.v1', 'candidate_id': experiment['experimentId'],
                  'objective': experiment['objective'], 'archive_bytes': archives, 'packed_model_bytes': weights,
                  'metadata_sample_gain_over_E': archives['E'] - archives['M'],
                  'aligned_gain_over_wrong': archives['S'] - archives['M'],
                  'two_copy_weight_gain_over_E': 2 * (weights['E'] - weights['M']),
                  'native_executable_delta': executable_delta, 'canonical_source_zip_delta': source_delta,
                  'declared_option_delta': 0, 'independent_inverse': True, 'raw_repeat': True,
                  'zero_control_exact': True, 'baseline_archive_identities': True, 'capture_alignment': True,
                  'witness_scope': 'introduced metadata memory, matched causal features and complete raw WRT inverse; excludes full parent state',
                  'witnesses': witnesses, 'commands': records, 'objective_credit_bytes': 0,
                  'full_corpus_score_bytes': None, 'promotion_authorized': False,
                  'accounting_scope': 'actual archive and packed weights; source-only ZIP and executable deltas separately measured; self-extracting delivery not constructed',
                  'limitations': ['exposed 250KB development only', 'CPU reference and truncated warmup training surrogate',
                                  'title token bags lose order; previous titles can be related',
                                  '1MB replay and resource qualification remain separate gates']}
        result['sample_plus_weight_delta_over_E'] = result['metadata_sample_gain_over_E'] + result['two_copy_weight_gain_over_E']
        result['two_executable_planning_delta_over_E'] = result['sample_plus_weight_delta_over_E'] - 2 * executable_delta
        result['fixed_configuration_lost'] = result['two_executable_planning_delta_over_E'] <= 0 or result['aligned_gain_over_wrong'] <= 0
        write(output / 'comparison.json', result)
        # Retain one exact lossless witness. Other runs were compared byte-for-byte
        # by authenticated SHA-256; their identities are retained above.
        for suffix in ('features', 'state', 'raw'):
            path = native / ('title.' + suffix)
            with path.open('rb') as source, (native / ('title.' + suffix + '.gz')).open('xb') as sink:
                with gzip.GzipFile(filename='', mode='wb', fileobj=sink, mtime=0) as compressed:
                    shutil.copyfileobj(source, compressed, 1 << 20)
            path.unlink()
        write(output / 'artifacts.json', {'artifacts': [fingerprint(p, root) for p in sorted(output.rglob('*')) if p.is_file()]})
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('run', 'prepare', 'train'), default='run')
    for name in ('root', 'output', 'plan'): parser.add_argument('--' + name, type=Path, required=True)
    for name in ('experiment', 'closure', 'features'): parser.add_argument('--' + name, type=Path)
    parser.add_argument('--mode', type=int, choices=(1, 2))
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    if args.phase == 'prepare': prepare_zero(args.root, args.output, plan)
    elif args.phase == 'train':
        from .fx2_title_development import train
        print('[run-contract] lane=compression profile=fx2_cpu_title_reference_v1 device=cpu population=exposed-opening250k steps=16 mode=' + str(args.mode), flush=True)
        train(upstream=args.root / plan['upstream'], checkpoint=args.root / plan['checkpoint'],
              parent_packed=args.root / plan['parent_packed'], token_path=args.root / plan['tokens'],
              prior_path=args.root / plan['priors'], feature_path=args.features, mode=args.mode,
              output=args.output, plan=plan['training'])
    else:
        result = run(args.root.resolve(), args.output.resolve(), args.experiment.resolve(), args.closure.resolve(), args.plan.resolve())
        print(json.dumps({k: result[k] for k in ('archive_bytes', 'packed_model_bytes', 'two_executable_planning_delta_over_E')}))

if __name__ == '__main__': main()
