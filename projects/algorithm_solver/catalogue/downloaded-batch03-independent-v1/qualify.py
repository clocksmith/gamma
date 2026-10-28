"""Freeze and execute the downloaded batch 03 (88 pairs) in an authorized isolated judge."""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'projects/algorithm_solver'))
sys.path.insert(0, str(HERE))

import cases
import oracles as o
from algsolve.judge import sandbox

IMPORT = Path('projects/algorithm_solver/catalogue/authored/downloaded-general88-v1')
TRANSPORT = Path('projects/algorithm_solver/catalogue/public-domain-qualification-easy16-v1')
LIMITS = sandbox.Limits(cpu_seconds=3, wall_seconds=8, memory_bytes=1024**3,
                        max_output_bytes=16 * 1024**2)
ARGV = {
    'python': ['/usr/bin/python3', '-I', '-S', 'harness.py'],
    'javascript': ['/usr/bin/node', '--jitless', '--single-threaded',
                   '--max-old-space-size=256', 'harness.cjs']
}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    target = Path(path)
    if target.exists():
        target.unlink()
    with target.open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def runtime():
    refs = {}
    is_linux = platform.system() == 'Linux'
    if is_linux:
        for name in ('python3', 'node', 'bwrap', 'prlimit'):
            path = Path('/usr/bin') / name
            if path.exists():
                refs[str(path)] = sha(path.read_bytes())
                proc = subprocess.run(['/usr/bin/ldd', str(path)], capture_output=True, text=True, check=True)
                for dep in re.findall(r'(?:=>\s*)?(/[^\s()]+)', proc.stdout):
                    dep_path = Path(dep)
                    if dep_path.exists():
                        refs[dep] = sha(dep_path.read_bytes())
    py_bin = sys.executable
    node_bin = shutil.which('node') or '/usr/bin/node'
    node_version = subprocess.check_output([node_bin, '--version'], text=True).strip() if shutil.which('node') else 'unavailable'
    lib = Path(subprocess.check_output([py_bin, '-c',
                'import sysconfig;print(sysconfig.get_path("stdlib"))'], text=True).strip())
    standard = {}
    if lib.exists():
        standard = {str(p.relative_to(lib)): sha(p.read_bytes()) for p in sorted(lib.rglob('*'))
                    if p.is_file() and p.suffix in ('.py', '.so') and
                    'site-packages' not in p.parts and '__pycache__' not in p.parts}
    return {
        'executables_and_linked_libraries': refs,
        'python_stdlib_path': str(lib),
        'python_stdlib_files': standard,
        'python_version': sys.version.split()[0],
        'node_version': node_version,
        'platform_system': platform.system(),
        'platform_release': platform.release(),
        'isolated_judge_available': Path('/usr/bin/bwrap').exists()
    }


def artifacts():
    paths = list(HERE.glob('*.py')) + [HERE / 'README.md', HERE / 'statement-pins.json']
    paths += [ROOT / TRANSPORT / name for name in ('harness.py', 'harness.cjs')]
    paths += [ROOT / 'projects/algorithm_solver/algsolve/judge/sandbox.py',
              ROOT / IMPORT / 'manifest.json', ROOT / IMPORT / 'assignment.public-safe.json']
    manifest = json.loads((ROOT / IMPORT / 'manifest.json').read_bytes())
    assert len(manifest['source_inventory']) == 176
    for row in manifest['source_inventory']:
        p = ROOT / IMPORT / row['path']
        if sha(p.read_bytes()) != row['sha256']:
            raise ValueError(f'source identity mismatch: {row["path"]}')
        paths.append(p)
    return {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in sorted(set(paths)) if p.exists()}


def batches(values):
    batch = []
    size = 0
    for index, case in enumerate(values):
        length = len(encoded(case['args']))
        if batch and (len(batch) >= 32 or size + length > 256 * 1024):
            yield batch + [batch[0]]
            batch, size = [], 0
        batch.append(index)
        size += length
    if batch:
        yield batch + [batch[0]]


