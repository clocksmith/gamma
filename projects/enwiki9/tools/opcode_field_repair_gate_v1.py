#!/usr/bin/env python3
"""Run the sealed field-only P/K/D comparison through the existing phase driver."""
from __future__ import annotations
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = 'tools/opcode_field_repair_gate_v1.py'
TESTS = 'tests/test_opcode_field_repair_gate_v1.py'
SHARED_DRIVER = 'tools/dualstream_grammar_gate_v1.py'
HARNESS_BASE = 'tools/dualstream_grammar_v1.py'
spec = importlib.util.spec_from_file_location(__name__ + '_driver', ROOT / SHARED_DRIVER)
driver = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = driver
spec.loader.exec_module(driver)
require = driver.require
SCHEMA = 'gamma.enwiki9.opcode-field-gate-plan.v1'
ARMS = [dict(id=a, mode=a) for a in ('P', 'K', 'D')]
OPENING_SHA = '665fc689441b68462d88f82dc33212abe9c4824be095d03a556c9b55a2829fd3'
HISTORICAL = dict(archive_bytes=67959, archive_sha256='a2b4d6385b9cc211ec819873665b331166d78334c2d05b8114ff16efd8ceea87')
CAPS = dict(cpus=[2], memory_bytes=4294967296, scratch_bytes=536870912, swap_bytes=0, wall_seconds=3600)
PHASE_CAPS = dict(phase_cpu_seconds=300, phase_wall_seconds=420, phase_address_bytes=2147483648)


def integer(value, low, high):
    return type(value) is int and low <= value <= high


