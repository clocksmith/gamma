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
CID = 'opcode_previous_word_validation250k_q0_v1'
SELF = 'tools/opcode_previous_word_transfer_gate_v1.py'
CLI = 'tools/opcode_previous_word_compact_corpus_v1.py'
INPUTS = 'operations/provenance/opcode_previous_word_validation250k_v1_inputs.json'
CAPS = dict(cpus=[2], memory_bytes=4294967296, scratch_bytes=1073741824,
            swap_bytes=0, wall_seconds=4200)
PHASES = dict(base.PHASES)
SOURCES = release.SOURCES | {SELF, CLI, 'tools/opcode_previous_word_release_gate_v1.py',
    'tests/test_opcode_previous_word_transfer_gate_v1.py'}
PACKAGE = {
    'p': (5562, 'b58e245d32513d7446d338f6a1a36956d2d77b25777621408da1658e9b6b394f'),
    'program.py': (399, 'a3655332888d9f78d87fe0417a10382b268ca9f3ad4cc3887498c605f40cce22'),
    **{'release/'+key: value for key, value in release.PACKAGE.items()}}
EXPECTED = {
    'input': (250000, 'ffb6c9e73f59dc3ee7109441aa05881d1980ff440f47db63120bf36822b765bf'),
    'parent_archive': (68981, 'da66b4d059e30280e9de55c00f6c4755501e341388fc7d4e5f9d39e1f02e1eb6'),
    'parent_audit': (24886, 'd3d5b66fd1d45bfa10c7196ea48ad2d1cf215104f33c71327896d9c7c5082e83')}


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


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    directory, snapshot = directory.resolve(), snapshot.resolve()
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    controlled_dir, released_dir = directory / 'controls', directory / 'release'
    controlled_dir.mkdir(); released_dir.mkdir()
    controlled = _controlled(controlled_dir, plan, snapshot, marker, limits)
    treatment = controlled['arms']['D']
    # Fresh D is a phase dependency, not fictitious evidence available at freeze.
    released_plan = dict(plan, parent_archive=treatment['artifacts']['archive'],
        parent_audit=treatment['audits']['encode'], original_parent_archive=plan['parent_archive'])
    realized = release.run_comparison(released_dir, released_plan, snapshot / 'release', marker, limits)
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(); reference, plan, snapshot = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False))); return 0
    directory = ROOT / 'results' / CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-previous-word-transfer-gate.v1', candidate_id=CID,
        experiment=reference, input=plan['input'], status='running', correctness_pass=False,
        package_files=plan['package_files'], local_source_bytes=5856,
        control_source_bytes=5961, original_parent_local_source_bytes=5746, source_delta_bytes=110,
        complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
        note='Cold reserved population; previously exposed to other mechanisms. No word tuning or automatic larger launch.')
    try:
        stage.update(run_comparison(directory, plan, snapshot, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate(); stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, controls_equivalent=False,
                     prediction_gate_pass=False, local_subtotal_gate_pass=False, transfer_gate_pass=False,
                     failure_class=base.failure_class(error),
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory / 'artifacts.json', dict(complete=stage['status'] == 'passed',
        files=[phase.artifact(p) for p in sorted(directory.rglob('*')) if p.is_file()]))
    phase.write_json(directory / 'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
