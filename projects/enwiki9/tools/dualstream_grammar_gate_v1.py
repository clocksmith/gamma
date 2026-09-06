#!/usr/bin/env python3
"""Bounded standalone grammar comparisons through the existing adaptive queue.

Every configuration is explicit before this worker starts. Development may
compare several configurations; confirmation evaluates one frozen selection.
No model campaign, external parent or compiler is loaded by this runner.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from tools import dualstream_grammar_v1 as codec

SELF = "tools/dualstream_grammar_gate_v1.py"
CODEC = "tools/dualstream_grammar_v1.py"
SCHEMA = "gamma.enwiki9.dualstream-grammar-gate-plan.v1"
require = codec.require


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def artifact(path):
    path = Path(path)
    return dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=sha(path))


def write_json(path, value):
    data = (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()
    codec.new_file(path, lambda target: target.write(data))


def validate_plan(plan, candidate):
    require(set(plan) == {'schema', 'candidate_id', 'stage', 'population', 'arms', 'frame_size',
                          'resources', 'phase_wall_seconds', 'phase_cpu_seconds', 'phase_address_bytes', 'runtime_files'}, 'plan fields differ')
    require(plan['schema'] == SCHEMA and plan['candidate_id'] == candidate, 'plan identity differs')
    require(plan['stage'] in ('development', 'validation', 'confirmation'), 'unknown selection stage')
    require(plan['population']['bytes'] in (250000, 1000000), 'population must be250KB or1MB')
    require(plan['frame_size'] == codec.MAX_FRAME, 'frame policy differs')
    arms = plan['arms']
    require(4 <= len(arms) <= 18 and len({a['id'] for a in arms}) == len(arms), 'arm count or identity differs')
    require({a['mode'] for a in arms} == set(codec.MODES), 'all four ablations are mandatory')
    for arm in arms:
        require(set(arm) == {'id', 'mode', 'config'} and __import__('re').fullmatch(r'[A-Za-z0-9_]+', arm['id']), 'invalid arm')
        codec.Config(**arm['config']).validate()
    if plan['stage'] == 'confirmation':
        require(len(arms) == 4 and len({json.dumps(a['config'], sort_keys=True) for a in arms}) == 1, 'confirmation cannot tune configurations')
    caps = plan['resources']
    require(set(caps) == {'cpus', 'memory_bytes', 'scratch_bytes', 'swap_bytes', 'wall_seconds'} and
            caps['cpus'] == [2] and caps['swap_bytes'] == 0 and
            512 * 1024**2 <= caps['memory_bytes'] <= 2 * 1024**3 and
            1 <= caps['scratch_bytes'] <= 512 * 1024**2 and 1 <= caps['wall_seconds'] <= 1800, 'resource bounds differ')
    require(1 <= plan['phase_cpu_seconds'] <= 120 and 1 <= plan['phase_wall_seconds'] <= 180 and
            256 * 1024**2 <= plan['phase_address_bytes'] <= caps['memory_bytes'], 'phase bounds differ')
    require(plan['runtime_files'], 'runtime identity is missing')


def authenticate(candidate, validate_only=False):
    require(__import__('re').fullmatch(r'[a-z0-9_]+', candidate), 'invalid candidate')
    path = ROOT / 'operations/adaptive/experiments' / (candidate + '.json')
    contract = read_json(path)
    reference = dict(path=str(path.relative_to(ROOT)), sha256='sha256:' + sha(path))
    require(contract['experimentId'] == candidate and contract['status'] == 'frozen' and
            contract['registrationTiming'] == 'prospective' and contract['objectiveCreditBytes'] == 0, 'contract authority differs')
    inputs = {r['path']: r for r in contract['inputs']}
    require(len(inputs) == len(contract['inputs']) and SELF in inputs and CODEC in inputs, 'source binding missing')
    for name, row in inputs.items():
        p = ROOT / name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve() == p and p.is_file(), 'aliased input')
        require(sha(p) == row['sha256'].removeprefix('sha256:'), 'changed frozen input: ' + name)
    plans = [row for row in inputs.values() if row['id'] == 'grammar-gate-plan']
    require(len(plans) == 1, 'one grammar plan is required')
    plan = read_json(ROOT / plans[0]['path'])
    validate_plan(plan, candidate)
    population = plan['population']
    require(population['path'] in inputs and population['sha256'].removeprefix('sha256:') == inputs[population['path']]['sha256'].removeprefix('sha256:'), 'population unbound')
    require((ROOT / population['path']).stat().st_size == population['bytes'] == contract['population']['scopeBytes'], 'population size differs')
    for row in plan['runtime_files']:
        p = Path(row['path'])
        require(p.is_absolute() and p.is_file() and p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'runtime identity changed')
    if not validate_only:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) == reference, 'canonical invocation absent')
        require(os.sched_getaffinity(0) == {2}, 'worker must inherit CPU2')
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        job_id = marker.parent.name.removesuffix('.resources')
        require(marker == ROOT / 'run_logs/adaptive' / (job_id + '.resources/phases.jsonl') and marker.resolve() == marker, 'phase owner differs')
        jobs = list((ROOT / 'operations/adaptive/running').glob('*' + job_id + '.json'))
        require(len(jobs) == 1, 'running job missing or ambiguous')
        job = read_json(jobs[0])
        require(job['candidate_id'] == candidate and job['experiment'] == reference and job['state'] == 'running' and
                job['execution_mode'] == 'discovery' and all(job['resource_budget'].get(k) == v for k, v in plan['resources'].items()), 'job authority differs')
        group = Path(job['execution_resources']['cgroup_path'])
        membership = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
        require(group == Path('/sys/fs/cgroup' + membership) and group.stat().st_ino == job['execution_resources']['cgroup_inode'], 'resource group differs')
        require((group / 'memory.max').read_text().strip() == str(plan['resources']['memory_bytes']) and
                (group / 'memory.swap.max').read_text().strip() == '0', 'memory enforcement differs')
    return contract, reference, plan


def classification(error, returncode=None):
    if isinstance(error, subprocess.TimeoutExpired) or returncode == -signal.SIGXCPU:
        return 'budget-exhausted'
    if isinstance(error, OSError) or returncode == -signal.SIGKILL:
        return 'infrastructure-failure'
    return 'implementation-failure'


def run_phase(directory, phase, argv, plan, marker):
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU, (plan['phase_cpu_seconds'], plan['phase_cpu_seconds']))
        resource.setrlimit(resource.RLIMIT_AS, (plan['phase_address_bytes'], plan['phase_address_bytes']))
        resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    def event(kind):
        with marker.open('a') as stream:
            stream.write(json.dumps(dict(phase=phase, event=kind)) + '\n')
    event('start')
    begin = time.monotonic()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = dict(phase=phase, argv=argv, returncode=None, timeout=False, error=None)
    try:
        with (directory / (phase + '.stdout')).open('xb') as out, (directory / (phase + '.stderr')).open('xb') as err:
            with subprocess.Popen(argv, stdout=out, stderr=err, preexec_fn=limits, start_new_session=True,
                                  env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'PYTHONDONTWRITEBYTECODE': '1'}) as child:
                try:
                    result['returncode'] = child.wait(timeout=plan['phase_wall_seconds'])
                except subprocess.TimeoutExpired:
                    result['timeout'] = True
                    os.killpg(child.pid, signal.SIGKILL)
                    result['returncode'] = child.wait()
    except OSError as error:
        result['error'] = str(error)
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        result.update(elapsed_seconds=time.monotonic() - begin, user_cpu_seconds=after.ru_utime - before.ru_utime,
                      system_cpu_seconds=after.ru_stime - before.ru_stime, timing_authority='shared-host diagnostic')
        write_json(directory / (phase + '.execution.json'), result)
        event('end')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args()
    contract, reference, plan = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', raw_bytes=plan['population']['bytes'], arms=len(plan['arms']), native_phases=3 * len(plan['arms']), executed=False)))
        return 0
    directory = ROOT / 'results' / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), 'result directory must be empty')
    marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    population = ROOT / plan['population']['path']
    raw = population.read_bytes()
    stage = dict(schema='gamma.enwiki9.dualstream-grammar-stage.v1', candidate_id=args.candidate, experiment=reference,
                 selection_stage=plan['stage'], raw_bytes=len(raw), status='running', arms=[], commands=[], objective_credit_bytes=0,
                 complete_package_bytes=None, full_corpus_score_bytes=None, resource_qualified=False)
    last = None
    try:
        for arm in plan['arms']:
            paths = {k: directory / (arm['id'] + suffix) for k, suffix in
                     [('archive', '.d2g'), ('restored', '.raw'), ('repeat', '.repeat.d2g')]}
            options = ['--mode', arm['mode'], '--frame-size', str(plan['frame_size'])]
            for key in ('max_rule_length', 'grammar_budget', 'min_benefit'):
                options += ['--' + key.replace('_', '-'), str(arm['config'][key])]
            for phase, operation, source, output in [('encode', 'encode', population, paths['archive']),
                    ('decode', 'decode', paths['archive'], paths['restored']), ('repeat', 'encode', paths['restored'], paths['repeat'])]:
                command = [sys.executable, str(ROOT / CODEC), operation, str(source), str(output)] + (options if operation == 'encode' else [])
                last = run_phase(directory, arm['id'] + '-' + phase, command, plan, marker)
                stage['commands'].append(last)
                require(last['returncode'] == 0 and not last['timeout'] and last['error'] is None, 'codec phase failed: ' + last['phase'])
            require(paths['restored'].read_bytes() == raw and paths['archive'].read_bytes() == paths['repeat'].read_bytes(), 'inverse or repeat differs')
            reports = {phase: read_json(directory / (arm['id'] + '-' + phase + '.stdout')) for phase in ('encode', 'decode', 'repeat')}
            require(reports['encode']['result'] == reports['repeat']['result'], 'deterministic encode accounting differs')
            report = reports['encode']['result']
            require(report['complete_archive_bytes'] == paths['archive'].stat().st_size, 'archive accounting differs')
            keys = ('literal_definition_bytes', 'structure_bytes', 'content_bytes', 'argument_reference_bytes', 'exception_bytes', 'framing_bytes')
            require(sum(report[k] for k in keys) == report['complete_archive_bytes'], 'component byte accounting differs')
            row = dict(arm=arm, archive_bytes=report['complete_archive_bytes'], accounting={k: report[k] for k in keys},
                       encode_cpu_seconds=reports['encode']['cpu_seconds'], decode_cpu_seconds=reports['decode']['cpu_seconds'],
                       encode_peak_rss_kib=reports['encode']['peak_process_rss_kib'], decode_peak_rss_kib=reports['decode']['peak_process_rss_kib'],
                       exact_inverse=True, deterministic_repeat=True, supplied_arguments=sum(f['supplied_arguments'] for f in report['frames']),
                       repeated_argument_references=sum(f['repeated_argument_references'] for f in report['frames']),
                       artifacts={k: artifact(p) for k, p in paths.items()})
            write_json(directory / (arm['id'] + '.result.json'), row)
            stage['arms'].append(row)
        stage.update(status='passed', correctness_pass=True, native_phases=len(stage['commands']))
    except Exception as error:
        classified_error = error
        if last and last['timeout']:
            classified_error = subprocess.TimeoutExpired(last['argv'], plan['phase_wall_seconds'])
        elif last and last['error']:
            classified_error = OSError(last['error'])
        stage.update(status='failed', correctness_pass=False, native_phases=len(stage['commands']),
                     failure_class=classification(classified_error, last['returncode'] if last else None), error=type(error).__name__ + ': ' + str(error))
    try:
        authenticate(args.candidate)
        stage['frozen_inputs_reverified'] = True
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, frozen_inputs_reverified=False,
                     failure_class='infrastructure-failure', error='Final source authentication: ' + str(error))
    files = [artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]
    write_json(directory / 'artifacts.json', dict(complete=stage['correctness_pass'], files=files))
    write_json(directory / 'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], arms_closed=len(stage['arms']), native_phases=stage['native_phases'])))
    return 0 if stage['correctness_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
