#!/usr/bin/env python3
"""Frozen forward/bookkeeping/reverse BZip2 comparisons using the existing driver."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF, CODEC = 'tools/raw_reverse_bz2_gate_v1.py', 'tools/raw_reverse_bz2_v1.py'
TESTS = 'tests/test_raw_reverse_bz2_gate_v1.py'
SHARED_DRIVER = 'tools/dualstream_grammar_gate_v1.py'
HARNESS_BASE = 'tools/dualstream_grammar_v1.py'
BASELINE = 'programs/baseline_bz2/program.py'
PACKAGE = [CODEC]
spec = importlib.util.spec_from_file_location(__name__ + '_driver', ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF, driver.CODEC = SELF, CODEC
require = driver.require
SCHEMA = 'gamma.enwiki9.raw-reverse-bz2-gate-plan.v1'
ARMS = [dict(id=a, mode=a) for a in ('P', 'K', 'D')]
OPENING_SHA = '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'
HEADER, FRAME = struct.Struct('<8sIIQ'), struct.Struct('<IIB32s')
COSTS = {'bz2_payload', 'framing'}


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def valid_reference(row):
    require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'invalid artifact reference')
    p = Path(row['path'])
    require(not p.is_absolute() and '..' not in p.parts and str(p) == row['path']
            and integer(row['bytes'], 1, 8000000) and re.fullmatch('[a-f0-9]{64}', row['sha256']), 'invalid artifact reference')


def validate_plan(plan, candidate):
    fields = {'schema', 'candidate_id', 'stage', 'population', 'arms', 'block_size', 'resources',
              'phase_wall_seconds', 'phase_cpu_seconds', 'phase_address_bytes', 'runtime_files', 'transform_spec', 'kernel_basis'}
    require(fields <= set(plan) <= fields | {'selection_receipt'}, 'raw-reverse plan fields differ')
    require(plan['schema'] == SCHEMA and plan['candidate_id'] == candidate and plan['arms'] == ARMS
            and plan['stage'] in ('development', 'validation', 'confirmation'), 'frozen P/K/D comparison differs')
    valid_reference(plan['population'])
    require(plan['population']['bytes'] in (250000, 1000000) and plan['block_size'] == 250000, 'population or block partition differs')
    if plan['stage'] == 'development':
        require(plan['population']['bytes'] == 250000 and plan['population']['sha256'] == OPENING_SHA
                and 'selection_receipt' not in plan, 'opening identity or stage differs')
    else:
        require(plan['population']['sha256'] != OPENING_SHA and 'selection_receipt' in plan, 'fresh population and selection receipt required')
        valid_reference(plan['selection_receipt'])
    caps = plan['resources']
    require(caps == dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864, swap_bytes=0, wall_seconds=300)
            and all(type(caps[k]) is int for k in ('memory_bytes', 'scratch_bytes', 'swap_bytes', 'wall_seconds')), 'resource policy differs')
    require(all(type(plan[k]) is int and plan[k] == v for k, v in
                [('phase_cpu_seconds', 60), ('phase_wall_seconds', 90), ('phase_address_bytes', 536870912)]), 'phase bounds differ')
    require(isinstance(plan['runtime_files'], list) and plan['runtime_files'] and plan['kernel_basis'], 'runtime or kernel basis missing')
    codec = importlib.import_module('tools.raw_reverse_bz2_v1')
    require(plan['transform_spec'] == codec.TRANSFORM_SPEC, 'frozen transform specification differs')


driver.validate_plan = validate_plan


def authenticate(candidate, validate_only=False):
    require(isinstance(candidate, str) and re.fullmatch('[a-z0-9_]+', candidate), 'invalid candidate')
    prospective = driver.read_json(ROOT / 'operations/adaptive/experiments' / (candidate + '.json'))
    closure = {SELF, SHARED_DRIVER, HARNESS_BASE, BASELINE, TESTS, *PACKAGE}
    require(closure.issubset({r['path'] for r in prospective['inputs']}), 'raw-reverse source closure unbound')
    contract, reference, plan = driver.authenticate(candidate, validate_only)
    inputs = {r['path']: r for r in contract['inputs']}
    require(closure.issubset(inputs), 'raw-reverse source closure unbound')
    require([json.loads(c['definition']) for c in contract['controls']] == ARMS, 'contract control definitions differ')
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve() for r in plan['runtime_files']), 'current interpreter is not frozen')
    if 'selection_receipt' in plan:
        row = plan['selection_receipt']
        bound = inputs.get(row['path'])
        require(bound is not None and bound['sha256'].removeprefix('sha256:') == row['sha256']
                and (ROOT / row['path']).stat().st_size == row['bytes'], 'selection receipt unbound')
        previous = driver.read_json(ROOT / row['path'])
        require(previous['schema'] == 'gamma.enwiki9.raw-reverse-bz2-stage.v1' and previous['status'] == 'passed'
                and previous['correctness_pass'] is True and previous['frozen_inputs_reverified'] is True
                and previous['costs']['strict_d_improvement'] is True and previous['costs']['confirmation_eligible'] is True
                and previous['candidate_id'] != candidate, 'prior selection did not pass')
        previous_population = {r['artifacts']['restored']['sha256'] for r in previous['arms']}
        require(len(previous_population) == 1 and plan['population']['sha256'] not in previous_population, 'selection population reused')
    return contract, reference, plan


def common_report(report):
    result = copy.deepcopy(report)
    result.pop('requested_mode', None)
    return result


def checked_wrapper(wrapper):
    require(wrapper['complete_package_bytes'] is None and wrapper['full_corpus_score_bytes'] is None, 'unsupported package or score credit')
    for field in ('cpu_seconds', 'elapsed_seconds'):
        require(type(wrapper[field]) in (int, float) and math.isfinite(wrapper[field]) and wrapper[field] >= 0, 'invalid child timing')
    require(integer(wrapper['peak_process_rss_kib'], 1, 2**40), 'invalid child RSS')
    return wrapper['result']


def checked_report(report, arm, archive, plan, raw):
    data = archive.read_bytes()
    magic, block_size, count, total = HEADER.unpack_from(data)
    require(magic == b'D2REVB01' and block_size == plan['block_size'] == report['block_size']
            and total == len(raw) == plan['population']['bytes'] == report['raw_bytes']
            and report['raw_sha256'] == hashlib.sha256(raw).hexdigest() == plan['population']['sha256']
            and report['archive_sha256'] == hashlib.sha256(data).hexdigest()
            and count == len(report['frames']) == (len(raw) + block_size - 1) // block_size,
            'archive or population identity differs')
    require(report['requested_mode'] == arm['mode'] and report['backend'] == 'bz2-9', 'codec mode or backend differs')
    require(report['complete_package_bytes'] is None and report['full_corpus_score_bytes'] is None, 'unsupported result package or score')
    costs = report['costs']
    require(set(costs) == COSTS and all(integer(v, 0, len(data)) for v in costs.values())
            and sum(costs.values()) == len(data) == report['complete_archive_bytes'], 'complete archive accounting differs')
    cursor = HEADER.size
    for i, frame in enumerate(report['frames']):
        n, payload, direction, digest = FRAME.unpack_from(data, cursor)
        part = raw[i * block_size:(i + 1) * block_size]
        require(n == len(part) == frame['raw_bytes'] and digest == hashlib.sha256(part).digest()
                and frame['raw_sha256'] == frame['output_sha256'] == digest.hex()
                and type(frame['direction']) is int and direction == frame['direction'] == int(arm['id'] == 'D'), 'frame identity or direction differs')
        require(frame['coded_bytes_sha256'] == hashlib.sha256(part[::-1] if direction else part).hexdigest(), 'coded byte identity differs')
        require(frame['costs'] == dict(bz2_payload=payload, framing=FRAME.size)
                and frame['complete_frame_bytes'] == FRAME.size + payload, 'frame accounting differs')
        cursor += FRAME.size + payload
        require(cursor <= len(data), 'truncated frame')
    require(cursor == len(data), 'trailing archive bytes')
    require(costs == {k: sum(f['costs'][k] for f in report['frames']) + (HEADER.size if k == 'framing' else 0) for k in COSTS},
            'global framing or frame costs differ')
    return costs, report['frames']


def comparison_table(rows, plan):
    by_id = {r['arm']['id']: r for r in rows}
    require(len(rows) == 3 and set(by_id) == {'P', 'K', 'D'}, 'incomplete three-arm table')
    require({r['backend'] for r in rows} == {'bz2-9'}, 'paired backend differs')
    sizes = {a: r['archive_bytes'] for a, r in by_id.items()}
    require(sizes['P'] == sizes['K'], 'P/K cost identity differs')
    for p, k, d in zip(*(by_id[a]['frames'] for a in ('P', 'K', 'D')), strict=True):
        require(p == k and p['raw_sha256'] == d['raw_sha256'] and p['raw_bytes'] == d['raw_bytes'], 'frame population or P/K report differs')
    return dict(schema='gamma.enwiki9.raw-reverse-bz2-costs.v1', raw_bytes=plan['population']['bytes'], archive_bytes=sizes,
                p_minus_k_bytes=0, p_minus_d_bytes=sizes['P']-sizes['D'], strict_d_improvement=sizes['D'] < sizes['P'],
                confirmation_eligible=sizes['D'] < sizes['P'], confirmation_requires_separately_frozen_gate=True,
                fresh_p_measured=True, historical_baseline_used=False, raw_encoder_repeat_proved=True,
                forced_treatment=True, equality_or_loss_authorizes_confirmation=False,
                package_source=[driver.artifact(ROOT/p) for p in PACKAGE], known_source_bytes=sum((ROOT/p).stat().st_size for p in PACKAGE),
                complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0, resource_qualified=False,
                package_gaps=['runtime distribution and license closure', 'accepted source and option accounting'],
                cells=[dict(arm=r['arm'], archive_bytes=r['archive_bytes'], accounting=r['accounting']) for r in rows])


def classify_failure(error, last, plan):
    if last and last['timeout']:
        error = subprocess.TimeoutExpired(last['argv'], plan['phase_wall_seconds'])
    elif last and last['error']:
        error = OSError(last['error'])
    return driver.classification(error, last['returncode'] if last else None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(argv)
    _, reference, plan = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', executed=False, native_phases=9)))
        return 0
    directory = ROOT/'results'/args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), 'nonempty output')
    marker, population = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS']), ROOT/plan['population']['path']
    raw = population.read_bytes()
    stage = dict(schema='gamma.enwiki9.raw-reverse-bz2-stage.v1', candidate_id=args.candidate, experiment=reference,
                 status='running', arms=[], commands=[], objective_credit_bytes=0, complete_package_bytes=None,
                 full_corpus_score_bytes=None, resource_qualified=False, selection_stage=plan['stage'])
    last, table = None, None
    try:
        for arm in ARMS:
            paths = {k: directory/(arm['id']+s) for k, s in [('archive', '.rbz'), ('restored', '.raw'), ('repeat', '.repeat.rbz')]}
            for phase, operation, inp, out in [('encode', 'encode', population, paths['archive']),
                    ('decode', 'decode', paths['archive'], paths['restored']), ('repeat', 'encode', paths['restored'], paths['repeat'])]:
                command = [sys.executable, str(ROOT/CODEC), operation, str(inp), str(out)]
                if operation == 'encode':
                    command += ['--mode', arm['mode'], '--block-size', str(plan['block_size'])]
                last = driver.run_phase(directory, arm['id']+'-'+phase, command, plan, marker)
                stage['commands'].append(last)
                require(last['returncode'] == 0 and not last['timeout'] and last['error'] is None, 'phase failed: '+last['phase'])
            require(paths['restored'].read_bytes() == raw, 'independent inverse differs')
            require(paths['archive'].read_bytes() == paths['repeat'].read_bytes(), 'raw encoder repeat differs')
            wrappers = {p: driver.read_json(directory/(arm['id']+'-'+p+'.stdout')) for p in ('encode', 'decode', 'repeat')}
            reports = {p: checked_wrapper(w) for p, w in wrappers.items()}
            report = reports['encode']
            require(report == reports['repeat'], 'raw encoder repeat report differs')
            require(common_report(report) == common_report(reports['decode']), 'independent decoder projection differs')
            if arm['id'] == 'K':
                require(paths['archive'].read_bytes() == (directory/'P.rbz').read_bytes(), 'P/K archive identity differs')
            costs, frames = checked_report(report, arm, paths['archive'], plan, raw)
            row = dict(arm=arm, archive_bytes=report['complete_archive_bytes'], accounting=costs, frames=frames,
                       backend=report['backend'], exact_inverse=True, deterministic_repeat=True, raw_encoder_repeat_proved=True,
                       repeat_scope='raw-transform-and-encoding', reversed_frames=sum(f['direction'] for f in frames),
                       phase_resources={p: {k: w[k] for k in ('cpu_seconds', 'elapsed_seconds', 'peak_process_rss_kib')} for p, w in wrappers.items()},
                       artifacts={k: driver.artifact(p) for k, p in paths.items()})
            driver.write_json(directory/(arm['id']+'.result.json'), row)
            stage['arms'].append(row)
        table = comparison_table(stage['arms'], plan)
        stage.update(status='passed', correctness_pass=True, accounting_pass=True, p_k_archive_identity_pass=True,
                     raw_encoder_repeat_proved=True, native_phases=len(stage['commands']))
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, accounting_pass=False, native_phases=len(stage['commands']),
                     failure_class=classify_failure(error, last, plan), error=type(error).__name__+': '+str(error))
    try:
        authenticate(args.candidate)
        stage['frozen_inputs_reverified'] = True
        if stage['correctness_pass']:
            driver.write_json(directory/'costs-table.json', table)
            stage['costs'] = table
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, accounting_pass=False, frozen_inputs_reverified=False,
                     failure_class='infrastructure-failure', error='Final authentication or table publication: '+str(error))
    files = [driver.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]
    driver.write_json(directory/'artifacts.json', dict(complete=stage['correctness_pass'], files=files))
    driver.write_json(directory/'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], arms_closed=len(stage['arms']), native_phases=stage['native_phases'])))
    return 0 if stage['correctness_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
