"""No-fitting native P/E/K/M/S replay on one explicitly retained population."""
from __future__ import annotations
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget
from .fx2_title_native import adapt


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value) + b'\n')


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
    env = {'PATH': '/usr/bin:/bin', 'PYTHONDONTWRITEBYTECODE': '1', 'OMP_NUM_THREADS': '1',
           'TMPDIR': str(native), 'LC_ALL': 'C', 'GAMMA_FX2_TITLE_CAPTURE': str(native / 'current-title')}
    caps = plan['caps']
    context = ExecutionContext(experiment['experimentId'], snapshot, native,
        ResourceBudget(tuple(caps['cpus']), caps['memory_bytes'], caps['scratch_bytes'], caps['wall_seconds']),
        BuildProfile(tuple(plan['compile_command']), tuple(map(tuple, plan['build_tools']))), tuple(env.items()))
    records, witnesses = [], []
    with CgroupMemoryGuard.current(caps['memory_bytes']) as resident_guard:
        executor = CommandExecutor(context, resident_guard=resident_guard)
        def phase(name, argv, seconds=360):
            for tool, digest in plan['build_tools']:
                if hashlib.sha256(Path(tool).read_bytes()).hexdigest() != digest:
                    raise ValueError('build tool changed')
            measured = ['/usr/bin/time', '-f', '{"maximum_process_rss_kib":%M,"user_seconds":%U,"system_seconds":%S,"exit_status":%x}',
                        '-o', str(native / (name + '.rusage.json')), *argv]
            outcome, row = executor.run(name, measured,
                PhaseLimits(seconds, seconds + 10, plan['address_space_bytes'], caps['scratch_bytes']))
            records.append(row)
            scratch = native / 'ppm.temp'
            if scratch.exists():
                if scratch.is_symlink() or not scratch.is_file(): raise ValueError('unexpected PPM scratch')
                scratch.unlink()
            if outcome.classification != 'completed': raise RuntimeError('phase failed: ' + name)
            row['native_rusage'] = json.loads((native / (name + '.rusage.json')).read_bytes())
            row['rss_scope'] = 'GNU time wait4 maximum process RSS, not simultaneous aggregate tree RSS; outer cgroup supplies aggregate job peak'

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

        phase('build', plan['compile_command'])
        executable = str(native / 'cmix')
        if fingerprint(native / 'cmix', root)['sha256'] != fingerprint(snapshot / plan['development_executable'], root)['sha256']:
            raise ValueError('rebuild differs from development binary')
        dictionary = str(native / 'dictionary/english.dic')
        raw = snapshot / plan['raw']
        models = {arm: snapshot / name for arm, name in plan['models'].items()}
        for arm in ('P', 'E', 'K', 'M', 'S'):
            phases = [('encode', '-c', raw, native / (arm + '.arc'))]
            if arm != 'K':
                phases += [('decode', '-d', native / (arm + '.arc'), native / (arm + '.raw')),
                           ('repeat', '-c', native / (arm + '.raw'), native / (arm + '.repeat.arc'))]
            for name, mode, source, destination in phases:
                phase(arm + '-' + name, [executable, mode, dictionary, str(source), str(destination), '--transformer', str(models[arm])])
                if arm in ('K', 'M', 'S'): capture(arm + '-' + name)
            if arm != 'K':
                if (native / (arm + '.raw')).read_bytes() != raw.read_bytes() or (native / (arm + '.repeat.arc')).read_bytes() != (native / (arm + '.arc')).read_bytes():
                    raise ValueError('native inverse or repeat differs: ' + arm)
            if arm == 'P' and (native / 'P.arc').read_bytes() != (snapshot / plan['parent_archive']).read_bytes():
                raise ValueError('parent differs from retained 1MB native baseline')
            if arm == 'K':
                if (native / 'K.arc').read_bytes() != (native / 'E.arc').read_bytes():
                    raise ValueError('zero metadata path changed E')
                if (native / 'title.raw').read_bytes() != raw.read_bytes():
                    raise ValueError('metadata inverse differs from canonical raw population')
                if (native / 'title.features').stat().st_size != plan['scope_symbols'] * 411:
                    raise ValueError('metadata population differs from retained WRT geometry')
        archives = {arm: (native / (arm + '.arc')).stat().st_size for arm in models}
        weights = {arm: path.stat().st_size for arm, path in models.items()}
        result = {'schema': 'gamma.enwiki9.fx2-joint-replay.v1', 'candidate_id': experiment['experimentId'],
                  'objective': experiment['objective'], 'population': plan['population'],
                  'archive_bytes': archives, 'packed_model_bytes': weights,
                  'archive_gain_E_over_P': archives['P'] - archives['E'],
                  'metadata_archive_gain_over_E': archives['E'] - archives['M'],
                  'aligned_gain_over_wrong': archives['S'] - archives['M'],
                  'model_identities_unchanged': True, 'native_rebuild_identity': True,
                  'independent_inverse': True, 'raw_repeat': True, 'zero_control_exact': True,
                  'K_scope': 'fresh encode equality to E; K inverse/repeat measured at250KB, not repeated here',
                  'parent_archive_identity': True,
                  'witness_scope': 'introduced metadata memory, features and complete raw WRT inverse; not complete parent state',
                  'witnesses': witnesses, 'commands': records, 'objective_credit_bytes': 0,
                  'full_corpus_score_bytes': None, 'promotion_authorized': False,
                  'development_pricing': plan['development_comparison'],
                  'accounting_scope': 'finite archives and frozen packed models; source/executable/options differences unchanged from development; complete delivery not constructed',
                  'limitations': ['already exposed 1MB population, outside current training windows',
                                  'no fitting, rescue, model selection or additional populations',
                                  'no full-corpus extrapolation or resource qualification']}
        result['sample_plus_weight_delta_E_over_P'] = archives['P'] - archives['E'] + 2 * (weights['P'] - weights['E'])
        result['sample_plus_weight_delta_M_over_E'] = archives['E'] - archives['M'] + 2 * (weights['E'] - weights['M'])
        development = json.loads((snapshot / plan['development_comparison']).read_bytes())
        result['two_executable_planning_delta_M_over_E'] = result['sample_plus_weight_delta_M_over_E'] - 2 * development['native_executable_delta']
        result['fixed_configuration_lost'] = result['two_executable_planning_delta_M_over_E'] <= 0 or archives['M'] >= archives['S']
        write(output / 'comparison.json', result)
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
    for name in ('root', 'output', 'plan', 'experiment', 'closure'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root.resolve(), args.output.resolve(), args.experiment.resolve(), args.closure.resolve(), args.plan.resolve())
    print(json.dumps({k: result[k] for k in ('archive_bytes', 'packed_model_bytes', 'sample_plus_weight_delta_E_over_P')}))

if __name__ == '__main__': main()
