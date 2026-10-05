"""Full donor encode, repeat and restricted inverse using an immutable rebuild."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from gamma_enwiki9.adapters.fx2_package_gate import sandbox
from gamma_enwiki9.adapters.lexth11c_reproduction import accounting, layout, write
from gamma_enwiki9.evidence.artifacts import fingerprint
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget


def restricted(runtime, work, argv, raw=None, weights=None):
    cmd = sandbox(runtime, work, argv, raw)
    index = cmd.index('--')
    extra = ['--dir', '/bin', '--ro-bind', runtime['shell']['resolved_path'], '/bin/sh']
    if weights is not None:
        extra += ['--ro-bind', str(weights), '/weights']
    cmd[index:index] = extra
    return cmd


def run(root: Path, output: Path, experiment: Path, plan: Path) -> int:
    exp = json.loads(experiment.read_bytes())
    cfg = json.loads(plan.read_bytes())
    bound = {'path': experiment.relative_to(root).as_posix(),
             'sha256': 'sha256:' + hashlib.sha256(experiment.read_bytes()).hexdigest()}
    if json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) != bound:
        raise ValueError('lab experiment binding differs')
    for row in exp['inputs']:
        if fingerprint(root / row['path'], root)['sha256'] != row['sha256'].removeprefix('sha256:'):
            raise ValueError('input differs: ' + row['path'])
    runtime = cfg['runtime']
    for row in [runtime['bwrap'], runtime['shell'], *runtime['providers'].values()]:
        path = Path(row['resolved_path'])
        if fingerprint(path, path.parent)['sha256'] != row['sha256']:
            raise ValueError('runtime provider differs')
    caps = cfg['caps']
    ctx = ExecutionContext(exp['experimentId'], root, output,
        ResourceBudget(tuple(caps['cpus']), caps['memory_bytes'], caps['scratch_bytes'], caps['wall_seconds']),
        BuildProfile((), ()), (('PATH', '/usr/bin:/bin'), ('LC_ALL', 'C')))
    phases = []
    checks = {}
    score = None
    ok = True
    error = None
    write(output / 'launch.json', {'experiment': bound, 'caps': caps, 'runtime': runtime,
        'qualification': False, 'full_corpus_score_bytes': None,
        'scope': 'Complete canonical enwik9; independently restricted decode has no corpus/source mount.',
        'qualification_memory_limit_bytes': 10000000000,
        'diagnostic_memory_limit_bytes': caps['memory_bytes'], 'prior_capture': False})
    compressor = root / cfg['compressor']
    raw = root / cfg['raw']
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor = CommandExecutor(ctx, resident_guard=guard)

        def phase(name, work, argv, source=None, weights=None):
            command = restricted(runtime, work, argv, source, weights)
            write(output / (name + '-launch.json'), {'command': command, 'raw_access': source is not None})
            outcome, record = executor.run(name, command,
                PhaseLimits(caps['wall_seconds'], caps['wall_seconds'], 68719476736, caps['scratch_bytes']))
            phases.append(record)
            if outcome.classification != 'completed':
                raise RuntimeError(name + ': ' + outcome.classification)

        try:
            # First establish that the narrower pinned runtime preserves the control.
            canary = output / 'canary'
            canary.mkdir()
            shutil.copyfile(compressor, canary / 'cmix')
            (canary / 'cmix').chmod(0o755)
            phase('runtime-control', canary, ['./cmix', '-n', '--transformer', '/weights',
                '--save-transformer-probs', '/work/control.probs', '/input', '/work/control.arc'],
                root / cfg['fixture'], root / cfg['weights'])
            for suffix in ['arc', 'probs']:
                checks['runtime_' + suffix + '_equal'] = fingerprint(canary / ('control.' + suffix), root)['sha256'] == fingerprint(root / cfg['control_' + suffix], root)['sha256']
            if not all(checks.values()):
                raise ValueError('restricted runtime control differs')
            for arm in ['encode', 'repeat']:
                work = output / arm
                work.mkdir()
                shutil.copyfile(compressor, work / 'cmix')
                (work / 'cmix').chmod(0o755)
                phase(arm, work, ['./cmix', '-e', '/input', 'o'], raw)
                blob = (work / 'archive9').read_bytes()
                layout(blob, archive=True)
                write(output / (arm + '-artifact.json'), fingerprint(work / 'archive9', root))
            checks['full_archive_repeat_equal'] = fingerprint(output / 'encode/archive9', root)['sha256'] == fingerprint(output / 'repeat/archive9', root)['sha256']
            if not checks['full_archive_repeat_equal']:
                raise ValueError('full archive repeat differs')
            work = output / 'decode'
            work.mkdir()
            shutil.copyfile(output / 'encode/archive9', work / 'archive9')
            (work / 'archive9').chmod(0o755)
            phase('decode', work, ['./archive9'])
            restored = fingerprint(work / 'enwik9_uncompressed', root)
            checks['full_exact_inverse'] = restored['bytes'] == exp['objective']['corpusBytes'] and restored['sha256'] == exp['objective']['corpusSha256']
            write(output / 'restored-artifact.json', restored)
            produced = (output / 'encode/archive9').read_bytes()
            score = accounting(compressor.read_bytes(), produced, cfg['required_option_bytes'])
            released = (root / cfg['released_archive']).read_bytes()
            a = layout(produced, archive=True)
            b = layout(released, archive=True)
            checks['released_payload_equal'] = produced[-16-a['payload_bytes']:-16] == released[-16-b['payload_bytes']:-16]
            # A measured difference is retained, never replaced with the donor's score.
            write(output / 'accounting.json', score)
        except (RuntimeError, ValueError, OSError) as exc:
            ok = False
            error = str(exc)
    required = ['runtime_arc_equal', 'runtime_probs_equal', 'full_archive_repeat_equal', 'full_exact_inverse']
    ok = ok and all(checks.get(name, False) for name in required)
    result = {'schema': 'gamma.enwiki9.full-donor-control.v1', 'experiment': bound,
        'status': 'reproduced' if ok else 'failed', 'error': error, 'checks': checks,
        'phases': phases, 'accounting': score, 'complete_donor_replay_verified': ok, 'complete_score_measured': ok,
        'complete_score_reproduced': bool(ok and score['S'] == cfg['released_complete_bytes']),
        'full_corpus_score_bytes': score['S'] if ok else None,
        'qualification': False, 'objective_credit_bytes': 0, 'prior_capture': False,
        'released_score_equal': bool(ok and score['S'] == cfg['released_complete_bytes']),
        'required_option_bytes': cfg['required_option_bytes']}
    write(output / 'result.json', result)
    print(json.dumps(result), flush=True)
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'output', 'experiment', 'plan']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    return run(*(getattr(args, name).resolve() for name in ['root', 'output', 'experiment', 'plan']))
