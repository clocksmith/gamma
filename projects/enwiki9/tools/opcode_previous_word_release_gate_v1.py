#!/usr/bin/env python3
"""Four bounded release replays against the frozen previous-word treatment."""
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
_path = ROOT / 'tools/opcode_previous_word_gate_v1.py'
_source = _path.read_bytes()
if hashlib.sha256(_source).hexdigest() != 'b01a2bbcc56be7c1ce0f191b71915e65aff6691f800861215abd7185ee8806ca':
    raise ValueError('immutable previous-word gate differs')
base = types.ModuleType(__name__ + '_authenticated_parent')
base.__file__ = str(_path)
exec(compile(_source, str(_path), 'exec'), vars(base))
phase, require, compare = base.phase, base.require, base.compare
read_audit, compare_complete = base.read_audit, base.compare_complete
require_phase, failure_class = base.require_phase, base.failure_class
EvidenceFailure = base.EvidenceFailure
CID = 'opcode_previous_word_release250k_q0_v1'
SELF = 'tools/opcode_previous_word_release_gate_v1.py'
CLI = 'tools/opcode_previous_word_release_corpus_v1.py'
INPUTS = 'operations/provenance/opcode_previous_word_release250k_v1_inputs.json'
CAPS = dict(cpus=[2], memory_bytes=4294967296, scratch_bytes=1073741824,
            swap_bytes=0, wall_seconds=1080)
PHASES = dict(base.PHASES)
SOURCES = base.SOURCES | {SELF, CLI, 'tools/opcode_previous_word_gate_v1.py',
    'tools/opcode_previous_word_corpus_v1.py', 'tools/opcode_previous_word_compact_observe_v1.py',
    'tools/opcode_previous_word_release_build_v1.py', 'tests/test_opcode_previous_word_release_gate_v1.py'}
PACKAGE = {'p': (5533, 'ad81a7f09cd1c5baefdaabb4cc218f360268576346fe64ed1b81096df1a362e0'),
           'program.py': (323, '7361c8aa3695ec9d1556be02de66a1f0781414e78b44827511fb08bf8c8c05eb')}
EXPECTED = {
    'input': (250000, '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'),
    'parent_archive': (67511, '4bdfdde62868082fda22570acfe7a0d3b4ffcb1dd4aa6bf6db41dd3474b7f276'),
    'parent_audit': (31202, '7dcd3a62bdb6cbb01d6159e4f4382a3fd40156b10c3b11f01b77306ccefab333'),
    'original_parent_archive': (67658, 'bda617eab7628f7cec6724ca3d82bf505efee9c2be4813dd404dcfa715140e6f')}


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
            {f'programs/{CID}/{name}': value for name, value in PACKAGE.items()}, 'release package differs')
    require(len(plan['materialization']) == 2 and
            {Path(r['path']).name: (r['bytes'], r['sha256']) for r in plan['materialization']} == PACKAGE,
            'release materialization differs')
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve()
                for r in plan['runtime_files']), 'interpreter not bound')


_bound = types.FunctionType(base.verify_contract_bindings.__code__,
    dict(vars(base), INPUTS=INPUTS), 'bound_plan')
_authenticate = types.FunctionType(base.authority.authenticate.__code__,
    dict(vars(base.authority), CID=CID, CAPS=CAPS, validate_plan=validate_plan,
         binding=base._binding), 'authenticate', base.authority.authenticate.__defaults__)


def verify_contract_bindings(contract, plan, snapshot):
    _bound(contract, plan, snapshot)
    inputs = {r['path']: r['sha256'].removeprefix('sha256:') for r in contract['inputs']}
    for row in [plan['original_parent_archive'], *plan['materialization']]:
        base.check_file(row)
        require(inputs.get(row['path']) == row['sha256'], 'unfrozen release reference')


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
    raw = ROOT / plan['input']['path']
    expected = raw.read_bytes()
    retained = (ROOT / plan['parent_archive']['path']).read_bytes()
    retained_audit = read_audit(ROOT / plan['parent_audit']['path'])
    original = (ROOT / plan['original_parent_archive']['path']).read_bytes()
    commands, paths = [], {k: directory / ('D'+suffix) for k, suffix in
        (('archive', '.arc'), ('restored', '.raw'), ('repeat', '.repeat.arc'), ('plain', '.plain.arc'))}
    audits = {k: directory / ('D-'+k+'.audit.json') for k in ('encode', 'decode', 'repeat')}
    for mode, operation, source, output in (
            ('encode', 'encode', raw, paths['archive']),
            ('decode', 'decode', paths['archive'], paths['restored']),
            ('repeat', 'encode', paths['restored'], paths['repeat']),
            ('plain', 'encode', raw, paths['plain'])):
        label = 'D-'+mode
        command = [sys.executable, str(ROOT / CLI), operation, str(source), str(output),
                   '--candidate-root', str(snapshot)]
        if mode != 'plain': command += ['--audit', str(audits[mode])]
        record = phase.run_phase(directory, label, command, limits, marker)
        commands.append(record)
        require_phase(record, (directory / (label+'.stderr')).read_text(errors='replace'))
        try: record['codec_resources'] = phase.read_json(directory / (label+'.stdout'))
        except (OSError, ValueError) as error:
            record.update(codec_resources=None, missing_diagnostics=[str(error)])
        compare(expected if mode == 'decode' else retained, output.read_bytes(), directory, label+'-bytes')
        if mode != 'plain':
            compare_complete(retained_audit, read_audit(audits[mode]), directory, label+'-retained-state')
    archive_bytes = paths['archive'].stat().st_size
    gain = len(original) - archive_bytes
    return dict(commands=commands, archive_bytes=archive_bytes, original_parent_archive_bytes=len(original),
        retained_treatment_archive_bytes=len(retained), archive_saving_bytes=gain,
        source_delta_bytes=110, adapter_source_saving=1167,
        archive_minus_local_source_delta_bytes=gain-110,
        archive_minus_two_local_source_copies_bytes=gain-220,
        correctness_pass=True, retained_treatment_archive_and_state_equal=True,
        exact_inverse=True, deterministic_repeat=True, observed_unobserved_archive_equal=True,
        same_arm_decoder=True, prediction_changed=False,
        local_subtotal_gate_pass=gain > 110,
        artifacts={k: phase.artifact(v) for k, v in paths.items()},
        audits={k: phase.artifact(v) for k, v in audits.items()},
        interpretation='Exact treatment release realization. The local subtotal charges one source copy; '
            'the two-copy sensitivity is separate. No new predictive gain, complete package score, '
            'qualification or automatic larger-gate authority.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(); reference, plan, snapshot = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False))); return 0
    directory = ROOT / 'results' / CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-previous-word-release-gate.v1', candidate_id=CID,
        experiment=reference, input=plan['input'], status='running', correctness_pass=False,
        package_files=plan['package_files'], local_source_bytes=5856,
        original_parent_local_source_bytes=5746, old_treatment_local_source_bytes=7023,
        source_delta_bytes=110, adapter_source_saving=1167, complete_package_bytes=None,
        full_corpus_score_bytes=None, objective_credit_bytes=0,
        note='Release parity on reused development data; no confirmation or automatic larger launch.')
    try:
        stage.update(run_comparison(directory, plan, snapshot, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate(); stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, failure_class=failure_class(error),
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory / 'artifacts.json', dict(complete=stage['status'] == 'passed',
        files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory / 'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
