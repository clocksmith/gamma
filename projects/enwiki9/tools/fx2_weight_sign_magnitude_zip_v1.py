#!/usr/bin/env python3
"""Measure exact source/assets ZIPs and relocated native builds; no corpus run."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import shlex
import time
import zipfile
from fx2_weight_adaptive_loader_gate_v1 import FAST, phase
from fx2_weight_neighbor_model_audit_v1 import binding
from fx2_wrt_support_deploy_fixture_v1 import write_bundle

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'operations/provenance/fx2_weight_sign_magnitude_zip_v1_plan.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def extract_exact(archive, destination, expected):
    """Validate the complete member set before creating a fresh extraction tree."""
    with zipfile.ZipFile(archive) as packed:
        infos = packed.infolist()
        names = [info.filename for info in infos]
        if len(set(names)) != len(names) or set(names) != set(expected):
            raise ValueError('ZIP member set differs')
        for info in infos:
            path = PurePosixPath(info.filename)
            if (path.is_absolute() or '..' in path.parts or str(path) != info.filename
                    or '\\' in info.filename or info.is_dir()
                    or ((info.external_attr >> 16) & 0o170000) != 0o100000):
                raise ValueError('invalid ZIP member path or type')
            row = expected[info.filename]
            if info.file_size != row['bytes']:
                raise ValueError('ZIP member size differs')
        destination.mkdir(exist_ok=False)
        for info in infos:
            raw = packed.read(info)
            if digest(raw) != expected[info.filename]['sha256']:
                raise ValueError('ZIP member hash differs')
            target = destination / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(raw)


def member_rows(plan, arm):
    manifest = json.loads((ROOT / plan['member_manifest']).read_text())
    overrides = plan['overrides'].get(arm, {})
    known = {r['path'] for r in manifest['countedFiles']}
    if len(known) != len(manifest['countedFiles']) or not set(overrides).issubset(known):
        raise ValueError('duplicate or unknown package member')
    return [dict(overrides.get(r['path'], dict(path=plan['baseline_root'] + '/' + r['path'],
                                             bytes=r['bytes'], sha256=r['sha256'])),
                 member=r['path'], role=r['role'])
            for r in sorted(manifest['countedFiles'], key=lambda r: r['path'])]


def verify(plan):
    for row in plan['inputs']:
        actual = binding(ROOT / row['path'])
        if any(actual[k] != row[k] for k in ('bytes', 'sha256')):
            raise ValueError('changed input: ' + row['path'])
    rows = [m for arm in ('P', 'D') for m in member_rows(plan, arm)]
    rows += list(plan['native_binaries'].values()) + list(plan['models'].values())
    for row in rows:
        actual = binding(ROOT / row['path'])
        if any(actual[k] != row[k] for k in ('bytes', 'sha256')):
            raise ValueError('changed package input: ' + row['path'])


def run(plan):
    verify(plan)
    output = ROOT / plan['output']
    output.mkdir(exist_ok=False)
    (output / 'tmp').mkdir()
    deadline = time.monotonic() + plan['bounds']['elapsed_seconds']
    members = {arm: member_rows(plan, arm) for arm in ('P', 'D')}
    if [r['member'] for r in members['P']] != [r['member'] for r in members['D']]:
        raise ValueError('matched member paths differ')
    arms = {}
    for arm in ('P', 'D'):
        tree = output / (arm + '-source')
        tree.mkdir()
        expected = {}
        for row in members[arm]:
            target = tree / row['member']
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = (ROOT / row['path']).read_bytes()
            with target.open('xb') as stream:
                stream.write(raw)
            expected[row['member']] = dict(bytes=len(raw), sha256=digest(raw))
        paths = sorted(tree.rglob('*'))
        paths = [p for p in paths if p.is_file()]
        options = plan['invocation_and_build']
        expected['invocation-and-build.txt'] = dict(bytes=len(options.encode()), sha256=digest(options.encode()))
        archive, repeat = output / (arm + '.zip'), output / (arm + '-repeat.zip')
        write_bundle(archive, tree, paths, options)
        write_bundle(repeat, tree, paths, options)
        if archive.read_bytes() != repeat.read_bytes():
            raise ValueError('ZIP repeat differs')
        relocated = output / (arm + '-relocated')
        extract_exact(archive, relocated, expected)
        expected_command = ['/usr/bin/make', '-j1', 'cmix', 'CC=/usr/bin/g++',
                            'CPPFLAGS_PART-THAT-SHOULD-BE-FAST=' + FAST + ' -O3',
                            'CPPFLAGS_PART-THAT-CAN-BE-SLOW=' + FAST + ' -Os']
        command = shlex.split(options.splitlines()[0])
        if command != expected_command:
            raise ValueError('delivered build instruction differs')
        phase(output, 'rebuild-' + arm, command, plan['bounds'], deadline, relocated)
        binary = binding(relocated / 'cmix')
        if any(binary[k] != plan['native_binaries'][arm][k] for k in ('bytes', 'sha256')):
            raise ValueError('relocated native rebuild differs')
        for name, row in expected.items():
            raw = (relocated / name).read_bytes()
            if len(raw) != row['bytes'] or digest(raw) != row['sha256']:
                raise ValueError('build changed an extracted member')
        arms[arm] = dict(archive=binding(archive), repeat=binding(repeat),
                         members=expected, native_binary=binary, exact_extraction=True,
                         deterministic_repeat=True, exact_relocated_build=True)
    verify(plan)
    if time.monotonic() > deadline:
        raise TimeoutError('aggregate elapsed stop')
    if sum(p.stat().st_blocks * 512 for p in output.rglob('*') if p.is_file()) > plan['bounds']['scratch_bytes']:
        raise ValueError('combined scratch stop')
    zip_delta = arms['D']['archive']['bytes'] - arms['P']['archive']['bytes']
    binary_delta = arms['D']['native_binary']['bytes'] - arms['P']['native_binary']['bytes']
    model_delta = plan['models']['D']['bytes'] - plan['models']['P']['bytes']
    result = dict(schema='gamma.enwiki9.sign-magnitude-source-zip.v1', id=plan['id'],
                  status='passed', arms=arms, zip_delta_bytes=zip_delta,
                  decoder_binary_delta_bytes=binary_delta, decoder_model_delta_bytes=model_delta,
                  source_zip_plus_decoder_delta_bytes=zip_delta + binary_delta + model_delta,
                  required_option_bytes_per_arm=len(plan['invocation_and_build'].encode()),
                  option_delta_bytes=0, inherited_runtime_pair_delta_bytes=2 * (binary_delta + model_delta),
                  unchanged_decoder_dictionary_bytes=plan['dictionary_bytes'],
                  dependency_qualification=plan['unresolved'], corpus_executed=False,
                  complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0)
    with (output / 'receipt.json').open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admission', required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(PLAN.read_text())
    admission = json.loads(args.admission.read_text())
    if (admission.get('id') != plan['id'] or admission.get('admitted') is not True
            or admission.get('plan_sha256') != digest(PLAN.read_bytes())):
        raise ValueError('matching source-bound admission required')
    if sorted(os.sched_getaffinity(0)) != plan['bounds']['cpu_set']:
        raise ValueError('CPU assignment differs')
    for limit, value in ((resource.RLIMIT_AS, plan['bounds']['address_space_bytes']),
                         (resource.RLIMIT_CPU, plan['bounds']['cpu_seconds_per_phase']),
                         (resource.RLIMIT_FSIZE, plan['bounds']['per_file_bytes'])):
        resource.setrlimit(limit, (value, value))
    result = run(plan)
    print(json.dumps({k: result[k] for k in ('zip_delta_bytes', 'source_zip_plus_decoder_delta_bytes',
                                           'inherited_runtime_pair_delta_bytes')}))


if __name__ == '__main__':
    main()
