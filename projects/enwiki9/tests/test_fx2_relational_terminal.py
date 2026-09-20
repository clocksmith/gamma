"""A closed tiny evidence bundle exercises terminal certification without codecs."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gamma_enwiki9.adapters import fx2_relational_terminal as terminal
from gamma_enwiki9.evidence.artifacts import canonical_bytes, fingerprint


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    root = tmp_path
    name, job_id = 'relational-fixture', 'test-job'
    output = root / 'results' / name
    native = output / 'native'

    def put(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else canonical_bytes(value))
        return fingerprint(path, root)

    # Bind the interpreter inside the fixture's project, as a real terminal does.
    implementation = root / 'interpreter.py'
    put(implementation, Path(terminal.__file__).read_bytes())
    monkeypatch.setattr(terminal, '__file__', str(implementation))
    parent_path = 'results/parent/cmix'
    parent = put(output / 'snapshot' / parent_path, b'parent')
    # The mutable checkout deliberately has different parent bytes.
    put(root / parent_path, b'changed checkout parent bytes')
    binary = put(native / 'cmix', b'parent' + b'added')
    source = put(output / 'S-source.zip', b'source-added')
    put(output / 'P-source.zip', b'source')
    increment = min(2 * 5, 6 + 5) + len('GAMMA_RELATIONAL_ARM=S')
    package = {'binary': binary, 'source': source, 'counted_increment': increment}
    populations = ('development', 'validation', 'confirmation')
    plan = {'parent_binary': parent_path, 'populations': {}}
    inputs = [{'path': parent_path, 'sha256': parent['sha256']}]
    measurements = {}
    for pop in populations:
        raw = (pop + '-raw').encode()
        raw_path = 'fixtures/' + pop
        raw_ref = put(output / 'snapshot' / raw_path, raw)
        plan['populations'][pop] = {'raw': raw_path}
        inputs.append({'path': raw_path, 'sha256': raw_ref['sha256']})
        put(native / (pop + '-original.arc'), b'p' * 80)
        arms = measurements[pop] = {}
        for arm, size in zip('PKISW', (80, 80, 50, 40, 55)):
            prefix = pop + '-' + arm
            archive = (b'p' if arm in 'PK' else arm.encode()) * size
            arms[arm] = {
                'archive_bytes': size,
                'archive': put(native / (prefix + '.arc'), archive),
                'repeat': put(native / (prefix + '.repeat.arc'), archive),
                'inverse': put(native / (prefix + '.decoded'), raw),
                'exact_inverse': True, 'repeat_exact': True,
                'parent_predictions_exact': True, 'introduced_state_exact': True,
                'diagnostics': {'relation_bits': 1, 'parent_bits': 1, 'mixed_bits': 1},
            }
            for action in ('encode', 'decode', 'repeat'):
                stem = native / (prefix + '-' + action)
                for suffix, data in (('raw', raw), ('state', b'same-state'),
                                     ('parent', b'same-parent'),
                                     ('json', arms[arm]['diagnostics'])):
                    put(Path(str(stem) + '.' + suffix), data)
    plan_path = root / 'operations/provenance' / (name + '_plan.json')
    inputs.append(put(plan_path, plan))
    experiment_path = root / 'operations/adaptive/experiments' / (name + '.json')
    experiment = put(experiment_path, {'inputs': inputs})
    guard_path = root / 'run_logs/guard.json'
    put(guard_path, {'status': 'complete', 'guards': {'exceeded': False},
                     'elapsed_s': 1, 'peaks': {'cgroup_memory_peak_bytes': 10,
                                              'max_sampled_scratch_allocated_bytes': 20}})
    job_path = root / 'operations/adaptive/completed' / ('001_' + job_id + '.json')
    job = {'candidate_id': name, 'job_id': job_id, 'state': 'completed',
           'returncode': 0, 'finished_at': '2026-09-20T00:00:00Z',
           'candidate_tree_sha256': 'a' * 64, 'candidate_revision': {},
           'experiment': experiment,
           'execution_resources': {'cleanup_complete': True,
                                   'guard_path': guard_path.relative_to(root).as_posix()}}
    put(job_path, job)
    phases = ['build', 'clean', 'build-repeat']
    for pop in populations:
        phases.append(pop + '-original')
        phases.extend(f'{pop}-{arm}-{action}' for arm in 'PKISW'
                      for action in ('encode', 'decode', 'repeat'))
    commands = []
    for phase in phases:
        command = {'phase': phase, 'returncode': 0, 'cleanup_complete': True,
                   'timeout': False, 'error': None, 'elapsed_seconds': 1}
        commands.append(command)
        put(output / (phase + '.command.json'), command)
    comparison = {'candidate_id': name, 'measurements': measurements,
                  'package': package, 'commands': commands, 'mechanism_supported': True}

    def seal(omit=None):
        put(output / 'comparison.json', comparison)
        artifacts = [fingerprint(p, root) for p in sorted(output.rglob('*'))
                     if p.is_file() and p.name != 'artifacts.json' and p != omit]
        put(output / 'artifacts.json', {'artifacts': artifacts})

    seal()
    return SimpleNamespace(root=root, output=output, native=native, name=name,
                           job_id=job_id, job=job, job_path=job_path,
                           comparison=comparison, put=put, seal=seal)


def run(b):
    return terminal.verify_and_publish(b.root, b.name, b.job_id)


def test_complete_bundle_uses_original_parent_and_is_idempotent(bundle):
    report = run(bundle)
    assert report['comparison_valid']
    assert report['binding_payload_supported_all_populations']
    assert report['frozen_paid_fixture_predicate']
    assert report['full_corpus_score_bytes'] is None
    assert len(json.loads((bundle.output / 'terminal-index.json').read_bytes())['arms']) == 15
    assert run(bundle) == report


@pytest.mark.parametrize('fault', [
    'duplicate-phase', 'failed-command', 'unretained-command', 'unretained-archive',
    'wrong-reference', 'different-shared-state', 'false-predicate', 'wrong-job',
    'changed-original-parent', 'missing-population', 'false-diagnostics',
])
def test_invalid_bundle_cannot_publish_terminal(bundle, fault):
    b = bundle
    omit = None
    if fault == 'duplicate-phase':
        b.comparison['commands'][-1] = b.comparison['commands'][-2]
    elif fault == 'failed-command':
        command = b.comparison['commands'][-1]
        command['returncode'] = 7
        b.put(b.output / (command['phase'] + '.command.json'), command)
    elif fault == 'unretained-command':
        omit = b.output / 'build.command.json'
    elif fault == 'unretained-archive':
        omit = b.native / 'development-S.arc'
    elif fault == 'wrong-reference':
        b.comparison['measurements']['development']['S']['archive']['sha256'] = '0' * 64
    elif fault == 'different-shared-state':
        # Every S replay still agrees; only the independent P/K/S comparison fails.
        for action in ('encode', 'decode', 'repeat'):
            b.put(b.native / ('development-S-' + action + '.state'), b'wrong state')
    elif fault == 'false-predicate':
        b.comparison['mechanism_supported'] = False
    elif fault == 'wrong-job':
        b.job['candidate_id'] = 'another-candidate'
        b.put(b.job_path, b.job)
    elif fault == 'changed-original-parent':
        b.put(b.output / 'snapshot/results/parent/cmix', b'changed parent')
    elif fault == 'missing-population':
        del b.comparison['measurements']['validation']
    elif fault == 'false-diagnostics':
        b.comparison['measurements']['development']['S']['diagnostics']['relation_bits'] = 0
    b.seal(omit)
    with pytest.raises(ValueError):
        run(b)
    assert not (b.output / 'terminal.json').exists()
    assert not (b.output / 'terminal-index.json').exists()
