"""Bounded fixed-parent opportunity attribution; never a finite-codec result."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint, publish_immutable_artifact
from gamma_enwiki9.evidence.history import materialize
from gamma_enwiki9.execution.commands import CommandExecutor, PhaseLimits
from gamma_enwiki9.execution.memory import CgroupMemoryGuard
from gamma_enwiki9.types import BuildProfile, ExecutionContext, ResourceBudget


def write(path, value):
    publish_immutable_artifact(path, canonical_bytes(value) + b'\n')


def run(root, output, experiment_path, closure_path, plan_path):
    experiment = json.loads(experiment_path.read_bytes())
    plan = json.loads(plan_path.read_bytes())
    for row in experiment['inputs']:
        if fingerprint(root / row['path'], root)['sha256'] != row['sha256'].removeprefix('sha256:'):
            raise ValueError('bound input changed: ' + row['path'])
    for path, digest in plan['build_tools']:
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError('build tool changed: ' + path)
    output.mkdir(parents=True, exist_ok=True)
    snapshot = output / 'snapshot'
    materialize(root, json.loads(closure_path.read_bytes()), snapshot)
    work = output / 'work'
    work.mkdir()
    caps = plan['caps']
    command = ['/usr/bin/g++', '-std=c++17', '-O2', '-Wall', '-Wextra',
               '-Wno-misleading-indentation', '-Werror', '-fsanitize=undefined',
               '-fno-sanitize-recover=all', '-I', str(snapshot / 'lib'),
               str(snapshot / plan['source']), '-o', str(work / 'coverage')]
    context = ExecutionContext(
        experiment['experimentId'], snapshot, work,
        ResourceBudget(tuple(caps['cpus']), caps['memory_bytes'], caps['scratch_bytes'], caps['wall_seconds']),
        BuildProfile(tuple(command), tuple(map(tuple, plan['build_tools']))),
        tuple({'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'TMPDIR': str(work)}.items()))
    records = []
    with CgroupMemoryGuard.current(caps['memory_bytes']) as guard:
        executor = CommandExecutor(context, resident_guard=guard)

        def phase(name, argv):
            outcome, record = executor.run(name, argv, PhaseLimits(60, 90, caps['memory_bytes'], caps['scratch_bytes']))
            records.append(record)
            write(output / (name + '.command.json'), record)
            if outcome.classification != 'completed':
                raise RuntimeError('phase failed: ' + name)
            print(json.dumps({'phase': name, 'elapsed_seconds': record['elapsed_seconds']}), flush=True)

        phase('build', command)
        for label in ('replay', 'repeat'):
            phase(label, [str(work / 'coverage'), str(snapshot / plan['dictionary']),
                          str(snapshot / plan['trace']), str(snapshot / plan['raw']), str(work / label)])
        for suffix in ('.json', '.state', '.tsv'):
            if (work / ('replay' + suffix)).read_bytes() != (work / ('repeat' + suffix)).read_bytes():
                raise ValueError('repeat differs: ' + suffix)
        if (work / 'replay.state').read_bytes() != (snapshot / plan['state']).read_bytes():
            raise ValueError('sealed introduced-state witness differs')
        measured = json.loads((work / 'replay.json').read_bytes())
        original = json.loads((snapshot / plan['summary']).read_bytes())
        for key, value in measured['original'].items():
            if not math.isclose(value, original[key], rel_tol=0, abs_tol=1e-6):
                raise ValueError('original cost differs: ' + key)
        for key in ('all', 'additional_cap', 'additional_pool', 'additional_pair_filter'):
            cell = measured[key]
            cell['parent_minus_expert_bits'] = [cell['parent_bits'] - value for value in cell['expert_bits']]
            cell['early_minus_expert_bits'] = [cell['expert_bits'][0] - value for value in cell['expert_bits']]
            if any(value > cell['parent_bits'] + 1e-7 for value in cell['parent_minus_expert_bits']):
                raise ValueError('perfect-prediction ceiling violated')
        # Numeric discriminator frozen before observing the development result.
        transfer_supported = (
            measured['additional_pool']['parent_bits'] >= plan['minimum_ceiling_bits']
            and measured['all']['expert_bits'][2] < measured['all']['parent_bits']
            and measured['all']['expert_bits'][2] < measured['all']['expert_bits'][0])
        result = {
            'schema': 'gamma.enwiki9.donor-coverage-comparison.v1',
            'candidate_id': experiment['experimentId'], 'measurements': measured,
            'arm_order': ['early_four_paired', 'all_paired_rights', 'all_retained'],
            'transfer_supported': transfer_supported,
            'parent_trace_fixed': True, 'raw_exact': True, 'original_state_exact': True,
            'repeat_exact': True, 'objective_credit_bytes': 0, 'full_corpus_score_bytes': None,
            'finite_archive_bytes': None, 'delivery_increment_bytes': None,
            'commands': records, 'policy': plan['policy'], 'limits': plan['limits'],
        }
        write(output / 'comparison.json', result)
    write(output / 'artifacts.json', {'artifacts': [fingerprint(p, root) for p in sorted(output.rglob('*')) if p.is_file()]})
    return result


def main():
    parser = argparse.ArgumentParser()
    for key in ('root', 'output', 'experiment', 'closure', 'plan'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    result = run(*(getattr(args, key).resolve() for key in ('root', 'output', 'experiment', 'closure', 'plan')))
    print(json.dumps({'transfer_supported': result['transfer_supported']}))


if __name__ == '__main__':
    main()
