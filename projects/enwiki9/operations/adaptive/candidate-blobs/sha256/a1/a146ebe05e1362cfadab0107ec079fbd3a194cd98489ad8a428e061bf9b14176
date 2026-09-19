"""Bounded census and fixed seven-arm causal-history comparison."""
import argparse
import json
import os
from pathlib import Path
import sys
import zlib

from lib.coders import xml_history_deflate_v1 as codec
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value) + b'\n')


def run(root, output, experiment_path, closure_path, cpu):
    experiment = json.loads(experiment_path.read_bytes())
    for item in experiment['inputs']:
        actual = fingerprint(root / item['path'], root)
        if actual['sha256'] != item['sha256'].removeprefix('sha256:'):
            raise ValueError('bound input differs: ' + item['path'])
    population = next(i for i in experiment['inputs'] if i['id'] == 'population')
    raw = (root / population['path']).read_bytes()
    if len(raw) != 250000:
        raise ValueError('wrong population')
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / 'snapshot'
    materialize(root, json.loads(closure_path.read_bytes()), snapshot)
    write(output / 'census.json', codec.census(raw))
    env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'PYTHONDONTWRITEBYTECODE': '1',
           'PYTHONPATH': str(snapshot) + os.pathsep + str(snapshot / 'src')}
    context = ExecutionContext(experiment['experimentId'], snapshot, output,
        ResourceBudget((cpu,), 512*1024**2, 64*1024**2, 180),
        BuildProfile((sys.executable,), (('zlib', zlib.ZLIB_RUNTIME_VERSION),)), tuple(env.items()))
    executor, limits = CommandExecutor(context), PhaseLimits(15, 20, 256*1024**2, 8*1024**2)
    entry = snapshot / 'tools/xml_history_gate_v1.py'
    commands, rows = [], {}
    for arm in codec.ARMS:
        archive, inverse, repeat = (output / (arm + suffix) for suffix in ('.arc', '.raw', '.repeat.arc'))
        phases = [('encode', snapshot / population['path'], archive),
                  ('decode', archive, inverse), ('repeat', inverse, repeat)]
        reports = []
        for phase, source, destination in phases:
            argv = [sys.executable, str(entry), '--phase', 'decode' if phase == 'decode' else 'encode',
                    '--input', str(source), '--output', str(destination), '--arm', arm]
            outcome, command = executor.run(arm + '-' + phase, argv, limits)
            commands.append(command)
            if outcome.classification != 'completed':
                raise RuntimeError('phase failed: ' + arm + '-' + phase)
            reports.append(json.loads((output / (arm + '-' + phase + '.stdout')).read_bytes()))
        if inverse.read_bytes() != raw or repeat.read_bytes() != archive.read_bytes() or reports[0] != reports[1] or reports[0] != reports[2]:
            raise ValueError('inverse, repeat or common witness differs: ' + arm)
        if sum(reports[0]['costs'].values()) != archive.stat().st_size:
            raise ValueError('accounting differs')
        rows[arm] = reports[0]
    if (output / 'B.arc').read_bytes() != (output / 'K.arc').read_bytes():
        raise ValueError('bookkeeping changed archive')
    if rows['J']['cross_events'] != rows['S']['cross_events']:
        raise ValueError('shifted opportunities differ')
    source = fingerprint(root / 'lib/coders/xml_history_deflate_v1.py', root)
    result = {'schema': 'gamma.enwiki9.xml-history-diagnostic.v1',
        'candidate_id': experiment['experimentId'], 'objective': experiment['objective'],
        'execution': {'classification': 'completed', 'commands': commands},
        'evidence': {'verified': True, 'independent_inverse': True, 'raw_repeat': True,
                     'common_witness': True, 'bookkeeping_identity': True, 'bound_inputs': True},
        'archive_bytes': {k: v['archive_bytes'] for k, v in rows.items()}, 'arms': rows,
        'gains_vs_split_B': {k: rows['B']['archive_bytes']-v['archive_bytes'] for k, v in rows.items()},
        'joint_gain_vs_unsplit_P': rows['P']['archive_bytes']-rows['J']['archive_bytes'],
        'joint_gain_vs_shifted_S': rows['S']['archive_bytes']-rows['J']['archive_bytes'],
        'known_codec_source': source,
        'local_source_plus_archive': {k: source['bytes']+v['archive_bytes'] for k, v in rows.items()},
        'runtime': {'python': sys.version, 'zlib': zlib.ZLIB_RUNTIME_VERSION,
                    'python_executable': fingerprint(Path(sys.executable).resolve(), Path('/')),
                    'zlib_extension': fingerprint(Path(zlib.__file__), Path('/'))},
        'decision': 'hold', 'objective_credit_bytes': 0, 'promotion_authorized': False,
        'fixed_configuration_lost': rows['J']['archive_bytes'] >= rows['P']['archive_bytes'],
        'limitations': ['already exposed opening250k only', 'Deflate diagnostic, not native parent',
            'shifted donors can remain topically related', 'no confirmation or full-corpus measurement',
            'local source inventory excludes Python/zlib delivery accounting; no qualified package score',
            'page-local word census and prefix-history codec have distinct declared memory policies']}
    write(output / 'comparison.json', result)
    # Includes the snapshot, all phase output, inverse, archive and repeat bytes.
    artifacts = [fingerprint(p, root) for p in sorted(output.rglob('*')) if p.is_file()]
    write(output / 'artifacts.json', {'artifacts': artifacts, 'excluded_self': 'artifacts.json'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['run', 'encode', 'decode'], default='run')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arm', choices=list(codec.ARMS), default='J')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--experiment', type=Path)
    parser.add_argument('--closure', type=Path)
    parser.add_argument('--cpu', type=int)
    args = parser.parse_args()
    if args.phase != 'run':
        data = args.input.read_bytes()
        payload, report = codec.decompress(data) if args.phase == 'decode' else codec.compress(data, args.arm)
        publish_immutable_artifact(args.output, payload)
        print(json.dumps(report, sort_keys=True))
    else:
        result = run(args.root.resolve(), args.output.resolve(), args.experiment, args.closure, args.cpu)
        print(json.dumps({'archive_bytes': result['archive_bytes'], 'decision': result['decision']}, sort_keys=True))


if __name__ == '__main__':
    main()
