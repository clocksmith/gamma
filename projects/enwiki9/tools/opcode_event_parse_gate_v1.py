#!/usr/bin/env python3
"""Matched P/K/D event-pricing comparison with the existing guard machinery."""
import argparse
import json
import os
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import opcode_wiki_slot_gate_v1 as authority

phase, require = authority.phase, authority.require
compare, require_phase, BudgetStop = authority.compare, authority.require_phase, authority.BudgetStop
CID = 'opcode_event_parse250k_q0_v1'
SELF = 'tools/opcode_event_parse_gate_v1.py'
CLI = 'tools/opcode_event_parse_corpus_v1.py'
CAPS, PHASES = dict(authority.CAPS), dict(authority.PHASES)
SOURCES = {SELF, CLI, 'tools/opcode_event_parse_build_v1.py',
           'lib/opcode_event_parse_v1.py', 'lib/opcode_literal_event_cost_v1.py',
           'tools/opcode_wiki_slot_gate_v1.py', 'tools/opcode_field_compact_observe_v1.py',
           'tools/opcode_field_repair_cli_v1.py', 'tools/opcode_field_compact_gate_v1.py',
           'tools/opcode_field_repair_gate_v2.py', 'tools/dualstream_grammar_gate_v1.py',
           'tools/dualstream_grammar_v1.py', 'tools/research_contracts.py',
           'tests/test_opcode_event_parse_gate_v1.py'}


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS
            and plan['phase_resources'] == PHASES, 'plan identity or limits differ')
    require(plan['input']['bytes'] == 250000 and plan['input']['sha256'] ==
            '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3',
            'development population differs')
    require(SOURCES <= {r['path'] for r in plan['source_files']}, 'source closure missing')
    require(len(plan['package_files']) == 3 and {r['path'] for r in plan['package_files']} ==
            {f'programs/{CID}/{name}' for name in ('p', 'v', 'program.py')}, 'package owner differs')
    require(sum(r['bytes'] for r in plan['package_files']) <= 20000, 'source allowance exceeded')
    require(plan['runtime_files'] and plan['evidence'], 'runtime or evidence missing')


authenticate = types.FunctionType(authority.authenticate.__code__,
    dict(vars(authority), CID=CID, CAPS=CAPS, validate_plan=validate_plan),
    'authenticate', authority.authenticate.__defaults__)


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    directory, snapshot = directory.resolve(), snapshot.resolve()
    raw = ROOT / plan['input']['path']
    expected = raw.read_bytes()
    parent_archive = (ROOT / plan['parent_archive']['path']).read_bytes()
    parent_audit = phase.read_json(ROOT / plan['parent_audit']['path'])
    rows, commands = {}, []

    def run(label, operation, src, dst, arm, audit=None):
        command = [sys.executable, str(ROOT / CLI), operation, str(src), str(dst),
                   '--candidate-root', str(snapshot), '--arm', arm]
        if audit is not None:
            command += ['--audit', str(audit)]
        record = phase.run_phase(directory, label, command, limits, marker)
        commands.append(record)
        require_phase(record, (directory / (label + '.stderr')).read_text(errors='replace'))
        try:
            record['codec_resources'] = phase.read_json(directory / (label + '.stdout'))
        except (OSError, ValueError) as error:
            record.update(codec_resources=None, missing_diagnostics=[str(error)])

    for arm in 'PKD':
        arc, restored, repeat = [directory / (arm + suffix) for suffix in ('.arc', '.raw', '.repeat.arc')]
        audits = {key: directory / f'{arm}-{key}.audit.json' for key in ('encode', 'decode', 'repeat')}
        run(arm+'-encode', 'encode', raw, arc, arm, audits['encode'])
        run(arm+'-decode', 'decode', arc, restored, arm, audits['decode'])
        compare(expected, restored.read_bytes(), directory, arm+'-inverse')
        run(arm+'-repeat', 'encode', restored, repeat, arm, audits['repeat'])
        compare(arc.read_bytes(), repeat.read_bytes(), directory, arm+'-repeat')
        enc = phase.read_json(audits['encode'])
        for label in ('decode', 'repeat'):
            compare(enc, phase.read_json(audits[label]), directory, arm+'-'+label+'-state')
        if arm == 'P':
            compare(parent_archive, arc.read_bytes(), directory, 'retained-parent-archive')
            compare(parent_audit, enc['parent'], directory, 'retained-parent-state')
        if arm == 'K':
            compare((directory / 'P.arc').read_bytes(), arc.read_bytes(), directory, 'PK-archive')
            compare(rows['P']['audit'], enc, directory, 'PK-projection')
        rows[arm] = dict(archive_bytes=arc.stat().st_size, audit=enc,
            artifacts=dict(archive=phase.artifact(arc), restored=phase.artifact(restored), repeat=phase.artifact(repeat)),
            audits={k: phase.artifact(p) for k, p in audits.items()}, commands=commands[-3:])
    plain = directory / 'D.plain.arc'
    run('D-plain', 'encode', raw, plain, 'D')
    compare((directory / 'D.arc').read_bytes(), plain.read_bytes(), directory, 'D-observation')
    gain = rows['P']['archive_bytes'] - rows['D']['archive_bytes']
    return dict(arms=rows, commands=commands, archive_saving_bytes=gain,
                correctness_pass=True, controls_equivalent=True, prediction_gate_pass=gain > 0,
                interpretation='archive-gain' if gain > 0 else 'no-archive-gain',
                original_decoder_all_arms=True)


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
    size = sum(r['bytes'] for r in plan['package_files'])
    stage = dict(schema='gamma.enwiki9.opcode-event-parse-gate.v1', candidate_id=CID,
                 experiment=reference, input=plan['input'], correctness_pass=False, status='running',
                 package_files=plan['package_files'], local_source_bytes=size, source_delta_bytes=size-5746,
                 complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                 note='Development only; archive and source costs separate. No automatic confirmation.')
    try:
        stage.update(run_comparison(directory, plan, snapshot, Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])))
        authenticate()
        stage.update(status='passed', frozen_inputs_reverified=True)
    except Exception as error:
        stage.update(status='failed', failure_class='budget-exhausted' if isinstance(error, (BudgetStop, MemoryError))
                     else 'infrastructure-failure' if isinstance(error, OSError) else 'implementation-failure',
                     error=type(error).__name__+': '+str(error))
    phase.write_json(directory / 'artifacts.json', dict(complete=stage['status'] == 'passed',
                     files=[phase.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]))
    phase.write_json(directory / 'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], correctness_pass=stage['correctness_pass'])))
    return 0 if stage['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