def load_cases(statements, pins):
    pins = [p for p in pins if p['id'] in o.IDS]
    assert len(pins) == len(o.IDS) and {p['id'] for p in pins} == set(o.IDS)
    for pin in pins:
        raw = (Path(statements) / (str(pin['id']) + '.json')).read_bytes()
        q = json.loads(raw)['data']['question']
        raw_sha = sha(raw)
        content_sha = sha((q['content'] or '').encode())
        if raw_sha != pin['snapshot_sha256'] or content_sha != pin['content_sha256'] or q['titleSlug'] != pin['slug']:
            raise ValueError(f'official definition snapshot drift for problem {pin["id"]}')
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
    pins_path = args.pins or (HERE / 'statement-pins.json')
    pins = json.loads(pins_path.read_bytes())
    pins = [p for p in pins if p['id'] in o.IDS]
    assert len(pins) == len(o.IDS)
    data = load_cases(args.statements, pins)
    preflight_sha = None
    if args.preflight and args.preflight.exists():
        preflight_sha = sha(args.preflight.read_bytes())
    contract = {
        'schema': 'gamma.downloaded-batch03-independent-v1.frozen-contract.v1',
        'created_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'Exact owner-provided solve functions; 88 problems (176 programs); exposed public-domain evidence only',
        'historical_protected_payloads_used': False,
        'canonical_promotion': False,
        'qualification_scope': 'Functional solve adapter qualification; official LeetCode in-place wrappers distinguished and not execution-qualified',
        'artifact_hashes': artifacts(),
        'runtime': runtime(),
        'argv': ARGV,
        'limits': asdict(LIMITS),
        'statement_pins': pins,
        'cases_sha256': sha(encoded(data)),
        'case_counts': {str(k): len(v) for k, v in data.items()},
        'batch_plan': {str(k): list(batches(v)) for k, v in data.items()},
        'host': {'hostname': platform.node(), 'platform': platform.platform()},
        'judge_preflight_sha256': preflight_sha,
        'mandatory_failures': {f'{k[0]}_{k[1]}': v for k, v in o.MANDATORY_FAILURES.items()},
        'functional_adapter_ids': list(o.FUNCTIONAL_ADAPTER_IDS)
    }
    write(args.freeze, contract)
    print('FROZEN', sha(args.freeze.read_bytes()), flush=True)


