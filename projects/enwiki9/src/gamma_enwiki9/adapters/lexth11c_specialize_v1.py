"""Measure a private CLI specialization without altering donor predictions.

The generated runner remains a GPLv3 derivative of Neel49's lexth11c runner.
The source copy retains its upstream license and attribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

from gamma_enwiki9.adapters.lexth11c_build_v3 import sandbox, write
from gamma_enwiki9.evidence.artifacts import fingerprint
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget


def specialize(original: str) -> str:
    start = original.index('int Help() {')
    end = original.index('\nstruct ExtractionOptions', start)
    help_text = '''int Help() {
  printf("cmix-lex (Neel49 lexth11c; Gamma CLI specialization)\\n");
  printf("Modes: -e enwik9 output; no arguments to decode enwik9;\\n");
  printf("-c dictionary input output; -n input output; -d input output;\\n");
  printf("-s dictionary input output; -h dict_size order_size payload_size weights_size.\\n");
  printf("Controls: --transformer weights; --save-transformer-probs output.\\n");
  return -1;
}
'''
    text = original[:start] + help_text + original[end:]
    start = text.index('    if (arg == "--ppmd-only") {')
    end = text.index('    else if (arg == "--save-transformer-probs")', start)
    replacement = '''    std::string* value = NULL;
    if (arg == "--transformer") value = &options.transformer;
'''
    return text[:start] + replacement + text[end:]


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
    for row in cfg['files']:
        if row.get('symlink') is not None:
            if os.readlink(root / row['path']) != row['symlink']:
                raise ValueError('symlink differs')
        elif fingerprint(root / row['path'], root)['sha256'] != row['sha256']:
            raise ValueError('tool/source differs: ' + row['path'])
    for row in cfg['host_providers']:
        path = Path(row['path'])
        if fingerprint(path, path.parent)['sha256'] != row['sha256']:
            raise ValueError('host provider differs')
    caps = cfg['caps']
    work = output / 'work'
    work.mkdir()
    entry = work / 'entry'
    upstream = root / 'external/lexth11c-campaign/release-source/lexth11c-src'
    shutil.copytree(upstream, entry)
    runner = entry / 'src/runner.cpp'
    runner.write_text(specialize(runner.read_text()))
    ctx = ExecutionContext(exp['experimentId'], root, output,
        ResourceBudget(tuple(caps['cpus']), caps['memory_bytes'], caps['scratch_bytes'], caps['wall_seconds']),
        BuildProfile((), ()), (('PATH', '/usr/bin:/bin'), ('LC_ALL', 'C')))
    phases = []
    comparisons = {}
    component = None
    ok = True

    def command(argv):
        cmd = sandbox(root, work, argv)
        index = cmd.index('/entry')
        cmd[index - 1] = str(entry)
        return cmd

    write(output / 'launch.json', {'experiment': bound, 'caps': caps,
        'qualification': False, 'generated_runner': fingerprint(runner, root),
        'source_derivation': 'Neel49 lexth11c GPLv3; only diagnostic long-option dispatch and Help changed.'})
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor = CommandExecutor(ctx, resident_guard=guard)

        def phase(name, argv, seconds=3600):
            nonlocal ok
            outcome, record = executor.run(name, command(argv),
                PhaseLimits(seconds, seconds, 68719476736, caps['scratch_bytes']))
            phases.append(record)
            ok = ok and outcome.classification == 'completed'
            return ok

        phase('build', ['bash', '/entry/build.sh'], caps['wall_seconds'])
        if ok:
            parent = root / 'results/lexth11c_rebuild_control_q0_v3/work/cmix'
            shutil.copyfile(parent, work / 'parent')
            (work / 'parent').chmod(0o755)
            for arm, binary in [('P', './parent'), ('A', './cmix'), ('R', './cmix')]:
                if not phase(arm, [binary, '-n', '--transformer', '/entry/models/lex_h1_run11.tfwc2',
                    '--save-transformer-probs', '/work/' + arm + '.probs',
                    '/entry/prof_input/input', '/work/' + arm + '.arc']):
                    break
            if ok:
                phase('inverse', ['./cmix', '-d', '--transformer', '/entry/models/lex_h1_run11.tfwc2',
                    '/work/A.arc', '/work/restored'])
            if ok:
                ok = fingerprint(work / 'restored', root)['sha256'] == fingerprint(upstream / 'prof_input/input', root)['sha256']
                for suffix in ['arc', 'probs']:
                    refs = {arm: fingerprint(work / (arm + '.' + suffix), root) for arm in ['P', 'A', 'R']}
                    equal = len({row['sha256'] for row in refs.values()}) == 1
                    comparisons[suffix] = {'files': refs, 'byte_equal': equal}
                    ok = ok and equal
                parent_run = root / 'results/lexth11c_rebuild_control_q0_v3/work/src/run'
                child_run = work / 'src/run'
                ps = (parent_run / 'cmix_orig').stat().st_size
                cs = (child_run / 'cmix_orig').stat().st_size
                component = {'parent_stub_bytes': ps, 'child_stub_bytes': cs,
                    'saving_per_stub_copy': ps - cs, 'counted_stub_saving_bytes': 2 * (ps - cs),
                    'net_component_saving_bytes': 2 * (ps - cs),
                    'full_payload_unchanged_verified': False, 'full_corpus_score_bytes': None}
                for name in ['comp_dict', 'comp_order', 'comp_tfweights']:
                    component[name + '_byte_equal'] = fingerprint(parent_run / name, root)['sha256'] == fingerprint(child_run / name, root)['sha256']
                    ok = ok and component[name + '_byte_equal']
    artifacts = {}
    for rel in ['cmix', 'src/run/cmix_orig', 'entry/src/runner.cpp', 'restored']:
        path = work / rel
        if path.is_file():
            artifacts[rel] = fingerprint(path, root)
    result = {'schema': 'gamma.enwiki9.executable-specialization-result.v1',
        'experiment': bound, 'status': 'control_pass' if ok else 'failed',
        'phases': phases, 'comparisons': comparisons, 'component': component, 'artifacts': artifacts,
        'qualification': False, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None,
        'control_scope': 'Causal raw50051-byte tagged fixture; actual packed model, dictionary, order and both executable copies.'}
    write(output / 'result.json', result)
    print(json.dumps(result), flush=True)
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['root', 'output', 'experiment', 'plan']:
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    return run(*(getattr(args, name).resolve() for name in ['root', 'output', 'experiment', 'plan']))
