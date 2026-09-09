#!/usr/bin/env python3
"""One frozen P/K/D/S development comparison for previous-word literal context."""
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
from tools.opcode_previous_word_observe_v1 import compare_audits

phase, binding, require = authority.phase, authority.binding, authority.require
compare, require_phase, BudgetStop = authority.compare, authority.require_phase, authority.BudgetStop
CID = 'opcode_previous_word250k_q0_v1'
SELF = 'tools/opcode_previous_word_gate_v1.py'
CLI = 'tools/opcode_previous_word_corpus_v1.py'
INPUTS = 'operations/provenance/opcode_previous_word250k_v1_inputs.json'
CAPS = dict(cpus=[2], memory_bytes=4294967296, scratch_bytes=1073741824,
            swap_bytes=0, wall_seconds=3120)
PHASES = dict(phase_cpu_seconds=180, phase_wall_seconds=240, phase_address_bytes=2147483648)
SOURCES = {SELF, CLI, 'tools/opcode_previous_word_build_v1.py',
           'lib/opcode_previous_word_v1.py', 'tools/opcode_previous_word_observe_v1.py',
           'tools/opcode_wiki_slot_gate_v1.py', 'tools/opcode_field_compact_observe_v1.py',
           'tools/opcode_field_repair_cli_v1.py', 'tools/opcode_field_compact_gate_v1.py',
           'tools/opcode_field_repair_gate_v2.py', 'tools/dualstream_grammar_gate_v1.py',
           'tools/dualstream_grammar_v1.py', 'tools/research_contracts.py',
           'tests/test_opcode_previous_word_gate_v1.py'}
PACKAGE = {'p': (5423, '7d331ba82c635af8afe6517bf5f4471b41dcf7854c6ec01cb5564078d9bb56a8'),
           'v': (832, '2415dc99d1338ab9d50f189070144fdf0d54c751e091e2b7a307eaf2e682481b'),
           'program.py': (768, '2fea664bc823dd817d0ad66bc310d05e8d0c903e65f697ce66079e6a9dfd6297')}
PUBLISHED = {'lib/opcode_previous_word_v1.py': 'b25ea617a34707d4928a9a9605ad4710dbccb63b2c5d4da80a57eea6ef1f26c5',
             'tools/opcode_previous_word_build_v1.py': '5be410cc3102c69d42f14e146606abc1880efee4690b46e0c0aee8485abff421',
             'tools/opcode_previous_word_observe_v1.py': '33b69c71525fc49fa968c59652744eac9795d9950442ae35e2bdda000a670b0c'}


class EvidenceFailure(ValueError):
    pass


def validate_plan(plan):
    require(plan['candidate_id'] == CID and plan['resources'] == CAPS
            and plan['phase_resources'] == PHASES, 'plan identity or limits differ')
    require(plan['input']['bytes'] == 250000 and plan['input']['sha256'] ==
            '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3', 'development population differs')
    require(plan['parent_archive']['bytes'] == 67658 and plan['parent_archive']['sha256'] ==
            'bda617eab7628f7cec6724ca3d82bf505efee9c2be4813dd404dcfa715140e6f', 'retained parent archive differs')
    require(plan['parent_audit']['bytes'] == 24889 and plan['parent_audit']['sha256'] ==
            '7aa2091cc61cf1bc838062df300aff0719d23eec0cfc734508f56d5633356315', 'retained parent audit differs')
    for key in ('source_files', 'package_files', 'runtime_files', 'evidence'):
        rows = plan[key]
        require(rows and len({r['path'] for r in rows}) == len(rows), 'missing or duplicate '+key)
    sources = {r['path']: r['sha256'] for r in plan['source_files']}
    require(SOURCES <= sources.keys() and all(sources.get(k) == v for k, v in PUBLISHED.items()),
            'published source closure differs')
    require({r['path']: (r['bytes'], r['sha256']) for r in plan['package_files']} ==
            {f'programs/{CID}/{k}': v for k, v in PACKAGE.items()}, 'package identity differs')
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve()
                for r in plan['runtime_files']), 'interpreter not bound')