def hash_text(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def reference_shape(row, absolute=False):
    require(isinstance(row, dict) and set(row) == {'path', 'bytes', 'sha256'}, 'invalid file reference')
    name = Path(row['path'])
    require(name.is_absolute() == absolute and '..' not in name.parts and str(name) == row['path']
            and integer(row['bytes'], 1, 2**34) and hash_text(row['sha256']), 'invalid file reference')


def check_file(row, absolute=False, snapshot=None, candidate=None):
    reference_shape(row, absolute)
    path = Path(row['path']) if absolute else ROOT / row['path']
    prefix = 'programs/' + str(candidate) + '/'
    if snapshot is not None and row['path'].startswith(prefix):
        path = snapshot / row['path'][len(prefix):]
    require(path.is_file() and (absolute or path.resolve() == path), 'missing or aliased file: ' + row['path'])
    require(path.stat().st_size == row['bytes'] and driver.sha(path) == row['sha256'], 'changed file: ' + row['path'])
    return path


def validate_plan(plan, candidate):
    fields = {'schema', 'candidate_id', 'stage', 'population', 'arms', 'resources', 'runtime_files',
              'cli', 'source_files', 'package_files', 'parent_package_files', 'kernel_basis',
              'historical_parent', *PHASE_CAPS}
    require(set(plan) == fields and plan['schema'] == SCHEMA and plan['candidate_id'] == candidate,
            'plan fields or identity differ')
    require(plan['stage'] == 'development' and plan['arms'] == ARMS, 'only frozen development P/K/D authorized')
    reference_shape(plan['population'])
    require(plan['population']['bytes'] == 250000 and plan['population']['sha256'] == OPENING_SHA
            and plan['historical_parent'] == HISTORICAL, 'historical opening population differs')
    require(plan['resources'] == CAPS and all(type(plan['resources'][k]) is int for k in CAPS if k != 'cpus')
            and all(type(plan[k]) is int and plan[k] == v for k, v in PHASE_CAPS.items()), 'resource bounds differ')
    reference_shape(plan['cli'])
    for key in ('source_files', 'package_files', 'parent_package_files', 'kernel_basis', 'runtime_files'):
        rows = plan[key]
        require(isinstance(rows, list) and rows and len({r['path'] for r in rows}) == len(rows), 'missing or duplicate ' + key)
        for row in rows:
            reference_shape(row, absolute=key == 'runtime_files')
    sources = {r['path']: r for r in plan['source_files']}
    require({SELF, TESTS, SHARED_DRIVER, HARNESS_BASE, plan['cli']['path']} <= set(sources)
            and sources[plan['cli']['path']] == plan['cli'], 'runner/CLI source closure missing')
    require({r['path'] for r in plan['package_files']} <= set(sources), 'candidate package source unbound')


def verify_snapshot(snapshot, revision):
    require(snapshot.is_absolute() and snapshot.resolve() == snapshot and snapshot.is_dir(), 'invalid candidate snapshot')
    records = revision['files']
    require(records and len({r['path'] for r in records}) == len(records), 'invalid snapshot manifest')
    for row in records:
        path = snapshot / row['path']
        require(not Path(row['path']).is_absolute() and '..' not in Path(row['path']).parts
                and path.resolve() == path and path.is_file(), 'aliased snapshot file')
        require(path.stat().st_size == row['bytes'] and driver.sha(path) == row['sha256'], 'snapshot source differs')
    actual = {str(p.relative_to(snapshot)) for p in snapshot.rglob('*') if p.is_file()}
    require(actual == {r['path'] for r in records}, 'snapshot has unbound files')


def authenticate(candidate, validate_only=False):
    require(isinstance(candidate, str) and re.fullmatch('[a-z0-9_]+', candidate), 'invalid candidate')
    path = ROOT / 'operations/adaptive/experiments' / (candidate + '.json')
    contract = driver.read_json(path)
    reference = dict(path=str(path.relative_to(ROOT)), sha256='sha256:' + driver.sha(path))
    require(contract['experimentId'] == candidate and contract['status'] == 'frozen'
            and contract['registrationTiming'] == 'prospective' and contract['objectiveCreditBytes'] == 0,
            'frozen contract authority differs')
    require([json.loads(c['definition']) for c in contract['controls']] == ARMS, 'contract controls differ')
    inputs = {r['path']: r for r in contract['inputs']}
    require(len(inputs) == len(contract['inputs']), 'duplicate frozen inputs')
    for name, row in inputs.items():
        p = ROOT / name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve() == p
                and p.is_file() and driver.sha(p) == row['sha256'].removeprefix('sha256:'), 'changed frozen input: ' + name)
    snapshot = Path(os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ROOT']) if not validate_only else ROOT / 'programs' / candidate
    plan = driver.read_json(snapshot / 'gate-plan.json')
    validate_plan(plan, candidate)
    for key in ('source_files', 'package_files', 'parent_package_files', 'kernel_basis'):
        for row in plan[key]:
            check_file(row, snapshot=snapshot, candidate=candidate)
    check_file(plan['population'])
    require(plan['population']['path'] in inputs and inputs[plan['population']['path']]['sha256'] == 'sha256:' + plan['population']['sha256']
            and contract['population']['scopeBytes'] == plan['population']['bytes'], 'population is not contract-bound')
    for row in plan['runtime_files']:
        check_file(row, absolute=True)
    require(any(Path(r['path']).resolve() == Path(sys.executable).resolve() for r in plan['runtime_files']), 'interpreter not bound')
    if not validate_only:
        require(json.loads(os.environ['GAMMA_ENWIKI9_EXPERIMENT_JSON']) == reference
                and os.environ['GAMMA_ENWIKI9_SNAPSHOT_CANDIDATE_ID'] == candidate, 'canonical invocation absent')
        require(os.sched_getaffinity(0) == {2}, 'worker must inherit CPU2')
        marker = Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
        job_id = marker.parent.name.removesuffix('.resources')
        require(marker == ROOT / 'run_logs/adaptive' / (job_id + '.resources/phases.jsonl') and marker.resolve() == marker,
                'phase owner differs')
        jobs = list((ROOT / 'operations/adaptive/running').glob('*' + job_id + '.json'))
        require(len(jobs) == 1, 'running job missing or ambiguous')
        job = driver.read_json(jobs[0])
        require(job['candidate_id'] == candidate and job['experiment'] == reference and job['state'] == 'running'
                and job['execution_mode'] == 'discovery' and not job.get('held', False)
                and all(job['resource_budget'].get(k) == v for k, v in plan['resources'].items()), 'job authority differs')
        require(job['runner'] == dict(path=SELF, sha256='sha256:' + driver.sha(ROOT / SELF)), 'queued runner differs')
        binding = json.loads(os.environ['GAMMA_ENWIKI9_CANDIDATE_REVISION_JSON'])
        require(binding == dict(candidateId=candidate, candidateTreeSha256=job['candidate_tree_sha256'], receipt=job['candidate_revision']),
                'candidate revision environment differs')
        ref = job['candidate_revision']
        rp = ROOT / ref['path']
        require(rp.resolve() == rp and driver.sha(rp) == ref['sha256'].removeprefix('sha256:'), 'revision receipt changed')
        revision = driver.read_json(rp)
        require(revision['candidateId'] == candidate and revision['candidateTreeSha256'] == job['candidate_tree_sha256']
                and snapshot.name == candidate and snapshot.parent.name.startswith('gamma-enwiki9-' + job_id + '-'), 'snapshot owner differs')
        verify_snapshot(snapshot, revision)
        group = Path(job['execution_resources']['cgroup_path'])
        membership = next(line[3:] for line in Path('/proc/self/cgroup').read_text().splitlines() if line.startswith('0::'))
        require(group == Path('/sys/fs/cgroup' + membership) and group.stat().st_ino == job['execution_resources']['cgroup_inode'],
                'resource group differs')
        require((group / 'memory.max').read_text().strip() == str(CAPS['memory_bytes'])
                and (group / 'memory.swap.max').read_text().strip() == '0', 'memory enforcement differs')
    return contract, reference, plan, snapshot


def checked_wrapper(wrapper):
    for key in ('cpu_seconds', 'elapsed_seconds'):
        require(type(wrapper[key]) in (int, float) and math.isfinite(wrapper[key]) and wrapper[key] >= 0, 'invalid phase timing')
    require(integer(wrapper['peak_process_rss_kib'], 1, 2**40), 'invalid phase memory')
    return wrapper['result']


def common_report(report):
    result = copy.deepcopy(report)
    result.pop('arm', None)
    return result


def checked_report(report, arm, archive, raw, plan):
    data = archive.read_bytes()
    require(report['arm'] == arm and report['raw_bytes'] == len(raw) == plan['population']['bytes']
            and report['raw_sha256'] == hashlib.sha256(raw).hexdigest() == plan['population']['sha256'], 'reported raw identity differs')
    require(report['archive_bytes'] == len(data) and report['archive_sha256'] == hashlib.sha256(data).hexdigest(), 'reported archive identity differs')
    require(report['arm_value_bytes'] == 1 and report['archive_plus_arm_value_bytes'] == len(data) + 1
            and report['complete_options_bytes'] is None, 'archive and arm value accounting differs')
    require(integer(report['modeled_bytes'], 1, len(raw) * 2), 'invalid modeled byte count')
    audit = report['audit']
    for key in ('lookup_tables_sha256', 'probability_sha256', 'transition_sha256', 'arithmetic_sha256',
                'terminal_common_state_sha256', 'parent_projection_sha256'):
        require(hash_text(audit[key]), 'missing synchronization digest: ' + key)
    require(audit['modeled_bytes'] == report['modeled_bytes'] and integer(audit['arithmetic_events'], 1, 2**32)
            and integer(audit['predictor_bits'], 1, 2**32)
            and integer(audit['terminal_common_state_bytes'], 1, 2**31), 'synchronization counts differ')
    return report


def classify_failure(error, last, plan):
    if last and (last['returncode'] == -signal.SIGXFSZ or last.get('child_failure_class') == 'budget-exhausted'):
        return 'budget-exhausted'
    if last and last['timeout']:
        error = subprocess.TimeoutExpired(last['argv'], plan['phase_wall_seconds'])
    elif last and last['error']:
        error = OSError(last['error'])
    return driver.classification(error, last['returncode'] if last else None)


def comparison_table(rows, plan):
    by_id = {r['arm']: r for r in rows}
    require(len(rows) == 3 and set(by_id) == {'P', 'K', 'D'}, 'incomplete arm comparison')
    sizes = {a: row['archive_bytes'] for a, row in by_id.items()}
    require(sizes['P'] == sizes['K'], 'P/K size differs')
    candidate_bytes = sum(r['bytes'] for r in plan['package_files'])
    parent_bytes = sum(r['bytes'] for r in plan['parent_package_files'])
    saving = sizes['P'] - sizes['D']
    return dict(schema='gamma.enwiki9.opcode-field-costs.v1', archive_bytes=sizes, archive_saving_bytes=saving,
                known_candidate_source_bytes=candidate_bytes, known_parent_source_bytes=parent_bytes,
                added_source_bytes=candidate_bytes-parent_bytes, archive_saving_less_added_source_bytes=saving-candidate_bytes+parent_bytes,
                arm_value_bytes=1, complete_options_bytes=None,
                invocation_options=dict(P=['--arm', 'P'], K=['--arm', 'K'], D=['--arm', 'D']),
                strict_archive_improvement=saving > 0, validation_eligible=saving > 0,
                confirmation_eligible=False, confirmation_requires_positive_separately_frozen_validation=True,
                package_files=plan['package_files'], parent_package_files=plan['parent_package_files'],
                complete_package_bytes=None, full_corpus_score_bytes=None, objective_credit_bytes=0,
                resource_qualified=False, package_gaps=['runtime distribution and licensing', 'accepted package and option accounting'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(argv)
    _, reference, plan, snapshot = authenticate(args.candidate, args.validate_only)
    if args.validate_only:
        print(json.dumps(dict(status='preflight_pass', executed=False, native_phases=10, effective_phase_file_bytes=33554432)))
        return 0
    directory = ROOT / 'results' / args.candidate
    require(directory.is_dir() and directory.resolve() == directory and not any(directory.iterdir()), 'nonempty output')
    population, marker = ROOT / plan['population']['path'], Path(os.environ['GAMMA_RESOURCE_PHASE_MARKERS'])
    raw = population.read_bytes()
    stage = dict(schema='gamma.enwiki9.opcode-field-stage.v1', candidate_id=args.candidate, experiment=reference,
                 status='running', arms=[], commands=[], objective_credit_bytes=0, full_corpus_score_bytes=None,
                 complete_package_bytes=None, resource_qualified=False, effective_phase_file_bytes=33554432)
    last, table = None, None
    try:
        for arm in ['legacy', 'P', 'K', 'D']:
            paths = dict(archive=directory/(arm+'.arc'), restored=directory/(arm+'.raw'), repeat=directory/(arm+'.repeat.arc'))
            phases = [('encode', population, paths['archive'])]
            if arm != 'legacy':
                phases += [('decode', paths['archive'], paths['restored']), ('repeat', paths['restored'], paths['repeat'])]
            wrappers, reports = {}, {}
            for phase, inp, out in phases:
                operation = 'decode' if phase == 'decode' else 'legacy-encode' if arm == 'legacy' else 'encode'
                audit_path = directory/(arm+'-'+phase+'.audit.json')
                command = [sys.executable, str(ROOT/plan['cli']['path']), operation, str(inp), str(out),
                           '--candidate-root', str(snapshot), '--audit', str(audit_path)]
                if arm != 'legacy':
                    command += ['--arm', arm]
                last = driver.run_phase(directory, arm+'-'+phase, command, plan, marker)
                stage['commands'].append(last)
                if last['returncode'] != 0:
                    try:
                        failure = driver.read_json(directory/(arm+'-'+phase+'.stderr'))
                        if failure.get('error_class') in ('budget-exhausted', 'implementation-failure', 'infrastructure-failure'):
                            last['child_failure_class'] = failure['error_class']
                    except (OSError, ValueError, AttributeError):
                        pass
                require(last['returncode'] == 0 and not last['timeout'] and last['error'] is None, 'phase failed: ' + last['phase'])
                wrappers[phase] = driver.read_json(directory/(arm+'-'+phase+'.stdout'))
                reports[phase] = checked_wrapper(wrappers[phase])
                require(driver.read_json(audit_path) == reports[phase]['audit'], 'retained audit and report differ')
            report = reports['encode']
            if arm == 'legacy':
                require(driver.sha(paths['archive']) == report['archive_sha256'] == plan['historical_parent']['archive_sha256']
                        and paths['archive'].stat().st_size == report['archive_bytes'] == plan['historical_parent']['archive_bytes']
                        and report['raw_bytes'] == len(raw) and report['raw_sha256'] == plan['population']['sha256'],
                        'fresh retained parent differs from historical archive')
                stage['legacy_reference'] = dict(archive=driver.artifact(paths['archive']), report=report)
                continue
            require(paths['restored'].read_bytes() == raw, 'independent raw inverse differs')
            require(paths['archive'].read_bytes() == paths['repeat'].read_bytes(), 'raw encoder repeat differs')
            require(report == reports['decode'] == reports['repeat'], 'complete decoder-common report differs')
            checked_report(report, arm, paths['archive'], raw, plan)
            if arm == 'P':
                require(paths['archive'].read_bytes() == (directory/'legacy.arc').read_bytes(), 'observed P differs from uninstrumented parent')
            if arm == 'K':
                require(paths['archive'].read_bytes() == (directory/'P.arc').read_bytes(), 'P/K archive differs')
                p_report = driver.read_json(directory/'P-encode.stdout')['result']
                keys = ('lookup_tables_sha256', 'probability_sha256', 'arithmetic_sha256', 'parent_projection_sha256',
                        'modeled_bytes', 'arithmetic_events', 'predictor_bits')
                require(all(report['audit'][k] == p_report['audit'][k] for k in keys), 'P/K authoritative probability/state projection differs')
            row = dict(arm=arm, archive_bytes=report['archive_bytes'], report=report, exact_inverse=True,
                       deterministic_repeat=True, complete_state_synchronization=True, raw_encoder_repeat_proved=True,
                       artifacts={k: driver.artifact(p) for k, p in paths.items()},
                       phase_resources={p: {k: w[k] for k in ('cpu_seconds', 'elapsed_seconds', 'peak_process_rss_kib')} for p,w in wrappers.items()})
            driver.write_json(directory/(arm+'.result.json'), row)
            stage['arms'].append(row)
        table = comparison_table(stage['arms'], plan)
        stage.update(status='passed', correctness_pass=True, p_k_identity_pass=True, fresh_parent_identity_pass=True)
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, failure_class=classify_failure(error, last, plan), error=type(error).__name__ + ': ' + str(error))
    stage['native_phases'] = len(stage['commands'])
    try:
        authenticate(args.candidate)
        stage['frozen_inputs_reverified'] = True
        if stage['correctness_pass']:
            driver.write_json(directory/'costs-table.json', table)
            stage['costs'] = table
    except Exception as error:
        stage.update(status='failed', correctness_pass=False, frozen_inputs_reverified=False, failure_class='infrastructure-failure',
                     error='Final authentication or table publication: ' + str(error))
    files = [driver.artifact(p) for p in sorted(directory.iterdir()) if p.is_file()]
    driver.write_json(directory/'artifacts.json', dict(complete=stage['correctness_pass'], files=files))
    driver.write_json(directory/'stage-decision.json', stage)
    print(json.dumps(dict(status=stage['status'], arms_closed=len(stage['arms']), native_phases=stage['native_phases'])))
    return 0 if stage['correctness_pass'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
