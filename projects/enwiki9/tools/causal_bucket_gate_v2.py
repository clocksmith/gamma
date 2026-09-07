#!/usr/bin/env python3
"""Frozen raw causal-bucket P/K/D comparisons using the existing bounded driver."""
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
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF, CODEC = 'tools/causal_bucket_gate_v2.py', 'tools/causal_bucket_v2.py'
PLAIN, DECODER = 'tools/dualstream_grammar_argtokens_v2.py', 'tools/dualstream_grammar_decode_dispatch_v1.py'
SHARED_DRIVER, TESTS = 'tools/dualstream_grammar_gate_v1.py', 'tests/test_causal_bucket_gate_v2.py'
PACKAGE = [CODEC, PLAIN, 'tools/dualstream_grammar_v1.py', DECODER]
spec = importlib.util.spec_from_file_location(__name__ + '_driver', ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
driver.SELF, driver.CODEC = SELF, CODEC
require = driver.require
SCHEMA = 'gamma.enwiki9.causal-bucket-gate-plan.v1'
ARMS = [dict(id='P', mode='plain'), dict(id='K', mode='K'), dict(id='D', mode='D')]
COSTS = {'deflate_payload', 'framing'}
OPENING_SHA = '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'
PLAIN_SHA = '1c67e760d01c45398bbbd74882ee0026baf0e6995f6a7c782a305dad572c729a'
LEGACY_COSTS = ('literal_definition_bytes', 'structure_bytes', 'content_bytes',
                'argument_reference_bytes', 'exception_bytes', 'framing_bytes')


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def is_hash(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def valid_reference(row):
    require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'invalid artifact reference')
    p = Path(row['path'])
    require(not p.is_absolute() and '..' not in p.parts and str(p) == row['path']
            and integer(row['bytes'], 1, driver.codec.MAX_ARCHIVE) and is_hash(row['sha256']), 'invalid artifact reference')


def validate_plan(plan, candidate):
    fields = {'schema', 'candidate_id', 'stage', 'population', 'arms', 'frame_size', 'resources',
              'phase_wall_seconds', 'phase_cpu_seconds', 'phase_address_bytes', 'runtime_files', 'transform_spec', 'kernel_basis'}
    optional = {'plain_archive', 'selection_receipt'}
    require(fields <= set(plan) <= fields | optional, 'causal-bucket plan fields differ')
    require(plan['schema'] == SCHEMA and plan['candidate_id'] == candidate and plan['arms'] == ARMS
            and plan['stage'] in ('development', 'validation', 'confirmation'), 'frozen P/K/D comparison differs')
    valid_reference(plan['population'])
    require(plan['population']['bytes'] in (250000, 1000000) and plan['frame_size'] == 65536, 'population or frame partition differs')
    if 'plain_archive' in plan:
        valid_reference(plan['plain_archive'])
    if plan['stage'] == 'development':
        require(plan['population']['bytes'] == 250000 and plan.get('plain_archive', {}).get('bytes') == 89041,
                'opening retained baseline required')
        require(plan['population']['sha256'] == OPENING_SHA and plan['plain_archive']['sha256'] == PLAIN_SHA
                and 'selection_receipt' not in plan, 'opening identity or stage differs')
    else:
        require(plan['population']['sha256'] != OPENING_SHA and 'selection_receipt' in plan,
                'fresh population and selection receipt required')
        valid_reference(plan['selection_receipt'])
    caps = plan['resources']
    require(caps == dict(cpus=[2], memory_bytes=1073741824, scratch_bytes=67108864, swap_bytes=0, wall_seconds=300)
            and all(type(caps[k]) is int for k in ('memory_bytes', 'scratch_bytes', 'swap_bytes', 'wall_seconds')),
            'resource policy differs')
    require(type(plan['phase_cpu_seconds']) is int and plan['phase_cpu_seconds'] == 60
            and type(plan['phase_wall_seconds']) is int and plan['phase_wall_seconds'] == 90
            and type(plan['phase_address_bytes']) is int and plan['phase_address_bytes'] == 536870912, 'phase bounds differ')
    require(isinstance(plan['runtime_files'], list) and plan['runtime_files'] and plan['kernel_basis'], 'runtime or kernel basis missing')
    codec = importlib.import_module('tools.causal_bucket_v2')
    require(plan['transform_spec'] == codec.TRANSFORM_SPEC, 'frozen transform specification differs')


driver.validate_plan = validate_plan


def authenticate(candidate, validate_only=False):
    require(isinstance(candidate, str) and re.fullmatch('[a-z0-9_]+', candidate), 'invalid candidate')
    prospective = driver.read_json(ROOT / 'operations/adaptive/experiments' / (candidate + '.json'))
    closure = {SELF, SHARED_DRIVER, TESTS, *PACKAGE}
    require(closure.issubset({r['path'] for r in prospective['inputs']}), 'causal-bucket source closure unbound')
    contract, reference, plan = driver.authenticate(candidate, validate_only)
    inputs = {r['path']: r for r in contract['inputs']}
    require(closure.issubset(inputs), 'causal-bucket source closure unbound')
    if 'plain_archive' in plan:
        row = plan['plain_archive']
        bound = inputs.get(row['path'])
        p = ROOT / row['path']
        require(bound is not None and bound['sha256'].removeprefix('sha256:') == row['sha256']
                and p.stat().st_size == row['bytes'], 'retained plain archive unbound')
        with p.open('rb') as stream:
            require(stream.read(8) == b'D2GRAM02', 'retained plain frontend differs')
    if 'selection_receipt' in plan:
        row = plan['selection_receipt']
        bound = inputs.get(row['path'])
        require(bound is not None and bound['sha256'].removeprefix('sha256:') == row['sha256']
                and (ROOT / row['path']).stat().st_size == row['bytes'], 'selection receipt unbound')
        previous = driver.read_json(ROOT / row['path'])
        require(previous['schema'] == 'gamma.enwiki9.causal-bucket-stage.v1' and previous['status'] == 'passed'
                and previous['correctness_pass'] is True and previous['frozen_inputs_reverified'] is True
                and previous['costs']['strict_d_improvement'] is True and previous['costs']['confirmation_eligible'] is True
                and previous['candidate_id'] != candidate, 'prior selection did not pass')
        previous_population = {r['artifacts']['restored']['sha256'] for r in previous['arms']}
        require(len(previous_population) == 1 and plan['population']['sha256'] not in previous_population,
                'confirmation reuses selection population')
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve() for r in plan['runtime_files']),
            'current interpreter is not frozen')
    return contract, reference, plan


