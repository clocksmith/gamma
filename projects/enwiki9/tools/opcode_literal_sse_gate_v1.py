#!/usr/bin/env python3
"""Existing guarded comparison plus exact non-calibration and parse controls."""
import argparse
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import opcode_event_parse_gate_v1 as base

CID = 'opcode_literal_sse250k_q0_v1'
SELF = 'tools/opcode_literal_sse_gate_v1.py'
CLI = 'tools/opcode_literal_sse_corpus_v1.py'
CAPS, PHASES = dict(base.CAPS), dict(base.PHASES)
phase, require, compare = base.phase, base.require, base.compare
SOURCES = (base.SOURCES - {'lib/opcode_event_parse_v1.py', 'lib/opcode_literal_event_cost_v1.py',
                          'tools/opcode_event_parse_build_v1.py', 'tools/opcode_event_parse_corpus_v1.py',
                          'tests/test_opcode_event_parse_gate_v1.py'}) | {
    SELF, CLI, 'tools/opcode_literal_sse_build_v1.py', 'lib/opcode_literal_sse_v1.py',
    'tests/test_opcode_literal_sse_gate_v1.py'}
validate_plan = types.FunctionType(base.validate_plan.__code__, dict(vars(base), CID=CID, SOURCES=SOURCES))
authenticate = types.FunctionType(base.authority.authenticate.__code__,
    dict(vars(base.authority), CID=CID, CAPS=CAPS, validate_plan=validate_plan),
    'authenticate', base.authority.authenticate.__defaults__)
_comparison = types.FunctionType(base.run_comparison.__code__, dict(vars(base), CLI=CLI),
                                'comparison', base.run_comparison.__defaults__)


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    result = _comparison(directory, plan, snapshot, marker, limits)
    audits = {a: r['audit'] for a, r in result['arms'].items()}
    for arm in ('K', 'D'):
        for key in ('non_sse', 'parse_sha256', 'parse_events', 'updates_by_mode'):
            compare(audits['P'][key], audits[arm][key], directory, arm+'-unchanged-'+key)
    result.update(original_decoder_all_arms=False, matching_arm_decoders=True,
                  non_sse_state_equal=True, parse_events_equal=True)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--validate-only', action='store_true'); args = p.parse_args()
    reference, plan, snapshot = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False))); return 0
    directory = ROOT / 'results' / CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    size = sum(r['bytes'] for r in plan['package_files'])
    stage = dict(schema='gamma.enwiki9.opcode-literal-sse-gate.v1', candidate_id=CID,
                 experiment=reference, input=plan['input'], correctness_pass=False, status='running',
                 package_files=plan['package_files'], local_source_bytes=size, source_delta_bytes=size-5746,
                 complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                 note='Development only. Matched arm decoder required. Archive and package costs separate.')
    try:
        stage.update(run_comparison(directory, plan, snapshot, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate(); stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed', failure_class='budget-exhausted' if isinstance(error, (base.BudgetStop, MemoryError))
                     else 'infrastructure-failure' if isinstance(error, OSError) else 'implementation-failure',
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory/'artifacts.json', dict(complete=stage['status']=='passed',
                     files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory/'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status']=='passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