def check_file(row, absolute=False, **kwargs):
    # The existing checker rejects empty files; allow only exact empty runtime refs.
    if not absolute or not isinstance(row, dict) or row.get('bytes') != 0:
        return binding.check_file(row, absolute=absolute, **kwargs)
    require(set(row) == {'path', 'bytes', 'sha256'} and type(row['bytes']) is int
            and isinstance(row['path'], str) and binding.hash_text(row['sha256']), 'invalid empty runtime reference')
    path = Path(row['path'])
    require(path.is_absolute() and '..' not in path.parts and str(path) == row['path']
            and path.is_file(), 'missing or unsafe empty runtime file')
    require(path.stat().st_size == 0 and phase.sha(path) == row['sha256'], 'changed empty runtime file')
    return path


_binding = types.SimpleNamespace(**dict(vars(binding), check_file=check_file))
_authenticate = types.FunctionType(authority.authenticate.__code__,
    dict(vars(authority), CID=CID, CAPS=CAPS, validate_plan=validate_plan, binding=_binding),
    '_authenticate', authority.authenticate.__defaults__)


def verify_contract_bindings(contract, plan, snapshot):
    inputs = {r['path']: r for r in contract['inputs']}
    require(len(inputs) == len(contract['inputs']), 'duplicate frozen inputs')
    for name, row in inputs.items():
        relative = Path(name); path = ROOT / relative
        require(not relative.is_absolute() and '..' not in relative.parts and str(relative) == name
                and path.resolve() == path and path.is_file(), 'unsafe frozen input')
        require(phase.sha(path) == row['sha256'].removeprefix('sha256:'), 'changed frozen input')
        if 'bytes' in row:
            require(type(row['bytes']) is int and path.stat().st_size == row['bytes'], 'frozen input size differs')
    require(INPUTS in inputs and phase.sha(snapshot / 'gate-plan.json') ==
            inputs[INPUTS]['sha256'].removeprefix('sha256:') and
            (snapshot / 'gate-plan.json').read_bytes() == (ROOT / INPUTS).read_bytes(),
            'gate-plan is not contract-bound')
    rows = [plan[k] for k in ('input', 'parent_archive', 'parent_audit')]
    rows += plan['source_files'] + plan['evidence']
    for row in rows:
        require(row['path'] in inputs and inputs[row['path']]['sha256'].removeprefix('sha256:') ==
                row['sha256'], 'unfrozen plan reference: '+row['path'])


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


def read_audit(path):
    try:
        result = phase.read_json(path)
        compare_audits(result, result)
        require(isinstance(result['parent'], dict), 'missing parent audit')
        require(sum(result['updates_by_mode']) == result['parent']['predictor_bits'] ==
                8 * result['parent']['modeled_bytes'], 'incomplete all-byte updates')
        return result
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise EvidenceFailure('mandatory audit unavailable: '+str(error)) from error


def compare_complete(expected, actual, directory, label):
    try:
        compare_audits(expected, actual)
    except ValueError:
        compare(expected, actual, directory, label)
        raise EvidenceFailure('mandatory word observation missing')


