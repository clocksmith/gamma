#!/usr/bin/env python3
"""Frozen cold-population word transfer, with independent compact release replay."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
_path = ROOT / 'tools/opcode_previous_word_release_gate_v1.py'
_source = _path.read_bytes()
if hashlib.sha256(_source).hexdigest() != '8b6bbbab10f3fa45b6acaa7b4c0b466bfcc5f98b0185e497a8a827c3c5b3fbbe':
    raise ValueError('immutable release gate differs')
release = types.ModuleType(__name__ + '_release')
release.__file__ = str(_path)
exec(compile(_source, str(_path), 'exec'), vars(release))
base = release.base
phase, require, EvidenceFailure = base.phase, base.require, base.EvidenceFailure
CID = 'opcode_previous_word_confirmation1m_q0_v4'
SELF = 'tools/opcode_previous_word_bounded_gate_v3.py'
CLI = 'tools/opcode_previous_word_bounded_corpus_v1.py'
INPUTS = 'operations/provenance/opcode_previous_word_confirmation1m_v4_inputs.json'
CAPS = dict(cpus=[2], memory_bytes=4294967296, scratch_bytes=1073741824,
            swap_bytes=0, wall_seconds=4200)
PHASES = dict(base.PHASES, phase_cpu_seconds=720, phase_wall_seconds=960)
SOURCES = release.SOURCES | {SELF, CLI, 'tools/opcode_previous_word_release_gate_v1.py',
    'tests/test_opcode_previous_word_confirmation_policy_v1.py'}
PACKAGE = {
    'p': (5562, 'b58e245d32513d7446d338f6a1a36956d2d77b25777621408da1658e9b6b394f'),
    'program.py': (399, 'a3655332888d9f78d87fe0417a10382b268ca9f3ad4cc3887498c605f40cce22'),
    **{'release/'+key: value for key, value in release.PACKAGE.items()}}
EXPECTED = {
    'input': (1000000, '851329174ac0763701a0364fed26b58ba7c6847a3c0b8a737d2c5b88a24785d4'),
    'parent_archive': (259468, 'fe15e711394d7832f7deed1c597c0302b2078d612d62a5e3f2ef31c32aca1a0f'),
    'parent_audit': (94857, '76ca2e2059a564fdeaf2624537601c4df703bef2929d749fdc1c085d04dcc9f4')}


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS
            and plan['phase_resources'] == PHASES, 'plan identity or limits differ')
    for key, expected in EXPECTED.items():
        require((plan[key]['bytes'], plan[key]['sha256']) == expected, 'retained input differs: '+key)
    for key in ('source_files', 'runtime_files', 'evidence', 'package_files', 'materialization'):
        rows = plan[key]
        require(rows and len({r['path'] for r in rows}) == len(rows), 'missing or duplicate '+key)
    require(SOURCES <= {r['path'] for r in plan['source_files']}, 'source closure missing')
    require({r['path']: (r['bytes'], r['sha256']) for r in plan['package_files']} ==
            {f'programs/{CID}/{name}': value for name, value in PACKAGE.items()}, 'package differs')
    require(len(plan['materialization']) == 4 and
            sorted((r['bytes'], r['sha256']) for r in plan['materialization']) == sorted(PACKAGE.values()),
            'materialization differs')
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve()
                for r in plan['runtime_files']), 'interpreter not bound')


_bound = types.FunctionType(base.verify_contract_bindings.__code__,
    dict(vars(base), INPUTS=INPUTS), 'bound_plan')
_authenticate = types.FunctionType(base.authority.authenticate.__code__,
    dict(vars(base.authority), CID=CID, CAPS=CAPS, validate_plan=validate_plan,
         binding=base._binding), 'authenticate', base.authority.authenticate.__defaults__)
_controlled = types.FunctionType(base.run_comparison.__code__,
    dict(vars(base), CLI=CLI), 'controlled', base.run_comparison.__defaults__)


def verify_contract_bindings(contract, plan, snapshot):
    _bound(contract, plan, snapshot)
    inputs = {r['path']: r['sha256'].removeprefix('sha256:') for r in contract['inputs']}
    for row in plan['materialization']:
        base.check_file(row)
        require(inputs.get(row['path']) == row['sha256'], 'unfrozen materialization')


def authenticate(validate_only=False):
    try:
        contract = phase.read_json(ROOT / 'operations/adaptive/experiments' / (CID+'.json'))
        snapshot = (ROOT / 'programs' / CID if validate_only else
                    Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT']))
        plan = phase.read_json(ROOT / INPUTS)
        verify_contract_bindings(contract, plan, snapshot)
        return _authenticate(validate_only)
    except (ValueError, KeyError, OSError, TypeError) as error:
        raise EvidenceFailure(str(error)) from error


_released = types.FunctionType(release.run_comparison.__code__,
    dict(vars(release), CLI='tools/opcode_previous_word_bounded_release_corpus_v1.py'),
    'released', release.run_comparison.__defaults__)


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    directory, snapshot = directory.resolve(), snapshot.resolve()
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    controlled_dir, released_dir = directory / 'controls', directory / 'release'
    controlled_dir.mkdir(); released_dir.mkdir()
    controlled = _controlled(controlled_dir, plan, snapshot, marker, limits)
    phase.write_json(directory / 'completed-controls.json', controlled)
    treatment = controlled['arms']['D']
    # Fresh D is a phase dependency, not fictitious evidence available at freeze.
    released_plan = dict(plan, parent_archive=treatment['artifacts']['archive'],
        parent_audit=treatment['audits']['encode'], original_parent_archive=plan['parent_archive'])
    realized = _released(released_dir, released_plan, snapshot / 'release', marker, limits)
    require(realized['archive_saving_bytes'] == controlled['archive_saving_bytes'], 'release cost differs')
    return dict(controls=controlled, release=realized,
        commands=controlled['commands'] + realized['commands'],
        archive_saving_bytes=controlled['archive_saving_bytes'],
        delayed_control_saving_bytes=controlled['delayed_control_saving_bytes'],
        correctness_pass=True, controls_equivalent=True,
        prediction_gate_pass=controlled['prediction_gate_pass'],
        archive_minus_local_source_delta_bytes=realized['archive_minus_local_source_delta_bytes'],
        archive_minus_two_local_source_copies_bytes=realized['archive_minus_two_local_source_copies_bytes'],
        local_subtotal_gate_pass=realized['local_subtotal_gate_pass'],
        transfer_gate_pass=controlled['prediction_gate_pass'] and realized['local_subtotal_gate_pass'])


def decision(g_p, g_s, complete, correctness, repeatability, resource):
    if correctness is False:
        return 'Correctness or control failure; the affected compression inference is invalid.'
    if not complete or correctness is not True or resource is not True or repeatability is not True or g_p is None or g_s is None:
        return 'Resource failure or incomplete execution; no complete confirmation verdict.'
    if g_p == 0:
        return 'No archive improvement.'
    if g_p < 0:
        return 'Archive regression.'
    if g_s <= 0:
        return 'Parent improvement observed, but advantage over the delayed control is unconfirmed.'
    return 'Predictive confirmation on this cold 1MB sample.'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    reference, plan, snapshot = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False))); return 0
    directory = ROOT / 'results' / CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-previous-word-confirmation.v1', candidate_id=CID,
        experiment=reference, input=plan['input'], population='[819000000, 820000000)',
        status='running', correctness_pass=None, repeatability_pass=None, resource_gate_pass=None,
        package_files=plan['package_files'], source_delta_bytes=110,
        g_P=None, g_S=None, n_1=None, n_2=None,
        sensitivity_label='historical source-cost sensitivities',
        complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
        decision_policy=plan['decision_policy'],
        note='Cold initialization; prior exposure to other mechanisms retained. No tuning or larger launch.')
    try:
        stage.update(run_comparison(directory, plan, snapshot, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate()
        stage.update(status='passed', frozen_inputs_reverified=True, repeatability_pass=True,
            g_P=stage['archive_saving_bytes'], g_S=stage['delayed_control_saving_bytes'])
    except Exception as error:
        kind = base.failure_class(error)
        stage.update(status='failed', failure_class=kind, error=type(error).__name__+': '+str(error))
        if kind == 'budget-exhausted': stage['resource_gate_pass'] = False
        elif kind == 'implementation-failure': stage['correctness_pass'] = False
        completed = directory / 'completed-controls.json'
        if completed.exists():
            controls = phase.read_json(completed)
            stage.update(completed_controls=phase.artifact(completed),
                g_P=controls['archive_saving_bytes'], g_S=controls['delayed_control_saving_bytes'],
                measurement_scope='Completed experimental controls; release parity incomplete.')
    if stage['g_P'] is not None:
        stage.update(n_1=stage['g_P']-110, n_2=stage['g_P']-220)
    stage['verdict'] = decision(stage['g_P'], stage['g_S'], stage['status']=='passed',
        stage['correctness_pass'], stage['repeatability_pass'], stage['resource_gate_pass'])
    stage['resource_note'] = 'Final aggregate guard must close before the terminal confirmation verdict.'
    phase.write_json(directory / 'artifacts.json', dict(complete=stage['status'] == 'passed',
        files=[phase.artifact(p) for p in sorted(directory.rglob('*')) if p.is_file()]))
    phase.write_json(directory / 'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