def execute(args):
    raw = args.freeze.read_bytes()
    freeze_hash = sha(raw)
    if args.freeze_sha256 and freeze_hash != args.freeze_sha256:
        raise ValueError('freeze identity differs from approved command')
    contract = json.loads(raw)
    current_artifacts = artifacts()
    for path, exp_sha in contract['artifact_hashes'].items():
        if current_artifacts.get(path) != exp_sha:
            raise ValueError(f'source/helper drift since freeze: {path}')
    data = load_cases(args.statements, contract['statement_pins'])
    if sha(encoded(data)) != contract['cases_sha256']:
        raise ValueError('generated test drift')

    args.output.mkdir(parents=True, exist_ok=True)
    identity = {
        'freeze_sha256': freeze_hash,
        'host': platform.node(),
        'platform': platform.platform(),
        'started_at': datetime.now(timezone.utc).isoformat(),
        'artifact_hashes': current_artifacts
    }
    write(args.output / 'run-identity.json', identity)

    # Check authorized isolated judge availability
    try:
        sandbox.check_available()
        judge_available = True
    except sandbox.SandboxUnavailable:
        judge_available = False

    if not judge_available:
        # Per contract: "If execution is unavailable, deliver the prepared cases and contracts as unexecuted."
        unexecuted_receipt = {
            'schema': 'gamma.downloaded-batch03-unexecuted-receipt.v1',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'freeze_sha256': freeze_hash,
            'host': platform.node(),
            'platform': platform.platform(),
            'execution_status': 'unexecuted',
            'reason': 'isolated_judge_unavailable',
            'judge_binary_required': sandbox.BWRAP,
            'explanation': 'Linux bubblewrap isolation judge (/usr/bin/bwrap) is unavailable on host platform. Expected outputs remained outside candidate packets. Prepared cases, batch plans, and frozen contracts are delivered as unexecuted.',
            'total_problems': len(o.IDS),
            'total_pairs': len(o.IDS),
            'total_cases_prepared': sum(len(v) for v in data.values()),
            'canonical_admission_changed': False
        }
        write(args.output / 'unexecuted-receipt.json', unexecuted_receipt)
        report = {
            'freeze_sha256': freeze_hash,
            'execution_status': 'unexecuted',
            'judge_available': False,
            'reason': 'isolated_judge_unavailable',
            'total_problems': len(o.IDS),
            'total_pairs': len(o.IDS),
            'total_cases_prepared': sum(len(v) for v in data.values()),
            'passed': False,
            'canonical_admission_changed': False,
            'qualification_scope': 'Functional solve adapter only; official wrappers not execution-qualified'
        }
        write(args.output / 'report.json', report)
        print('UNEXECUTED: Isolated Linux bubblewrap judge unavailable on this host. Prepared cases and contracts delivered as unexecuted.', flush=True)
        return

    # If isolated judge is available, run batches
    summaries = []
    for pid in o.IDS:
        values = data[pid]
        assert list(batches(values)) == contract['batch_plan'][str(pid)]
        for language, ext, harness in [('python', 'py', 'harness.py'),
                                       ('javascript', 'js', 'harness.cjs')]:
            total, failures = 0, []
            for b, indices in enumerate(contract['batch_plan'][str(pid)]):
                packet = {'entry': 'solve', 'calls': [{'args': values[i]['args']} for i in indices]}
                stem = f'{pid}-{language}-{b:03d}'
                write(args.output / (stem + '.start.json'), {
                    'problem_id': pid, 'language': language,
                    'indices': indices, 'inputs_sha256': sha(encoded(packet))
                })
                result = sandbox.run(ARGV[language], files={
                    'program.' + ext: (ROOT / IMPORT / language / f'{pid}.{ext}').read_bytes(),
                    harness: (ROOT / TRANSPORT / harness).read_bytes(),
                    'inputs.json': encoded(packet)
                }, limits=LIMITS)
                metadata = asdict(result)
                for stream in ('stdout', 'stderr'):
                    payload = metadata.pop(stream)
                    (args.output / (stem + '.' + stream)).write_bytes(payload)
                    metadata[stream + '_sha256'] = sha(payload)
                write(args.output / (stem + '.result.json'), metadata)
                failures.extend(verdict(pid, language, values, indices, metadata, result.stdout))
                total += len(indices)
            row = {
                'problem_id': pid, 'language': language, 'distinct_cases': len(values),
                'generated_cases': len(values), 'executed_calls': total,
                'failures': failures, 'passed': not failures,
                'mandatory_constraint_failure': o.MANDATORY_FAILURES.get((pid, language)),
                'qualified': not failures and (pid, language) not in o.MANDATORY_FAILURES,
                'official_wrapper_execution_qualified': False
            }
            summaries.append(row)
            write(args.output / f'{pid}-{language}.summary.json', row)
            print(json.dumps({k: v for k, v in row.items() if k != 'failures'}), flush=True)
    write(args.output / 'report.json', {
        'freeze_sha256': freeze_hash, 'programs': summaries,
        'passed': all(r['passed'] for r in summaries), 'canonical_admission_changed': False,
        'qualification_scope': 'Functional solve adapter only; official wrappers not execution-qualified'
    })


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
    if args.operation == 'freeze':
        freeze(args)
    else:
        execute(args)


if __name__ == '__main__':
    main()