def run_comparison(directory, plan, snapshot, marker, limits=PHASES):
    directory, snapshot = directory.resolve(), snapshot.resolve()
    raw = ROOT / plan['input']['path']; expected = raw.read_bytes()
    parent_archive = (ROOT / plan['parent_archive']['path']).read_bytes()
    retained = phase.read_json(ROOT / plan['parent_audit']['path'])
    parent_audit = retained['parent'] if 'parent' in retained else retained
    rows, commands = {}, []

    def run(label, operation, src, dst, arm, audit=None):
        command = [sys.executable, str(ROOT / CLI), operation, str(src), str(dst),
                   '--candidate-root', str(snapshot), '--arm', arm]
        if audit is not None: command += ['--audit', str(audit)]
        record = phase.run_phase(directory, label, command, limits, marker)
        commands.append(record)
        require_phase(record, (directory / (label+'.stderr')).read_text(errors='replace'))
        try: record['codec_resources'] = phase.read_json(directory / (label+'.stdout'))
        except (OSError, ValueError) as error:
            record.update(codec_resources=None, missing_diagnostics=[str(error)])

    for arm in 'PKDS':
        arc, restored, repeat = [directory / (arm+s) for s in ('.arc', '.raw', '.repeat.arc')]
        audits = {k: directory / f'{arm}-{k}.audit.json' for k in ('encode', 'decode', 'repeat')}
        run(arm+'-encode', 'encode', raw, arc, arm, audits['encode'])
        run(arm+'-decode', 'decode', arc, restored, arm, audits['decode'])
        compare(expected, restored.read_bytes(), directory, arm+'-inverse')
        run(arm+'-repeat', 'encode', restored, repeat, arm, audits['repeat'])
        compare(arc.read_bytes(), repeat.read_bytes(), directory, arm+'-repeat')
        enc = read_audit(audits['encode'])
        for label in ('decode', 'repeat'):
            compare_complete(enc, read_audit(audits[label]), directory, arm+'-'+label+'-state')
        if arm == 'P':
            compare(parent_archive, arc.read_bytes(), directory, 'retained-parent-archive')
            compare(parent_audit, enc['parent'], directory, 'retained-parent-state')
        else:
            for field in ('parse_sha256', 'parse_events', 'updates_by_mode'):
                compare(rows['P']['audit'][field], enc[field], directory, arm+'-'+field)
        if arm == 'K':
            compare((directory / 'P.arc').read_bytes(), arc.read_bytes(), directory, 'PK-archive')
            compare(rows['P']['audit']['parent'], enc['parent'], directory, 'PK-projection')
        if arm in 'DS':
            for field in ('word_history_sha256', 'word_checkpoints', 'completed_words_hex', 'modeled_field'):
                compare(rows['K']['audit'][field], enc[field], directory, arm+'-'+field)
        rows[arm] = dict(archive_bytes=arc.stat().st_size, audit=enc,
            artifacts=dict(archive=phase.artifact(arc), restored=phase.artifact(restored), repeat=phase.artifact(repeat)),
            audits={k: phase.artifact(p) for k, p in audits.items()}, commands=commands[-3:])
    plain = directory / 'D.plain.arc'
    run('D-plain', 'encode', raw, plain, 'D')
    compare((directory / 'D.arc').read_bytes(), plain.read_bytes(), directory, 'D-observation')
    gain = rows['P']['archive_bytes'] - rows['D']['archive_bytes']
    delayed_gain = rows['S']['archive_bytes'] - rows['D']['archive_bytes']
    return dict(arms=rows, commands=commands, archive_saving_bytes=gain,
                delayed_control_saving_bytes=delayed_gain, correctness_pass=True,
                controls_equivalent=True, prediction_gate_pass=gain > 0 and delayed_gain > 0,
                interpretation='prediction-gain' if gain > 0 and delayed_gain > 0 else 'prediction-gate-not-passed',
                same_arm_decoder_all_arms=True, all_arm_parse_and_updates_equal=True,
                KDS_history_equal=True)


def failure_class(error):
    if isinstance(error, (BudgetStop, MemoryError)): return 'budget-exhausted'
    if isinstance(error, EvidenceFailure): return 'incomplete-evidence'
    if isinstance(error, OSError): return 'infrastructure-failure'
    return 'implementation-failure'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(); reference, plan, snapshot = authenticate(args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', codec_executed=False))); return 0
    directory = ROOT / 'results' / CID
    require(directory.is_dir() and not any(directory.iterdir()), 'result directory must be empty')
    stage = dict(schema='gamma.enwiki9.opcode-previous-word-gate.v1', candidate_id=CID,
                 experiment=reference, input=plan['input'], correctness_pass=False, status='running',
                 package_files=plan['package_files'], local_source_bytes=7023, source_delta_bytes=1277,
                 complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                 note='Development only; local source versus parent5746 bytes. No complete package credit or automatic confirmation.')
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
