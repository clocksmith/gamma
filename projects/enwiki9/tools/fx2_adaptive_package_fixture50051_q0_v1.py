#!/usr/bin/env python3
"""Frozen independent native package rebuild and exact public-fixture replay."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ID = 'fx2_adaptive_package_fixture50051_q0_v1'
SPEC = 'operations/provenance/fx2_adaptive_package_fixture_v1/spec.json'
MANIFEST = 'operations/provenance/fx2_adaptive_package_fixture_v1/bundle/dependency-closure.json'
CAPS = dict(cpus=[2], memory_bytes=9999998976, scratch_bytes=16000000000,
            swap_bytes=0, wall_seconds=900)


def bootstrap():
    path = ROOT / ('operations/adaptive/experiments/' + ID + '.json')
    inputs = {row['path']: row for row in json.loads(path.read_text())['inputs']}
    for name in ('tools/' + ID + '.py', 'lib/fx2_native_gate_v1.py', 'lib/artifacts.py'):
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != inputs[name]['sha256'].removeprefix('sha256:'):
            raise ValueError('bootstrap source changed')
    namespace = {}
    exec(compile((ROOT / 'lib/fx2_native_gate_v1.py').read_bytes(),
                 str(ROOT / 'lib/fx2_native_gate_v1.py'), 'exec'), namespace)
    return namespace['NativeGate']


def validate(gate):
    import enwiki9_native_package_replay_v1 as package
    spec = json.loads(gate.buffers[SPEC])
    parent = json.loads(gate.buffers[spec['parent_reflection']])
    terminal = json.loads(gate.buffers[spec['parent_terminal']])
    package.require(parent['validity']['valid'] and parent['decision']['promotionPredicatesPass'],
                    'parent transfer not selectable')
    package.require(gate.contract['parent'] == spec['parent'] and
                    parent['candidateId'] == spec['parent']['candidateId'], 'parent identity differs')
    package.require(parent['candidateRevision']['receipt'] == spec['parent']['revision'] and
                    any(row['path'] == spec['parent_terminal'] and
                        row['sha256'].removeprefix('sha256:') == hashlib.sha256(gate.buffers[spec['parent_terminal']]).hexdigest()
                        for row in parent['evidence']), 'parent evidence binding differs')
    package.require(terminal['status'] == 'passed' and terminal['all_parent_records_identical'],
                    'missing native transfer parity')
    package.require(spec['corpus']['bytes'] == 50051 and spec['archive']['bytes'] == 3223 and
                    spec['trace']['bytes'] == 7275072, 'wrong fixture population')
    package.require(spec['binary']['bytes'] == 496136 and spec['binary']['sha256'] ==
                    terminal['package_economics']['native_builds']['D']['sha256'], 'wrong expected build')
    fixture = json.loads(gate.buffers[spec['fixture_inputs']])['population']
    package.require(all(spec[key] == fixture['raw' if key == 'corpus' else key]
                        for key in ('corpus', 'archive', 'trace')), 'fixture binding differs')
    for row in spec['execution_tools']:
        package.match(Path(row['path']), row)
    package.validate(gate, MANIFEST, SPEC)
    return package


def main():
    if sys.argv[1:] not in ([], ['--validate-only']):
        raise ValueError('unexpected arguments')
    gate = bootstrap()(ROOT, ID, CAPS, bool(sys.argv[1:]))
    package = validate(gate)
    if sys.argv[1:]:
        print(json.dumps(dict(status='preflight_pass', inputs=len(gate.inputs), codec_executed=False)))
        return 0
    stage = dict(candidate_id=ID, experiment=gate.reference, objective_credit_bytes=0,
                 full_corpus_score_bytes=None, larger_gate_authorized=False,
                 continuous_guard_decision='pending canonical outer guard closure')
    try:
        gate.retain_sources()
        result = package.run(gate, MANIFEST, SPEC)
        if len(gate.commands) != 6:
            raise ValueError('package phase count differs')
        stage.update(status='passed', package_replay=gate.artifact(gate.result / 'package-replay.json'),
                     exact_inverse=result['exact_inverse'], exact_repeat=result['exact_repeat'],
                     native_coder_records_identical=result['native_coder_records_identical'])
    except Exception as error:
        stage.update(status='execution_failed', failure_class=getattr(error, 'category', 'invariant_or_missing_evidence'),
                     error=str(error))
    stage['child_closure_ok'] = False
    try:
        gate.closure()
        gate.verify()
        stage['child_closure_ok'] = True
    except Exception as error:
        stage.update(status='execution_failed', closure_error=str(error))
    # Sparse PPM scratch is never hashed; preserve metadata and remove it only
    # after this gate's cgroup is independently confirmed free of children.
    residuals = []
    for path in gate.result.rglob('ppm.temp'):
        stat = path.lstat()
        row = dict(path=str(path.relative_to(ROOT)), logical_bytes=stat.st_size,
                   allocated_bytes=stat.st_blocks * 512, removed=False)
        if stage['child_closure_ok'] and path.is_file() and not path.is_symlink():
            path.unlink()
            row['removed'] = True
        residuals.append(row)
    if residuals and stage['status'] == 'passed':
        stage.update(status='execution_failed', error='native transient survived successful replay')
    cleanup = dict(child_closure_ok=stage['child_closure_ok'], residuals=residuals,
                   cleanup_complete=stage['child_closure_ok'] and all(row['removed'] for row in residuals))
    gate.write('transient-cleanup.json', cleanup)
    stage['commands'] = gate.commands
    stage['transient_cleanup'] = gate.artifact(gate.result / 'transient-cleanup.json')
    try:
        artifacts = [gate.artifact(path) for path in sorted(gate.result.rglob('*'))
                     if path.is_file() and not path.is_symlink() and path.name != 'ppm.temp']
        gate.write('artifacts.json', artifacts)
        stage['artifacts'] = gate.artifact(gate.result / 'artifacts.json')
    except Exception as error:
        stage.update(status='execution_failed', index_error=str(error))
    gate.write('stage-decision.json', stage)
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
