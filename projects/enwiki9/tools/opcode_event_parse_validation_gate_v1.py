#!/usr/bin/env python3
"""Validate the unchanged codec with a fresh parent comparison on reserved bytes."""
import argparse
import inspect
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import opcode_event_parse_gate_v1 as engine

phase, require = engine.phase, engine.require
CID = 'opcode_event_parse_validation250k_q0_v1'
SELF = 'tools/opcode_event_parse_validation_gate_v1.py'
CAPS, PHASES = dict(engine.CAPS), dict(engine.PHASES)
SOURCES = engine.SOURCES | {SELF, 'tests/test_opcode_event_parse_validation_gate_v1.py'}
PACKAGE = {
    'p': (5423, '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'),
    'v': (1551, 'd9c4d28792936916715d37b1ace4572c0cdc2cc106498077418a3f32b66de48b'),
    'program.py': (768, '12ed0a23ee98326da0d0c174d726cdbc6543c3cf8921d326cb967d0a99f55c1b'),
}


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS
            and plan['phase_resources'] == PHASES, 'validation identity or limits differ')
    require(plan['input']['bytes'] == 250000 and plan['input']['sha256'] ==
            'ffb6c9e73f59dc3ee7109441aa05881d1980ff440f47db63120bf36822b765bf',
            'reserved validation population differs')
    require(SOURCES <= {r['path'] for r in plan['source_files']}, 'source closure missing')
    require(len(plan['package_files']) == 3 and
            {r['path']: (r['bytes'], r['sha256']) for r in plan['package_files']} ==
            {f'programs/{CID}/{name}': values for name, values in PACKAGE.items()},
            'unchanged measured bundle differs')
    require(plan['runtime_files'] and plan['evidence'], 'runtime or evidence missing')


def reuse(function, replacements, namespace):
    """Explicitly remove retained-opening checks; preserve every other gate check.

    No reserved parent archive exists before this run. P generates it in the
    same ten-phase comparison. The measured development module stays untouched.
    Exact replacement sites fail closed when the source being reused changes.
    """
    source = inspect.getsource(function)
    for old, new in replacements:
        require(source.count(old) == 1, 'shared gate source differs')
        source = source.replace(old, new)
    private = dict(namespace)
    exec(compile(source, '<reserved-event-pricing-gate>', 'exec'), private)
    return private[function.__name__]


authenticate = reuse(engine.authority.authenticate, [
    ("for key in ('input','parent_archive','parent_audit'):", "for key in ('input',):")],
    dict(vars(engine.authority), CID=CID, CAPS=CAPS, validate_plan=validate_plan))
run_comparison = reuse(engine.run_comparison, [
    ("    parent_archive = (ROOT / plan['parent_archive']['path']).read_bytes()\n", ''),
    ("    parent_audit = phase.read_json(ROOT / plan['parent_audit']['path'])\n", ''),
    ("        if arm == 'P':\n"
     "            compare(parent_archive, arc.read_bytes(), directory, 'retained-parent-archive')\n"
     "            compare(parent_audit, enc['parent'], directory, 'retained-parent-state')\n", '')],
    vars(engine))


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
    stage = dict(schema='gamma.enwiki9.opcode-event-parse-validation-gate.v1', candidate_id=CID,
                 experiment=reference, input=plan['input'], correctness_pass=False, status='running',
                 selection_stage='validation', package_files=plan['package_files'],
                 local_source_bytes=7742, source_delta_bytes=1996,
                 complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                 note='Unchanged codec on reserved bytes; parent generated within this comparison. '
                      'No tuning or automatic larger gate. Package remains separate.')
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
