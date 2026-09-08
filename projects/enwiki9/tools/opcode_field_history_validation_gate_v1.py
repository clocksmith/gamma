#!/usr/bin/env python3
"""Validate the unchanged field-history codec using the measured comparison engine."""
import argparse
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import opcode_field_history_gate_v1 as engine

phase, require = engine.phase, engine.require
CID = 'opcode_field_history_validation250k_q0_v1'
SELF = 'tools/opcode_field_history_validation_gate_v1.py'
CAPS, PHASES = dict(engine.CAPS), dict(engine.PHASES)
SOURCES = engine.SOURCES | {SELF, 'tests/test_opcode_field_history_validation_gate_v1.py'}
PACKAGE = {
    'p': (6075, '2d29f154a9df186caa7b547fa304820b6ceb6d675aef59005d7a1319febf3c64'),
    'program.py': (531, 'b96d641dc5a84dc9130932cca52d62b7fcefa54c2a0fce39027cb95bc1eee2ae'),
}


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS
            and plan['phase_resources'] == PHASES, 'validation identity or limits differ')
    require(plan['input']['bytes'] == 250000 and plan['input']['sha256'] ==
            '4c6b839c77999f9da19c0f856c40cceb1262aefb536ecc7e7f54e37f694c9b8b',
            'reserved validation population differs')
    require(SOURCES <= {r['path'] for r in plan['source_files']}, 'source closure missing')
    expected = {f'programs/{CID}/{name}': values for name, values in PACKAGE.items()}
    require(len(plan['package_files']) == 2 and
            {r['path']: (r['bytes'], r['sha256']) for r in plan['package_files']} == expected,
            'unchanged measured bundle differs')
    require(plan['runtime_files'] and plan['evidence'], 'runtime or evidence missing')


authenticate = types.FunctionType(engine.authenticate.__code__,
    dict(engine.authenticate.__globals__, CID=CID, CAPS=CAPS, validate_plan=validate_plan),
    'authenticate', engine.authenticate.__defaults__)
run_comparison = engine.run_comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    reference, plan, snapshot = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False)))
        return 0
    directory = ROOT / 'results' / CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-field-history-validation-gate.v1', candidate_id=CID,
                 experiment=reference, input=plan['input'], correctness_pass=False, status='running',
                 selection_stage='validation', package_files=plan['package_files'],
                 local_source_bytes=6606, source_delta_bytes=860,
                 complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                 note='Unchanged candidate on reserved validation. Original compact comparator costs '
                      'remain separate from lineage-parent costs. No tuning or automatic confirmation.')
    try:
        stage.update(run_comparison(directory, plan, snapshot, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate()
        stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed', failure_class='budget-exhausted' if isinstance(error, (engine.BudgetStop, MemoryError))
                     else 'infrastructure-failure' if isinstance(error, OSError) else 'implementation-failure',
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory / 'artifacts.json', dict(complete=stage['status'] == 'passed',
                     files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory / 'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
