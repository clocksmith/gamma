#!/usr/bin/env python3
"""One fixed-code 1MB confirmation, including the measured source-ZIP increment."""
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import opcode_event_parse_validation_gate_v1 as base

phase, require = base.phase, base.require
CID = 'opcode_event_parse_confirmation1m_q0_v1'
SELF = 'tools/opcode_event_parse_confirmation_gate_v1.py'
CLI = 'tools/opcode_event_parse_corpus1m_v1.py'
CAPS = dict(base.CAPS, wall_seconds=6000)
PHASES = dict(phase_cpu_seconds=600, phase_wall_seconds=720, phase_address_bytes=2147483648)
SOURCES = base.SOURCES | {SELF, CLI, 'tests/test_opcode_event_parse_confirmation_gate_v1.py'}
PACKAGE = dict(base.PACKAGE)
SOURCE_ZIP_INCREMENT = 1895


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS
            and plan['phase_resources'] == PHASES, 'confirmation identity or limits differ')
    require(plan['input']['bytes'] == 1000000 and plan['input']['sha256'] ==
            '851329174ac0763701a0364fed26b58ba7c6847a3c0b8a737d2c5b88a24785d4',
            'reserved confirmation population differs')
    require(SOURCES <= {r['path'] for r in plan['source_files']}, 'source closure missing')
    require(len(plan['package_files']) == 3 and
            {r['path']: (r['bytes'], r['sha256']) for r in plan['package_files']} ==
            {f'programs/{CID}/{n}': v for n,v in PACKAGE.items()}, 'unchanged measured bundle differs')
    require(plan['runtime_files'] and plan['evidence'], 'runtime or evidence missing')
    require(any(r['path'] == 'results/opcode_event_parse_source_zip_v1/attempt01/cost.json'
                for r in plan['evidence']), 'measured ZIP cost missing')


authenticate = types.FunctionType(base.authenticate.__code__,
    dict(base.authenticate.__globals__, CID=CID, CAPS=CAPS, validate_plan=validate_plan),
    'authenticate', base.authenticate.__defaults__)
comparison = types.FunctionType(base.run_comparison.__code__,
    dict(base.run_comparison.__globals__, CLI=CLI), 'comparison', (PHASES,))


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    result = comparison(directory, plan, snapshot, marker, limits)
    delta = result['archive_saving_bytes'] - SOURCE_ZIP_INCREMENT
    result.update(added_source_zip_bytes=SOURCE_ZIP_INCREMENT,
                  archive_minus_one_source_zip_delta_bytes=delta,
                  source_component_gate_pass=delta > 0,
                  accounting_scope='One fixed source ZIP increment; complete package and official multiplicities unresolved')
    return result


main = base.reuse(base.main, [
    ('gamma.enwiki9.opcode-event-parse-validation-gate.v1', 'gamma.enwiki9.opcode-event-parse-confirmation-gate.v1'),
    ("selection_stage='validation'", "selection_stage='confirmation'")],
    dict(vars(base), CID=CID, CAPS=CAPS, PHASES=PHASES, authenticate=authenticate,
         run_comparison=run_comparison))


if __name__ == '__main__':
    raise SystemExit(main())
