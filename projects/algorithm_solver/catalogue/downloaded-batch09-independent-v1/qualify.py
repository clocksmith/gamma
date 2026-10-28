"""Freeze and execute the next exact downloaded cohort in the existing Linux judge."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys

import cases
import oracles as o
o.IDS=cases.IDS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'projects/algorithm_solver'))
from algsolve.judge import sandbox

IMPORT = Path('projects/algorithm_solver/catalogue/authored/downloaded-general40-v1')
TRANSPORT = Path('projects/algorithm_solver/catalogue/public-domain-qualification-easy16-v1')
LIMITS = sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024**3,
                        max_output_bytes=16 * 1024**2)
ARGV = {'python': ['/usr/bin/python3', '-I', '-S', 'harness.py'],
        'javascript': ['/usr/bin/node', '--jitless', '--single-threaded',
                       '--max-old-space-size=256', 'harness.cjs']}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def runtime():
    refs = {}
    for name in ('python3', 'node', 'bwrap', 'prlimit'):
        path = Path('/usr/bin') / name
        refs[str(path)] = sha(path.read_bytes())
        proc = subprocess.run(['/usr/bin/ldd', str(path)], capture_output=True, text=True, check=True)
        for dep in re.findall(r'(?:=>\s*)?(/[^\s()]+)', proc.stdout):
            refs[dep] = sha(Path(dep).read_bytes())
    lib = Path(subprocess.check_output(['/usr/bin/python3', '-I', '-S', '-c',
                'import sysconfig;print(sysconfig.get_path("stdlib"))'], text=True).strip())
    standard = {str(p.relative_to(lib)): sha(p.read_bytes()) for p in sorted(lib.rglob('*'))
                if p.is_file() and p.suffix in ('.py', '.so') and
                'site-packages' not in p.parts and '__pycache__' not in p.parts}
    return {'executables_and_linked_libraries': refs, 'python_stdlib_path': str(lib),
            'python_stdlib_files': standard,
            'python_version': subprocess.check_output(['/usr/bin/python3', '--version'], text=True).strip(),
            'node_version': subprocess.check_output(['/usr/bin/node', '--version'], text=True).strip()}


def artifacts():
    paths = list(HERE.glob('*.py')) + [HERE / 'README.md']
    paths += [ROOT / TRANSPORT / name for name in ('harness.py', 'harness.cjs')]
    paths += [ROOT / 'projects/algorithm_solver/algsolve/judge/sandbox.py',
              ROOT / IMPORT / 'manifest.json', ROOT / IMPORT / 'assignment.public-safe.json']
    manifest = json.loads((ROOT / IMPORT / 'manifest.json').read_bytes())
    assert len(manifest['source_inventory']) == 80
    for row in manifest['source_inventory']:
        p = ROOT / IMPORT / row['path']
        if sha(p.read_bytes()) != row['sha256']:
            raise ValueError('source identity mismatch')
        paths.append(p)
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(paths)}


def batches(values):
    batch = []
    size = 0
    for index, case in enumerate(values):
        if case['category'].startswith('maximum'):
            if batch:
                yield batch + [batch[0]]
                batch, size = [], 0
            yield [index]
            continue
        length = len(encoded(case['args']))
        if batch and (len(batch) >= 32 or size + length > 256 * 1024):
            yield batch + [batch[0]]
            batch, size = [], 0
        batch.append(index)
        size += length
    if batch:
        yield batch + [batch[0]]


def load_cases(statements, pins):
    pins=[p for p in pins if p['id'] in o.IDS]
    assert len(pins) == len(o.IDS) and {p['id'] for p in pins} == set(o.IDS)
    for pin in pins:
        raw = (Path(statements) / (str(pin['id']) + '.json')).read_bytes()
        q = json.loads(raw)['data']['question']
        if (sha(raw) != pin['snapshot_sha256'] or
                sha((q['content'] or '').encode()) != pin['content_sha256'] or
                q['titleSlug'] != pin['slug']):
            raise ValueError('official definition snapshot drift')
    return cases.build(statements)


def parse(raw, count):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate observation key')
            result[key] = value
        return result
    rows = [json.loads(line, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            for line in raw.decode('utf8').splitlines()]
    if len(rows) != count + 1 or rows[-1] != {'done': count}:
        raise ValueError('incomplete observation stream')
    for i, row in enumerate(rows[:-1]):
        if not isinstance(row, dict) or type(row.get('i')) is not int or row['i'] != i:
            raise ValueError('observation order mismatch')
        required = {'i', 'error'} if 'error' in row else {
            'i', 'result', 'result_type', 'args_before', 'args_after', 'alias_edges'}
        if set(row) != required:
            raise ValueError('observation shape mismatch')
    return rows[:-1]


def verdict(pid, language, values, indices, metadata, stdout):
    if not (metadata['exit_code'] == 0 and not metadata['timed_out']
            and not metadata['output_limit_exceeded']):
        return [{'case': i, 'reason': 'sandbox_process_failure'} for i in indices]
    try:
        rows = parse(stdout, len(indices))
    except (ValueError, UnicodeError, TypeError):
        return [{'case': i, 'reason': 'observation_protocol'} for i in indices]
    failures = []
    for index, row in zip(indices, rows):
        case = values[index]
        ok, reason = o.compare(pid, case['args'], case['expected'], row, language)
        if not ok:
            failures.append({'case': index, 'reason': reason})
    return failures


def freeze(args):
    pins = json.loads(args.pins.read_bytes())
    data = load_cases(args.statements, pins)
    contract = {'schema': 'gamma.downloaded-remaining-exposed-qualification.v1',
                'created_at': datetime.now(timezone.utc).isoformat(),
                'scope': 'Exact owner-provided solve functions; bounded independent public-domain tests; separate mandatory constraints',
                'historical_protected_payloads_used': False, 'canonical_promotion': False,
                'artifact_hashes': artifacts(), 'runtime': runtime(), 'argv': ARGV,
                'limits': asdict(LIMITS), 'statement_pins': pins,
                'cases_sha256': sha(encoded(data)),
                'case_counts': {str(k): len(v) for k, v in data.items()},
                'batch_plan': {str(k): list(batches(v)) for k, v in data.items()},
                'host': {'hostname': platform.node(), 'platform': platform.platform()},
                'judge_preflight_sha256': sha(args.preflight.read_bytes())}
    if '37 passed' not in args.preflight.read_text():
        raise ValueError('the specified Linux judge preflight did not pass')
    write(args.freeze, contract)
    print('FROZEN', sha(args.freeze.read_bytes()), flush=True)


def execute(args):
    raw = args.freeze.read_bytes()
    if sha(raw) != args.freeze_sha256:
        raise ValueError('freeze identity differs from approved command')
    contract = json.loads(raw)
    if artifacts() != contract['artifact_hashes'] or runtime() != contract['runtime']:
        raise ValueError('source/helper/runtime drift since freeze')
    if contract['argv'] != ARGV or contract['limits'] != asdict(LIMITS):
        raise ValueError('execution settings drift')
    data = load_cases(args.statements, contract['statement_pins'])
    if sha(encoded(data)) != contract['cases_sha256']:
        raise ValueError('generated test drift')
    args.output.mkdir(parents=True, exist_ok=False)
    write(args.output / 'run-identity.json', {'freeze_sha256': sha(raw), 'host': platform.node(),
          'started_at': datetime.now(timezone.utc).isoformat(), 'artifact_hashes': artifacts()})
    summaries = []
    for pid in o.IDS:
        values = data[pid]
        assert list(batches(values)) == contract['batch_plan'][str(pid)]
        for language, ext, harness in [('python', 'py', 'harness.py'),
                                        ('javascript', 'js', 'harness.cjs')]:
            total, failures = 0, []
            for b, indices in enumerate(contract['batch_plan'][str(pid)]):
                # Host expectations and statement snapshots are never supplied.
                packet = {'entry': 'solve', 'calls': [{'args': values[i]['args']} for i in indices]}
                stem = f'{pid}-{language}-{b:03d}'
                write(args.output / (stem + '.start.json'), {'problem_id': pid,
                      'language': language, 'indices': indices, 'inputs_sha256': sha(encoded(packet))})
                result = sandbox.run(ARGV[language], files={
                    'program.' + ext: (ROOT / IMPORT / language / f'{pid}.{ext}').read_bytes(),
                    harness: (ROOT / TRANSPORT / harness).read_bytes(), 'inputs.json': encoded(packet)},
                    limits=LIMITS)
                metadata = asdict(result)
                for stream in ('stdout', 'stderr'):
                    payload = metadata.pop(stream)
                    (args.output / (stem + '.' + stream)).write_bytes(payload)
                    metadata[stream + '_sha256'] = sha(payload)
                write(args.output / (stem + '.result.json'), metadata)
                failures.extend(verdict(pid, language, values, indices, metadata, result.stdout))
                total += len(indices)
            row = {'problem_id': pid, 'language': language, 'distinct_cases': len(values),
                   'generated_cases': len(values), 'executed_calls': total,
                   'failures': failures, 'passed': not failures,
                   'mandatory_constraint_failure': o.MANDATORY_FAILURES.get((pid,language)),
                   'qualified': not failures and pid not in o.DEFINITION_BLOCKED and (pid,language) not in o.MANDATORY_FAILURES,
                   'official_wrapper_execution_qualified': False,
                   'definition_gate_failure': 'Official public definition unavailable; provisional semantics cannot qualify' if pid in o.DEFINITION_BLOCKED else None,
                   'scoped_test_qualified': not failures and pid not in o.DEFINITION_BLOCKED and (pid,language) not in o.MANDATORY_FAILURES}
            summaries.append(row)
            write(args.output / f'{pid}-{language}.summary.json', row)
            print(json.dumps({k: v for k, v in row.items() if k != 'failures'}), flush=True)
    write(args.output / 'report.json', {'freeze_sha256': sha(raw), 'programs': summaries,
          'passed': all(r['passed'] for r in summaries), 'canonical_admission_changed': False,
          'qualification_scope': 'Functional solve adapter only; official wrappers not execution-qualified'})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('freeze', 'run'))
    parser.add_argument('--statements', required=True, type=Path)
    parser.add_argument('--freeze', required=True, type=Path)
    parser.add_argument('--pins', type=Path)
    parser.add_argument('--preflight', type=Path)
    parser.add_argument('--freeze-sha256')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    (freeze if args.operation == 'freeze' else execute)(args)


if __name__ == '__main__':
    main()