def checked_wrapper(wrapper):
    require(wrapper['complete_package_bytes'] is None and wrapper['full_corpus_score_bytes'] is None, 'unsupported package or score credit')
    for field in ('cpu_seconds', 'elapsed_seconds'):
        require(type(wrapper[field]) in (int, float) and math.isfinite(wrapper[field]) and wrapper[field] >= 0, 'invalid child timing')
    require(integer(wrapper['peak_process_rss_kib'], 1, 2**40), 'invalid child RSS')
    return wrapper['result']


def common_report(report):
    result = copy.deepcopy(report)
    result.pop('mode', None)
    for frame in result['frames']:
        frame.pop('comparison', None)
    return result


def checked_report(report, arm, archive, plan, raw):
    """Bind reported costs to actual stored framing; do not rerun the transform."""
    data = archive.read_bytes()
    header, frame_header = driver.codec.HEADER, driver.codec.FRAME
    magic, frame_size, count, raw_size = header.unpack_from(data)
    require(magic in (b'D2GRAM02', b'D2BUKT01') and frame_size == plan['frame_size'] == report['frame_size']
            and raw_size == len(raw) == plan['population']['bytes'] == report['raw_bytes']
            and hashlib.sha256(raw).hexdigest() == plan['population']['sha256']
            and count == len(report['frames']) == (len(raw) + frame_size - 1) // frame_size,
            'raw population or frame count differs')
    require(report['backend'] == 'zlib9', 'backend differs')
    plain = arm['id'] == 'P'
    if plain:
        require(report['requested_mode'] == 'plain', 'plain encoder differs')
        values = {k: report[k] for k in LEGACY_COSTS}
        require(all(integer(v, 0, len(data)) for v in values.values()), 'invalid plain costs')
        costs = dict(deflate_payload=sum(values.values()) - values['framing_bytes'], framing=values['framing_bytes'])
    else:
        costs = report['costs']
        require(report['mode'] == arm['id'] and report['raw_sha256'] == hashlib.sha256(raw).hexdigest()
                and report['archive_sha256'] == hashlib.sha256(data).hexdigest()
                and report['complete_package_bytes'] is None and report['full_corpus_score_bytes'] is None, 'report identity or scope differs')
    require(set(costs) == COSTS and all(integer(v, 0, len(data)) for v in costs.values())
            and sum(costs.values()) == len(data) == report['complete_archive_bytes'], 'complete archive accounting differs')
    cursor, frames = header.size, []
    for index, f in enumerate(report['frames']):
        n, mode, *tail = frame_header.unpack_from(data, cursor)
        lengths, digest = tail[:5], tail[5]
        part = raw[index * frame_size:(index + 1) * frame_size]
        require(n == len(part) == f['raw_bytes'] and digest == hashlib.sha256(part).digest()
                and mode in (0, 5) and lengths[:3] == [0, 0, 0] and lengths[4] == 0, 'stored frame partition or mode differs')
        stored = data[cursor + frame_header.size:cursor + frame_header.size + sum(lengths)]
        require(len(stored) == sum(lengths), 'truncated frame')
        fc = dict(deflate_payload=len(stored), framing=frame_header.size)
        size = sum(fc.values())
        if plain:
            require(mode == 0 and f['mode'] == 'plain' and f['templates'] == f['supplied_arguments'] == f['repeated_argument_references'] == 0,
                    'plain frame is not plain')
            require(f['complete_archive_bytes'] == size and sum(f[k] for k in LEGACY_COSTS) == size, 'plain frame accounting differs')
            frame = dict(raw_bytes=n, raw_sha256=digest.hex(), mode='plain', complete_frame_bytes=size, costs=fc)
        else:
            require(f['raw_sha256'] == f['output_sha256'] == digest.hex() and is_hash(f['transmitted_payload_sha256'])
                    and f['mode'] == ('bucket' if mode == 5 else 'plain') and f['costs'] == fc
                    and f['complete_frame_bytes'] == size, 'frame identity or cost differs')
            c = f['comparison']
            require(set(c) == {'plain_bytes', 'bucket_bytes', 'delta', 'selected', 'transform_sha256', 'counts_sha256'}
                    and all(integer(c[k], 1, driver.codec.MAX_ARCHIVE) for k in ('plain_bytes', 'bucket_bytes'))
                    and type(c['delta']) is int and c['delta'] == c['plain_bytes'] - c['bucket_bytes']
                    and type(c['selected']) is bool and c['selected'] == (arm['id'] == 'D' and c['delta'] > 0)
                    and is_hash(c['transform_sha256']) and is_hash(c['counts_sha256']), 'invalid whole-frame comparison')
            require((mode == 5) == c['selected'] and size == c['bucket_bytes' if c['selected'] else 'plain_bytes'],
                    'non-strict frame admission or fallback differs')
            require(f['transmitted_payload_sha256'] == (c['transform_sha256'] if mode == 5 else digest.hex()),
                    'transmitted payload identity differs')
            frame = f
        frames.append(frame)
        cursor += size
    require(cursor == len(data), 'trailing archive bytes')
    require(magic == (b'D2BUKT01' if any(f['mode'] == 'bucket' for f in frames) else b'D2GRAM02'), 'archive magic or fallback differs')
    require(costs == {k: sum(f['costs'][k] for f in frames) + (header.size if k == 'framing' else 0) for k in COSTS},
            'global framing or frame costs differ')
    return costs, frames


