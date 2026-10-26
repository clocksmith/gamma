"""Bounded qualification of permitted imports against pinned independent cases.

The owner supplies a trusted recovered service configuration. This runner never
opens the mixed corpus or reserved cases. Expected values stay on the host. A
completed execution is independently rechecked before any catalogue adoption;
this module does not manufacture or automatically promote catalogue receipts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from algsolve.judge import sandbox
from .boundary_policy import authorize_before_open
from .known_spec_service import KnownSpecService, _boundary_snapshot

SOLVER = Path(__file__).resolve().parents[1]
REPO = SOLVER.parents[1]
INVENTORY = SOLVER / 'findings/library-answer-audit-v2/inventory.jsonl'
INVENTORY_SHA = 'da99c407bff14065f25282c23baef6d1daf69e7b9b76fce189b2922485bc5e77'
HARNESS = SOLVER / 'catalogue/public-domain-qualification-medium32-wave2-observer-v1'
LIMITS = dict(cpu_seconds=3, wall_seconds=8, memory_bytes=1024**3,
              max_output_bytes=4 * 1024**2)
MAX_FILE = 8 * 1024**2
MAX_PACKET = 1_100_000


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_hash(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON field')
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def read(path, maximum=MAX_FILE):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise ValueError('regular nonsymlink file required')
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError('file exceeds bounded reader')
    return raw


def write(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_bytes(encoded(value))
    os.replace(temporary, path)


def runtime():
    paths = {'/usr/bin/python3', '/usr/bin/node', '/usr/bin/bwrap', '/usr/bin/prlimit'}
    for name in sorted(paths.copy()):
        result = subprocess.run(['ldd', name], capture_output=True, text=True, check=True, timeout=10)
        paths.update(re.findall(r'(/[^\s()]+)', result.stdout))
    return {name: {'resolved': str(Path(name).resolve(strict=True)), 'sha256': file_hash(name)}
            for name in sorted(paths)}


def code_pins():
    paths = [Path(__file__), Path(sandbox.__file__), HARNESS / 'harness.py', HARNESS / 'harness.cjs',
             Path(__file__).with_name('imported_result_contracts.py')]
    return {str(p): file_hash(p) for p in paths}


def canonical_tests_hash(cases):
    # Historical library_audit.digest has no trailing newline.
    return sha(json.dumps(cases, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def exact(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def expected_type(value, language):
    names = {type(None): ('NoneType', 'object'), bool: ('bool', 'boolean'),
             int: ('int', 'number'), float: ('float', 'number'), str: ('str', 'string'),
             list: ('list', 'object'), dict: ('dict', 'object')}
    return names[type(value)][language == 'javascript']


def compare(case, record, language, policy='exact'):
    if policy.startswith('problem:'):
        from .imported_result_contracts import compare as statement_compare
        return statement_compare(int(policy.split(':')[1]), case, record, language)
    if 'error' in record:
        return 'candidate_error'
    if record.get('result_type') != expected_type(case['expected'], language):
        return 'result_type'
    got, wanted = record.get('result'), case['expected']
    if policy == 'set-of-strings':
        if type(got) is not list or any(type(x) is not str for x in got) or len(set(got)) != len(got):
            return 'result_value'
        got, wanted = sorted(got), sorted(wanted)
    elif policy == 'permutation-of-chars':
        if type(got) is not str:
            return 'result_value'
        got, wanted = sorted(got), sorted(wanted)
    elif policy != 'exact':
        raise ValueError('unregistered comparison policy')
    if not exact(got, wanted):
        return 'result_value'
    if not exact(record.get('args_before'), case['args']) or not exact(record.get('args_after'), case['args']):
        return 'input_effects'
    if not exact(record.get('alias_edges'), []):
        return 'return_aliases'
    return None


def packet(cases):
    from .imported_result_contracts import canonical
    return {'entry': 'solve', 'method': 'solve', 'calls': [{'args': canonical(c['args'])} for c in cases]}


def batches(cases):
    group = []
    offset = 0
    for case in cases:
        if len(encoded(packet([case]))) > MAX_PACKET:
            raise ValueError('case exceeds packet cap; no silent truncation')
        if group and (len(group) == 32 or len(encoded(packet(group + [case]))) > MAX_PACKET):
            yield offset, group
            offset += len(group)
            group = []
        group.append(case)
    if group:
        yield offset, group


def check_output(raw, cases, language, policy='exact'):
    records = [decode(line) for line in raw.splitlines()]
    if len(records) != len(cases) + 1 or records[-1] != {'done': len(cases)}:
        raise ValueError('incomplete output protocol')
    failures = []
    for i, (case, record) in enumerate(zip(cases, records[:-1])):
        if type(record) is not dict or type(record.get('i')) is not int or record['i'] != i:
            raise ValueError('out-of-order or duplicate observation')
        reason = compare(case, record, language, policy)
        if reason:
            failures.append({'index': i, 'reason': reason})
    return failures


def prepare(args):
    service = KnownSpecService.from_config(args.config, args.config_sha256)
    config = decode(read(args.config))
    gate = decode(read(config['source_access']['boundary_gate']['path']))
    boundary = _boundary_snapshot(gate)
    inventory_raw = read(INVENTORY)
    if sha(inventory_raw) != INVENTORY_SHA:
        raise ValueError('independent inventory anchor mismatch')
    inventory = {}
    for line in inventory_raw.splitlines():
        row = decode(line)
        ids = {int(u.split(':')[1]) for u in row.get('members', []) if re.fullmatch(r'(lcd|doocs):[0-9]+', u)}
        if len(ids) == 1:
            pid = next(iter(ids))
            if pid in inventory:
                raise ValueError('ambiguous numeric inventory identity')
            inventory[pid] = row
    snapshots = {r['problem_id']: r for r in decode(read(args.statements)) if r['status'] == 'fetched'}
    listed = subprocess.check_output(['git', 'ls-files', 'projects/algorithm_solver/catalogue/authored'], cwd=REPO, text=True).splitlines()
    selected = {}
    for name in listed:
        path = Path(name)
        if len(path.parts) != 7 or path.parts[-2] not in ('javascript', 'python') or not path.stem.isdecimal():
            continue
        pid, language = int(path.stem), path.parts[-2]
        # Metadata-only selection excludes reserved and unknown BEFORE opens.
        if f'leetcode:{pid}' not in boundary.authorized:
            continue
        existing = service.request(f'leetcode:{pid}', language=language)
        if existing.get('consumer_selection', {}).get('status') == 'selected':
            continue
        key = (pid, language)
        if key in selected:
            raise ValueError('multiple pending variants require explicit selection')
        selected[key] = REPO / path
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / 'sources').mkdir()
    (args.output / 'tests').mkdir()
    jobs, pending = [], []
    for (pid, language), source_path in sorted(selected.items()):
        identity = f'leetcode:{pid}'
        descriptors = inventory.get(pid, {}).get('independent_test_sets', [])
        if len(descriptors) != 1 or identity not in snapshots:
            pending.append({'id': pid, 'language': language, 'reason': 'missing_independent_tests_or_statement'})
            continue
        desc = descriptors[0]
        if desc['uid'] != f'lcd:{pid}' or desc['path'] != f'tests/lcd__{pid}.json':
            raise ValueError('test locator not bound to selected numeric identity')
        authorize_before_open(identity, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        tests_raw = read(SOLVER / 'data/derived' / desc['path'])
        cases = decode(tests_raw)
        if canonical_tests_hash(cases) != desc['sha256'] or len(cases) != desc['tests'] or not cases:
            raise ValueError('independent tests differ from historical inventory')
        if any(set(c) != {'args', 'expected', 'compare'} or c['compare'] != 'return' or type(c['args']) is not list for c in cases):
            raise ValueError('unsupported case contract')
        statement = snapshots[identity]
        if sha(read(statement['path'])) != statement['sha256']:
            raise ValueError('pinned statement changed')
        authorize_before_open(identity, gate['artifact_paths'], gate['trusted_hashes'], language=language)
        source = read(source_path, 1024 * 1024)
        suffix = 'py' if language == 'python' else 'js'
        relative = f'sources/{pid}.{suffix}'
        (args.output / relative).write_bytes(source)
        (args.output / f'tests/{pid}.json').write_bytes(tests_raw)
        jobs.append({'id': pid, 'language': language, 'source': relative, 'source_sha256': sha(source),
                     'original_source': str(source_path), 'tests': f'tests/{pid}.json', 'tests_raw_sha256': sha(tests_raw),
                     'tests_canonical_sha256': desc['sha256'], 'case_count': len(cases), 'statement': statement})
    contract = {'schema': 'gamma.imported-independent-execution.v1', 'jobs': jobs, 'pending': pending,
                'service_config': str(args.config.resolve()), 'service_config_sha256': args.config_sha256,
                'runtime': runtime(), 'code': code_pins(), 'limits': LIMITS, 'max_packet_bytes': MAX_PACKET,
                'test_authority': 'Owner request to qualify permitted implementations; pre-existing independently authored LCD cases, each bound to the historical source-free inventory.',
                'inventory_sha256': INVENTORY_SHA, 'effects': 'read-only arguments; no mutable return-to-input aliases',
                'comparison': 'exact typed ordered returns; failures retained, no comparator relaxation in this freeze',
                'scope': 'Independent finite tests plus explicit local effects. Execution alone does not establish full normative-domain applicability or catalogue qualification.',
                'automatic_promotion': False, 'protected_access': False}
    write(args.output / 'contract.json', contract)
    return {'jobs': len(jobs), 'pending': len(pending), 'contract_sha256': file_hash(args.output / 'contract.json')}


def load_freeze(path):
    raw = read(path / 'contract.json')
    contract = decode(raw)
    if contract['schema'] != 'gamma.imported-independent-execution.v1' or contract['code'] != code_pins() or contract['limits'] != LIMITS:
        raise ValueError('execution freeze drift')
    for name, expected in contract.get('additional_code', {}).items():
        if file_hash(name) != expected:
            raise ValueError('oracle or validator changed since freeze')
    KnownSpecService.from_config(Path(contract['service_config']), contract['service_config_sha256'])
    config = decode(read(contract['service_config']))
    gate = decode(read(config['source_access']['boundary_gate']['path']))
    if len({(j['id'], j['language']) for j in contract['jobs']}) != len(contract['jobs']):
        raise ValueError('duplicate frozen job')
    return raw, contract, gate


def job_inputs(root, job, gate):
    pid, lang = job['id'], job['language']
    if type(pid) is not int or lang not in ('python', 'javascript'):
        raise ValueError('invalid frozen job identity')
    suffix = 'py' if lang == 'python' else 'js'
    if job['source'] != f'sources/{pid}.{suffix}' or job['tests'] != f'tests/{pid}.json':
        raise ValueError('invalid frozen exact locator')
    authorize_before_open(f'leetcode:{pid}', gate['artifact_paths'], gate['trusted_hashes'], language=lang)
    source = read(root / job['source'], 1024 * 1024)
    raw = read(root / job['tests'])
    cases = decode(raw)
    if sha(source) != job['source_sha256'] or sha(raw) != job['tests_raw_sha256'] or len(cases) != job['case_count']:
        raise ValueError('frozen source/cases changed')
    if job.get('domain_validator') == 'fresh67-v1':
        from .qualification_fresh_cases import validate
        for case in cases:
            validate(pid, case['args'])
    elif job.get('domain_validator') == 'imported358-v1':
        from . import imported_case_admission, imported_clean_domains
        validator = imported_case_admission.validate if pid in imported_case_admission.DOMAIN_IDS else imported_clean_domains.validate
        for case in cases:
            validator(pid, case['args'])
    elif 'domain_validator' in job:
        raise ValueError('unknown input validator')
    return source, cases


def execute(args):
    frozen, contract, gate = load_freeze(args.freeze)
    if contract['runtime'] != runtime():
        raise ValueError('runtime drift')
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'gamma.imported-independent-report.v1', 'freeze': str(args.freeze.resolve()),
              'freeze_sha256': sha(frozen), 'status': 'running', 'rows': [], 'new_qualifications': 0}
    start = time.monotonic()
    try:
        for job in contract['jobs']:
            source, cases = job_inputs(args.freeze, job, gate)
            row = {'id': job['id'], 'language': job['language'], 'source_sha256': sha(source), 'calls': [],
                   'cases': len(cases), 'failures': [], 'passed': False}
            for offset, batch in batches(cases):
                if time.monotonic() - start > args.max_wall:
                    raise TimeoutError('campaign wall budget')
                if job['language'] == 'python':
                    argv = ['/usr/bin/python3', '-I', '-S', 'harness.py']; program = 'program.py'; harness = 'harness.py'
                else:
                    argv = ['/usr/bin/node', '--jitless', '--single-threaded', '--max-old-space-size=64', 'harness.cjs']; program = 'program.js'; harness = 'harness.cjs'
                result = sandbox.run(argv, files={program: source, harness: read(HARNESS / harness), 'inputs.json': encoded(packet(batch))}, limits=sandbox.Limits(**LIMITS))
                stem = f"{job['id']}-{job['language']}-{offset}"
                (args.output / (stem + '.stdout')).write_bytes(result.stdout)
                (args.output / (stem + '.stderr')).write_bytes(result.stderr)
                call = {'stem': stem, 'offset': offset, 'count': len(batch), 'exit_code': result.exit_code,
                        'timed_out': result.timed_out, 'output_limit_exceeded': result.output_limit_exceeded,
                        'stdout_sha256': sha(result.stdout), 'stderr_sha256': sha(result.stderr), 'wall_seconds': result.wall_seconds}
                row['calls'].append(call)
                if not result.ok:
                    row['failures'].append({'offset': offset, 'reason': 'isolated_execution_failed'})
                else:
                    try:
                        row['failures'].extend({'offset': offset, **f} for f in check_output(result.stdout, batch, job['language'], job.get('comparison_policy', 'exact')))
                    except (ValueError, TypeError, KeyError) as error:
                        row['failures'].append({'offset': offset, 'reason': 'invalid_output', 'error': str(error)})
            row['passed'] = not row['failures']
            report['rows'].append(row)
            report['elapsed_seconds'] = time.monotonic() - start
            write(args.output / 'report.json', report)
            print(json.dumps({'id': row['id'], 'language': row['language'], 'passed': row['passed'], 'cases': len(cases), 'completed': len(report['rows'])}), flush=True)
        if contract['runtime'] != runtime():
            raise ValueError('runtime changed during campaign')
        report['status'] = 'completed'
    except Exception as error:
        report.update(status='failed', error=type(error).__name__ + ': ' + str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic() - start
        write(args.output / 'report.json', report)
    return {'status': report['status'], 'passed': sum(r['passed'] for r in report['rows']), 'total': len(report['rows'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare_parser = sub.add_parser('prepare')
    for name in ('config', 'statements', 'output'):
        prepare_parser.add_argument('--' + name, required=True, type=Path)
    prepare_parser.add_argument('--config-sha256', required=True)
    run_parser = sub.add_parser('run')
    for name in ('freeze', 'output'):
        run_parser.add_argument('--' + name, required=True, type=Path)
    run_parser.add_argument('--max-wall', type=int, default=1800)
    args = parser.parse_args()
    print(json.dumps(prepare(args) if args.command == 'prepare' else execute(args)))


if __name__ == '__main__':
    main()