def comparison_table(rows, plan):
    by_id = {r['arm']['id']: r for r in rows}
    require(len(rows) == 3 and set(by_id) == {'P', 'K', 'D'}, 'incomplete three-arm table')
    require({r['backend'] for r in rows} == {'zlib9'} and len({r['zlib_version'] for r in rows}) == 1, 'paired backend differs')
    sizes = {a: r['archive_bytes'] for a, r in by_id.items()}
    require(sizes['P'] == sizes['K'] and sizes['D'] <= sizes['P'], 'plain-control or selective cost invariant differs')
    for p, k, d in zip(*(by_id[a]['frames'] for a in ('P', 'K', 'D')), strict=True):
        require(k['complete_frame_bytes'] == p['complete_frame_bytes'] == k['comparison']['plain_bytes'] == d['comparison']['plain_bytes'],
                'plain comparison cost differs')
        require({a: b for a, b in k['comparison'].items() if a != 'selected'} ==
                {a: b for a, b in d['comparison'].items() if a != 'selected'}, 'K/D transformed candidate differs')
    return dict(schema='gamma.enwiki9.causal-bucket-costs.v1', raw_bytes=plan['population']['bytes'], archive_bytes=sizes,
                p_minus_k_bytes=sizes['P']-sizes['K'], p_minus_d_bytes=sizes['P']-sizes['D'],
                strict_d_improvement=sizes['D'] < sizes['P'], confirmation_eligible=sizes['D'] < sizes['P'],
                confirmation_requires_separately_frozen_gate=True, fallback_equality_authorizes_confirmation=False,
                raw_encoder_repeat_proved=True, package_source=[driver.artifact(ROOT/p) for p in PACKAGE],
                known_source_bytes=sum((ROOT/p).stat().st_size for p in PACKAGE), complete_package_bytes=None,
                full_corpus_score_bytes=None, objective_credit_bytes=0, resource_qualified=False,
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
    directory = ROOT / 'results' / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), 'nonempty output')
    marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    population = ROOT / plan['population']['path']
    raw = population.read_bytes()
    stage = dict(schema='gamma.enwiki9.causal-bucket-stage.v1', candidate_id=args.candidate, experiment=reference,
                 status='running', arms=[], commands=[], objective_credit_bytes=0, complete_package_bytes=None,
                 full_corpus_score_bytes=None, resource_qualified=False, selection_stage=plan['stage'])
    last, table = None, None
    try:
        for arm in ARMS:
            paths = {k: directory/(arm['id']+s) for k, s in [('archive', '.d2g'), ('restored', '.raw'), ('repeat', '.repeat.d2g')]}
            for phase, operation, inp, out in [('encode', 'encode', population, paths['archive']),
                    ('decode', 'decode', paths['archive'], paths['restored']), ('repeat', 'encode', paths['restored'], paths['repeat'])]:
                tool = (PLAIN if operation == 'encode' else DECODER) if arm['id'] == 'P' else CODEC
                command = [sys.executable, str(ROOT/tool), operation, str(inp), str(out)]
                if operation == 'encode':
                    command += ['--mode', arm['mode'], '--frame-size', str(plan['frame_size'])]
                last = driver.run_phase(directory, arm['id']+'-'+phase, command, plan, marker)
                stage['commands'].append(last)
                require(last['returncode'] == 0 and not last['timeout'] and last['error'] is None, 'phase failed: '+last['phase'])
            require(paths['restored'].read_bytes() == raw, 'independent inverse differs')
            require(paths['archive'].read_bytes() == paths['repeat'].read_bytes(), 'raw encoder repeat differs')
            wrappers = {p: driver.read_json(directory/(arm['id']+'-'+p+'.stdout')) for p in ('encode', 'decode', 'repeat')}
            reports = {p: checked_wrapper(w) for p, w in wrappers.items()}
            report = reports['encode']
            require(report == reports['repeat'], 'raw encoder repeat report differs')
            if arm['id'] == 'P':
                if 'plain_archive' in plan:
                    require(driver.sha(paths['archive']) == plan['plain_archive']['sha256']
                            and paths['archive'].stat().st_size == plan['plain_archive']['bytes'], 'retained P diagonal differs')
                require(reports['decode']['raw_bytes'] == len(raw) and reports['decode']['frontend'] == 'D2GRAM02', 'plain decoder differs')
            else:
                require(common_report(report) == common_report(reports['decode']), 'independent decoder projection differs')
                if arm['id'] == 'K':
                    require(paths['archive'].read_bytes() == (directory/'P.d2g').read_bytes(), 'P/K archive identity differs')
            costs, frames = checked_report(report, arm, paths['archive'], plan, raw)
            selected = sum(f['mode'] == 'bucket' for f in frames)
            if arm['id'] == 'D' and not selected:
                require(paths['archive'].read_bytes() == (directory/'P.d2g').read_bytes(), 'all-plain fallback archive differs')
            row = dict(arm=arm, archive_bytes=report['complete_archive_bytes'], accounting=costs, frames=frames,
                       backend=report['backend'], zlib_version=report['zlib_version'], exact_inverse=True,
                       deterministic_repeat=True, raw_encoder_repeat_proved=True, repeat_scope='raw-transform-and-encoding',
                       selected_frames=selected, phase_resources={p: {k: w[k] for k in ('cpu_seconds', 'elapsed_seconds', 'peak_process_rss_kib')}
                           for p, w in wrappers.items()}, artifacts={k: driver.artifact(p) for k, p in paths.items()})
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
